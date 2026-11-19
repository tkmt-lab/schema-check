"""Fixed next3 native byte-API settings; no scientific language claims here."""
import json,sys,time,signal,resource,os
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path[:0]=[str(P),str(P/'schema_check/_engine/next7')]
from extended import canonical
from schema_check._shared import parse_schema,dumps

def worker(c):
    resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(29);start=time.process_time()
    out={'id':c['id']}
    probes=[b'',b'0',b'-0',b'0.0',b'1',b'-1',b'0.1',b'0.3',b'0.30000000000000004',b'1.5',b'1e0',b'true',b'false',b'null',b'""',b'[]',b'[',b'[true',b'[true,true]',b'[1,1.0]',b'{}']
    probes += [canonical(t['data']) for t in c['tests']]
    if '_mask_trace'in c:probes.append(bytes(c['_mask_trace']))
    probes=list(dict.fromkeys(probes))
    from llguidance import LLMatcher,LLTokenizer,TokenizerWrapper
    class Bytes:
        eos_token_id=256;bos_token_id=None;tokens=[bytes([i]) for i in range(256)]+[b'<eos>'];special_token_ids=[256]
        def __call__(self,s): return list(s if isinstance(s,bytes) else s.encode())
    tk=LLTokenizer(TokenizerWrapper(Bytes()),slices=[])
    try:
        g=LLMatcher.grammar_from_json_schema(json.loads(json.dumps(c['schema'],sort_keys=True)),overrides={'lenient':False,'coerce_one_of':False})
        err,msg=LLMatcher.validate_grammar_with_warnings(g,tk);rows=[]
        if not err:
            for p in probes:
                m=LLMatcher(tk,g,log_level=0);admitted=m.consume_tokens(list(p))
                mask=m.compute_logit_bias() if admitted else b''
                rows.append({'bytes':list(p),'admitted':admitted,'accepting':bool(admitted and m.is_accepting()),'allowed':[i for i,x in enumerate(mask) if x],'error':m.get_error()})
                if list(p)==c.get('_mask_trace'):
                    replay=LLMatcher(tk,g,log_level=0);chain=[]
                    for b in p:
                        current=replay.compute_logit_bias();chain.append(bool(current[b]))
                        if not replay.consume_tokens([b]):break
                    rows[-1]['byte_mask_path']={'all_steps_allowed':all(chain) and len(chain)==len(p),'steps':chain}
        out['llguidance']={'compile_error':err,'messages':msg,'prefixes':rows}
    except Exception as e: out['llguidance']={'compile_error':True,'messages':[str(e)],'prefixes':[]}
    from outlines_core import Index,Vocabulary
    from outlines_core.json_schema import build_regex_from_schema
    try:
        regex=build_regex_from_schema(json.dumps(c['schema'],sort_keys=True));idx=Index(regex,Vocabulary(256,{bytes([i]):[i] for i in range(256)}));rows=[]
        for p in probes:
            st=idx.get_initial_state();admitted=True
            for b in p:
                nxt=idx.get_next_state(st,b)
                if nxt is None: admitted=False;break
                st=nxt
            rows.append({'bytes':list(p),'admitted':admitted,'accepting':bool(admitted and idx.is_final_state(st)),'allowed':list(idx.get_allowed_tokens(st) or []) if admitted else []})
            if list(p)==c.get('_mask_trace'):
                trace=idx.get_initial_state();chain=[]
                for b in p:
                    chain.append(b in (idx.get_allowed_tokens(trace) or []));trace=idx.get_next_state(trace,b)
                    if trace is None:break
                rows[-1]['byte_mask_path']={'all_steps_allowed':all(chain) and len(chain)==len(p),'steps':chain}
        out['outlines']={'compile_error':False,'regex':regex,'prefixes':rows}
    except Exception as e: out['outlines']={'compile_error':True,'messages':[type(e).__name__+': '+str(e)],'prefixes':[]}
    try:
        import torch,xgrammar as xgr
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
        ti=xgr.TokenizerInfo([bytes([i]) for i in range(256)]+[b'<eos>'],stop_token_ids=[256])
        compiler=xgr.GrammarCompiler(ti,max_threads=1,cache_enabled=False)
        compiled=compiler.compile_json_schema(json.dumps(c['schema'],sort_keys=True),strict_mode=False)
        rows=[]
        for pfx in probes:
            m=xgr.GrammarMatcher(compiled,terminate_without_stop_token=True)
            admitted=m.accept_string(pfx)
            accepting=bool(admitted and m.is_completed())
            allowed=[]
            if admitted:
                if m.is_terminated(): allowed=[256]
                else:
                    mask=xgr.allocate_token_bitmask(1,257)
                    m.fill_next_token_bitmask(mask)
                    words=mask[0].tolist();allowed=[i for i in range(257) if (words[i//32]>>(i%32))&1]
            rows.append({'bytes':list(pfx),'admitted':admitted,'accepting':accepting,'allowed':allowed})
            if list(pfx)==c.get('_mask_trace'):
                replay=xgr.GrammarMatcher(compiled,terminate_without_stop_token=True);chain=[]
                for b in pfx:
                    bits=xgr.allocate_token_bitmask(1,257);replay.fill_next_token_bitmask(bits);ws=bits[0].tolist();chain.append(bool((ws[b//32]>>(b%32))&1))
                    if not replay.accept_token(b):break
                rows[-1]['byte_mask_path']={'all_steps_allowed':all(chain) and len(chain)==len(pfx),'steps':chain}
        out['xgrammar']={'compile_error':False,'prefixes':rows,'strict_mode':False,'max_threads':1}
    except Exception as e: out['xgrammar']={'compile_error':True,'messages':[type(e).__name__+': '+str(e)],'prefixes':[]}
    out['cpu_seconds']=time.process_time()-start;out['rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return out

if __name__=='__main__':print(json.dumps(worker(json.load(sys.stdin)),ensure_ascii=False))
