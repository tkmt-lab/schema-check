"""Few corpus examples, native metadata plus explicitly labelled raw-piece adapters."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import sys,json,gzip,time,resource,signal
from pathlib import Path
from vocabulary import load,digest
resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(59);start=time.process_time()
key,index=sys.argv[1],int(sys.argv[2]);P=Path(__file__).resolve().parent
first,later,stop,source,j=load(key);path=P.parents[2]/source['path']
r=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()))[index]
simplified='--simple-object' in sys.argv
if simplified:
    assert index==34
    r['schema']={'const':{}}
schema=json.dumps(r['schema'],sort_keys=True)
from llguidance import LLTokenizer,LLMatcher
errors={};compiled={}
try:
    ll=LLTokenizer(str(path),eos_token=stop,slices=[])
    grammar=LLMatcher.grammar_from_json_schema(r['schema'],overrides={'lenient':False,'coerce_one_of':False})
    err,msg=LLMatcher.validate_grammar_with_warnings(grammar,ll)
    if err:errors['llguidance']=msg
    else:compiled['llguidance']=(ll,grammar)
except Exception as e:errors['llguidance']=str(e)
from transformers import PreTrainedTokenizerFast
import torch,xgrammar as xgr
torch.set_num_threads(1);torch.set_num_interop_threads(1)
hf=PreTrainedTokenizerFast(tokenizer_file=str(path),unk_token='<unk>',pad_token='<pad>')
encoded=[w for w,score in j['model']['vocab']]
for t in j['added_tokens']:
    if t['id']>=len(encoded):encoded.extend(['']*(t['id']+1-len(encoded)))
    encoded[t['id']]=t['content']
for mode in ['auto','explicit-metaspace']:
    try:
        ti=xgr.TokenizerInfo.from_huggingface(hf,stop_token_ids=[stop]) if mode=='auto' else xgr.TokenizerInfo(encoded,vocab_type=xgr.VocabType.BYTE_FALLBACK,stop_token_ids=[stop],add_prefix_space=True)
        compiled['xgrammar-'+mode]=xgr.GrammarCompiler(ti,max_threads=1,cache_enabled=False).compile_json_schema(schema,strict_mode=False)
    except Exception as e:errors['xgrammar-'+mode]=str(e)
from outlines_core import Vocabulary,Index
from outlines_core.json_schema import build_regex_from_schema
regex=build_regex_from_schema(schema)
for phase,table in [('first',first),('continuation',later)]:
    try:
        groups={}
        for i,b in table.items():groups.setdefault(b,[]).append(i)
        compiled['outlines-'+phase]=Index(regex,Vocabulary(stop,groups))
    except Exception as e:errors['outlines-'+phase]=str(e)
probes=[([],b'',0)]
quote=next((i for i,b in first.items() if b==b'"' and later[i]==b'"'),None)
for token,b in first.items():
    if b==b'"':probes.append(([token],b'"',1))
rows=[];vsize=max([t['id'] for t in j['added_tokens']]+list(first))+1
def xmask(m):
    if m.is_terminated():return [stop]
    mask=xgr.allocate_token_bitmask(1,vsize);m.fill_next_token_bitmask(mask);words=mask[0].tolist()
    return [i for i in range(vsize) if (words[i//32]>>(i%32))&1]
for ids,raw,phase in probes:
    state=0
    for b in raw:state=r['byte_certificate']['states'][state]['edges'].get(str(b),r['byte_certificate']['sink'])
    our=json.loads((P/key/f'all/{index:03}.json').read_text())['proof'];N=len(our['quotient']['states'])
    row={'token_ids':ids,'prefix_hex':raw.hex(),'phase':phase,'byte_live':r['byte_certificate']['states'][state]['distance'] is not None,
         'token_live':our['graph'][phase*N+our['quotient']['mapping'][state]]['distance'] is not None,'tools':{}}
    for engine,g in compiled.items():
        if engine.startswith('outlines-') and engine!=('outlines-first' if phase==0 else 'outlines-continuation'):continue
        try:
            if engine=='llguidance':
                tk,grammar=g;m=LLMatcher(tk,grammar,log_level=0);admitted=m.consume_tokens(ids);accepting=bool(admitted and m.is_accepting());allowed=[i for i,b in enumerate(m.compute_logit_bias()) if b] if admitted else []
            elif engine.startswith('xgrammar-'):
                m=xgr.GrammarMatcher(g,terminate_without_stop_token=True);admitted=True;chain=[]
                for token in ids:
                    chain.append(token in xmask(m))
                    if not m.accept_token(token):admitted=False;break
                accepting=bool(admitted and m.is_completed());allowed=xmask(m) if admitted else []
            else:
                st=g.get_initial_state();admitted=True
                # Reconstruct the exact emitted bytes in the continuation raw-piece API.
                # A first-token ▁" and a literal " emit the same prefix, but have different later pieces.
                replay_ids=[quote] if raw==b'"' else []
                for token in replay_ids:
                    st=g.get_next_state(st,token)
                    if st is None:admitted=False;break
                accepting=bool(admitted and g.is_final_state(st));allowed=list(g.get_allowed_tokens(st) or []) if admitted else []
            row['tools'][engine]={'admitted':admitted,'accepting':accepting,'allowed_count':len(allowed),'allowed_ids_sha256':digest(sorted(allowed)),
                 'allowed_ids':allowed if len(allowed)<25 else None,'empty_mask_nonterminal':bool(admitted and not accepting and not allowed),'stop_allowed':stop in allowed}
            if engine.startswith('xgrammar-'):row['tools'][engine]['prefix_every_step_mask_allowed']=all(chain)
            if engine.startswith('outlines-'):row['tools'][engine]['adapter_replay_token_ids']=replay_ids
        except Exception as e:row['tools'][engine]={'runtime_error':str(e)}
    rows.append(row)
print(json.dumps({'key':key,'id':r['id'],'schema':r['schema'],'equivalent_simple_object_control':simplified,'errors':errors,'rows':rows,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},ensure_ascii=False,indent=2))
