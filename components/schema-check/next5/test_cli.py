import tempfile,subprocess,sys,json,time,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(59);start=time.process_time();P=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(dir=P,prefix='.cli-') as t:
    target=Path(t)/'tokens.json';source=P.parent/'next4/examples/issue-858-prefix.result.json';cmd=[sys.executable,'-B',str(P/'token-check')]
    r=subprocess.run(cmd+[str(source),'--prefix-token-ids','4895,4666,7483,1298','-o',str(target),'--quiet'],capture_output=True,text=True,timeout=30);assert r.returncode==0,(r.stdout,r.stderr)
    artifact=json.loads(target.read_text());assert artifact['query']['token_distance']==2
    r=subprocess.run(cmd+['verify',str(target),'--schema',str(P.parent/'next4/examples/issue-858.json'),'--quiet'],capture_output=True,text=True,timeout=30);assert r.returncode==0,(r.stdout,r.stderr)
    accepted=json.loads(r.stdout);rejected=[]
    r=subprocess.run([sys.executable,'-O','-B',str(P/'token-check'),'verify',str(target),'--quiet'],capture_output=True,text=True,timeout=30)
    assert r.returncode==1 and 'without -O' in json.loads(r.stdout)['explanation']
    for name in ['format','explanation','boolean_query_distance']:
        bad=json.loads(json.dumps(artifact))
        if name=='format':bad['format']='other'
        elif name=='explanation':bad['explanation']='No token completion in the canonical language.'
        else:bad['query']['token_distance']=True
        target.write_text(json.dumps(bad));r=subprocess.run(cmd+['verify',str(target),'--quiet'],capture_output=True,text=True,timeout=30);assert r.returncode==1 and json.loads(r.stdout)['verification']=='FAIL';rejected.append(name)
print(json.dumps({'status':'PASS','supplied_prefix_token_ids':artifact['supplied_prefix_token_ids'],'query':artifact['query'],'separate_verifier':accepted,'optimized_interpreter_refused':True,'mutations_rejected':rejected,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
