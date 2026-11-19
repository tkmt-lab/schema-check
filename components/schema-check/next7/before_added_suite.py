"""Compare the previous CLI on exactly the same 42 newly sampled original groups."""
import json,subprocess,sys,time,resource
from pathlib import Path
P=Path(__file__).resolve().parent;cases=json.loads((P/'CASES.json').read_text());folder=P/'before-added-suite';folder.mkdir(exist_ok=True);rows=[];start=time.process_time()
for i,c in enumerate(cases):
    if c['scope']!='new-original-42':continue
    path=folder/(c['id']+'.json');path.write_text(json.dumps(c['schema'],ensure_ascii=False)+'\n')
    proc=subprocess.run([sys.executable,'-B',str(P.parent/'next4/schema-check'),str(path),'--quiet'],capture_output=True,text=True,timeout=30)
    b=json.loads(proc.stdout);after=json.loads((P/'all'/f'{i:03d}.json').read_text())['bundle']
    rows.append({'id':c['id'],'before':b['support'],'after':after['support'],'before_returncode':proc.returncode})
print(json.dumps({'records':rows,'before_supported':sum(r['before']=='SUPPORTED' for r in rows),'after_supported':sum(r['after']=='SUPPORTED' for r in rows),'gained':[r['id'] for r in rows if r['before']!='SUPPORTED' and r['after']=='SUPPORTED'],'lost':[r['id'] for r in rows if r['before']=='SUPPORTED' and r['after']!='SUPPORTED'],'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
