"""Offline native metadata and light token-mask probes on the pinned public GPT-2 vocabulary."""
import os
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
import json,gzip,time,resource,signal,importlib.metadata as metadata
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(59);started=time.process_time()
P=Path(__file__).resolve().parent
from vocabulary import load,digest
pieces,eos,fallback,source=load();path=P.parents[2]/source['path'];j=json.loads(path.read_text())
versions={k:metadata.version(k) for k in ['llguidance','xgrammar','outlines-core','tokenizers','torch']}
assert versions=={'llguidance':'1.9.1','xgrammar':'0.2.8','outlines-core':'0.2.14','tokenizers':'0.23.3','torch':'2.15.0'}
from tokenizers import Tokenizer
hf=Tokenizer.from_file(str(path));assert hf.get_vocab_size()==50257
from llguidance import LLTokenizer,LLMatcher
ll=LLTokenizer(str(path),eos_token=eos,slices=[])
ll_differences=[i for i,b in pieces.items() if ll.decode_bytes([i])!=b]
assert ll_differences==[fallback[255]] and ll.decode_bytes([fallback[255]])==b'' and ll.is_special_token(fallback[255])
assert all(not ll.is_special_token(i) for b,i in fallback.items() if b!=255)
import torch,xgrammar as xgr
torch.set_num_threads(1);torch.set_num_interop_threads(1)
encoded=[None]*50257
for token,i in j['model']['vocab'].items():encoded[i]=token
ti=xgr.TokenizerInfo(encoded,vocab_type=xgr.VocabType.BYTE_LEVEL,stop_token_ids=[eos],add_prefix_space=False)
decoded=ti.decoded_vocab;assert all(decoded[i]==b for i,b in pieces.items())
compiler=xgr.GrammarCompiler(ti,max_threads=1,cache_enabled=False)
from outlines_core import Vocabulary,Index
from outlines_core.json_schema import build_regex_from_schema
vocab=Vocabulary(eos,{b:[i] for i,b in pieces.items()})
latin=''.join(chr(i) for i in range(256));latin_ids=[fallback[b] for b in latin.encode()]
assert hf.decode(latin_ids,skip_special_tokens=False)==latin
corpus=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()));cases={r['id']:r for r in corpus}
ff_live_edges=0
for r in corpus:
    c=r['byte_certificate']
    ff_live_edges+=sum(c['states'][n['edges'].get('255',c['sink'])]['distance'] is not None for n in c['states'])
assert ff_live_edges==0
probes=[('issue-xg858-original',[b'',b'{',b'{"modifier":',b'{"modifier":""}',b'{}']),('issue-xg895-original',[b'',b'{"k":"abc',b'{"k":"abcd',b'{"k":"abcd"}',b'{"k":"ABC"}']),('unicode-piece-control',[b'',b'"',b'"\xf0\x9f',b'"\xf0\x9f\x98\x80"'])]
rows=[]
for name,prefixes in probes:
    begin=time.process_time();s=cases[name]['schema'] if name in cases else {'const':'😀'}
    schema=json.dumps(s,sort_keys=True);compiled={};errors={}
    try:
        grammar=LLMatcher.grammar_from_json_schema(json.loads(schema),overrides={'lenient':False,'coerce_one_of':False});err,msg=LLMatcher.validate_grammar_with_warnings(grammar,ll)
        if err:errors['llguidance']=msg
        else:compiled['llguidance']=grammar
    except Exception as e:errors['llguidance']=str(e)
    try:compiled['xgrammar']=compiler.compile_json_schema(schema,strict_mode=False)
    except Exception as e:errors['xgrammar']=str(e)
    try:compiled['outlines']=Index(build_regex_from_schema(schema),vocab)
    except Exception as e:errors['outlines']=str(e)
    for raw in prefixes:
        if name in cases:
            c=cases[name]['byte_certificate'];q=0
            for b in raw:q=c['states'][q]['edges'].get(str(b),c['sink'])
            live=c['states'][q]['distance'] is not None
        else:live=b'"\xf0\x9f\x98\x80"'.startswith(raw)
        segmentations={'byte-fallback':[fallback[b] for b in raw]}
        try:segmentations['hf-bpe']=hf.encode(raw.decode('utf-8'),add_special_tokens=False).ids
        except UnicodeDecodeError:pass
        for segmentation,ids in segmentations.items():
            assert all(i in pieces for i in ids) and b''.join(pieces[i] for i in ids)==raw
            out={'id':name,'prefix_hex':raw.hex(),'token_ids':ids,'segmentation':segmentation,'our_byte_and_token_live':live,'tools':{}}
            for engine,g in compiled.items():
                if engine=='llguidance':
                    m=LLMatcher(ll,g,log_level=0);admitted=m.consume_tokens(ids);accepting=bool(admitted and m.is_accepting());mask=m.compute_logit_bias() if admitted else b'';allowed=[i for i,v in enumerate(mask) if v]
                elif engine=='xgrammar':
                    m=xgr.GrammarMatcher(g,terminate_without_stop_token=True);admitted=all(m.accept_token(i) for i in ids);accepting=bool(admitted and m.is_completed());allowed=[]
                    if admitted:
                        if m.is_terminated():allowed=[eos]
                        else:
                            mask=xgr.allocate_token_bitmask(1,50257);m.fill_next_token_bitmask(mask);words=mask[0].tolist();allowed=[i for i in range(50257) if (words[i//32]>>(i%32))&1]
                else:
                    st=g.get_initial_state();admitted=True
                    for i in ids:
                        st=g.get_next_state(st,i)
                        if st is None:admitted=False;break
                    accepting=bool(admitted and g.is_final_state(st));allowed=list(g.get_allowed_tokens(st) or []) if admitted else []
                out['tools'][engine]={'admitted':admitted,'accepting':accepting,'allowed_count':len(allowed),'allowed_ids_sha256':digest(sorted(allowed)),'empty_mask_nonterminal':bool(admitted and not accepting and not allowed),'d_fallback_allowed':fallback[ord('d')] in allowed,'ff_fallback_allowed':fallback[255] in allowed}
            out['compile_errors']=errors;rows.append(out)
    rows.append({'id':name,'case_cpu_seconds':time.process_time()-begin})
print(json.dumps({'status':'PASS','versions':versions,'tokenizer_sha256':source['sha256'],'metadata':{'ordinary_tokens':len(pieces),'eos':eos,'single_byte_coverage':len(fallback),'llguidance_native_matching_pieces':len(pieces)-len(ll_differences),'llguidance_reserved_ff_id':fallback[255],'llguidance_non_special_byte_coverage':255,'ff_live_edges_in_all_byte_certificates':ff_live_edges,'xgrammar_native_byte_level_decoding_all_pieces_match':True,'hf_256_latin1_characters_roundtrip':True,'outlines_receives_explicit_raw_piece_map':True},'rows':rows,'cpu_seconds':time.process_time()-started,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
