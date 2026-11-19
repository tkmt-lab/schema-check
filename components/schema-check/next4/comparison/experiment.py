import json,sys,time,signal,resource,subprocess,os
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/"schema_check/_engine/next3"))

def worker(c):
    resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(29);start=time.process_time()
    from generate import generate
    from finite_semantics import canonical,Unsupported
    def wire(x):
        try: return canonical(x)
        except Unsupported: return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    from checker import check,prefix
    cert=generate(c['schema']);supported=cert['status'] in ['EMPTY','NONEMPTY']
    out={'id':c['id'],'kind':c['kind'],'schema':c['schema'],'ours':cert}
    if supported:
        out['verified']=check(c['schema'],cert)
        # Normal forms used for the reference and the three external tools.
        for t in c['tests']:
            raw=wire(t['data'])
            assert prefix(cert,raw)['accepting']==t['valid'],(c['id'],t)
    probes=[b'',b'"']+[b'"'+b'a'*i for i in range(1,7)]+[b'"b',b'"ab',b'"c','"é'.encode(),'"😀'.encode(),b'"\xf0\x9f']
    probes += [b'{',b'{\"modifier\":',b'{\"k\":\"abc',b'{\"k\":\"abcd',b'{\"extra\":']
    probes += [wire(t['data']) for t in c['tests']]
    probes=list(dict.fromkeys(probes))
    if supported: out['prefixes']=[{'bytes':list(p),**prefix(cert,p)} for p in probes]
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
        out['xgrammar']={'compile_error':False,'prefixes':rows,'strict_mode':False,'max_threads':1}
    except Exception as e: out['xgrammar']={'compile_error':True,'messages':[type(e).__name__+': '+str(e)],'prefixes':[]}
    out['cpu']=time.process_time()-start;out['rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return out

def cases():
    return json.loads((P/'CASES.json').read_text())

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':
        try: print(json.dumps(worker(json.load(sys.stdin)),ensure_ascii=False))
        except Exception as e: print(json.dumps({'worker_error':type(e).__name__+': '+str(e)}));sys.exit(1)
    else:
        cc=cases();(P/'CASES.json').write_text(json.dumps(cc,ensure_ascii=False,indent=2)+'\n');rr=[];usage=resource.getrusage(resource.RUSAGE_CHILDREN)
        for c in cc:
            with open(P/'worker-out.tmp','w+') as fo,open(P/'worker-err.tmp','w+') as fe:
                proc=subprocess.Popen([sys.executable,'-B',__file__,'worker'],stdin=subprocess.PIPE,stdout=fo,stderr=fe,text=True,env={**os.environ,'RAYON_NUM_THREADS':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','MKL_NUM_THREADS':'1'})
                proc.stdin.write(json.dumps(c));proc.stdin.close();wall=time.monotonic();peak=0;stop=None
                while proc.poll() is None:
                    mem=subprocess.run(['ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True).stdout.strip()
                    if mem: peak=max(peak,int(mem)*1024)
                    if peak>1536*1024**2 or time.monotonic()-wall>29: stop='RESOURCE_LIMIT';proc.kill();break
                    time.sleep(.025)
                proc.wait();fo.seek(0);fe.seek(0);body=fo.read();err=fe.read()
            try: r=json.loads(body)
            except ValueError: r={'worker_error':stop or 'no JSON','stdout':body}
            r.update(id=c['id'],kind=c['kind'],returncode=proc.returncode,stderr=err,wall=time.monotonic()-wall,monitored_rss=peak);rr.append(r)
            (P/'RESULTS.json').write_text('[\n'+',\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in rr)+'\n]\n')
            now=resource.getrusage(resource.RUSAGE_CHILDREN)
            if now.ru_utime+now.ru_stime-usage.ru_utime-usage.ru_stime>7200: raise RuntimeError('total CPU limit')
        print('cases',len(rr),'errors',sum('worker_error' in r for r in rr))
