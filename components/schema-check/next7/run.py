"""Sequential combined per-case deadline across producer/checker/native phases."""
import json,sys,time,resource,subprocess,os
from pathlib import Path
P=Path(__file__).resolve().parent;cases=json.loads((P/'CASES.json').read_text());selected=set(sys.argv[1:]);resume='--resume'in selected;selected.discard('--resume');records=json.loads((P/'ALL-RUN.json').read_text()) if resume else []
completed={r['id'] for r in records if r['status']=='PASS'};prior_cpu=sum(r['cpu_seconds_with_monitor'] for r in records)
old={r['id']:r for r in json.loads((P.parent/'next3/RESULTS.json').read_text())}
for name in ['all','native','logs']:(P/name).mkdir(exist_ok=True)
baseline=resource.getrusage(resource.RUSAGE_CHILDREN)
for i,c in enumerate(cases):
    if selected and c['id']not in selected:continue
    if resume and c['id']in completed:continue
    started=time.monotonic();deadline=started+30;before=resource.getrusage(resource.RUSAGE_CHILDREN);phases=[];stop=None
    for phase in ['produce','verify','native']:
        if phase=='native':
            previous=old.get(c['id']);supported=json.loads((P/'all'/f'{i:03d}.json').read_text())['bundle']['support']=='SUPPORTED'
            if previous and previous['ours']['status']in ['EMPTY','NONEMPTY']:
                value={'id':c['id'],'reused_input_commit':'50b08ead0','reused_path':'components/schema-check/next3/RESULTS.json',**{e:previous[e] for e in ['llguidance','xgrammar','outlines']}}
                (P/'native'/f'{i:03d}.json').write_text(json.dumps(value,ensure_ascii=False)+'\n');phases.append({'phase':phase,'status':'FIXED_BASELINE_REUSED'});continue
            if not supported:continue
        remaining=deadline-time.monotonic()
        if remaining<=0:stop='combined wall limit';break
        with (P/'logs'/f'{i:03d}-{phase}.stdout').open('w+') as fo,(P/'logs'/f'{i:03d}-{phase}.stderr').open('w+') as fe:
            proc=subprocess.Popen([sys.executable,'-B',str(P/'worker.py'),phase,str(i),str(remaining)],stdout=fo,stderr=fe,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','TOKENIZERS_PARALLELISM':'false','RAYON_NUM_THREADS':'1','HF_HUB_OFFLINE':'1'})
            peak=0
            while proc.poll()is None:
                rss=subprocess.run(['ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True).stdout.strip()
                if rss:peak=max(peak,int(rss)*1024)
                if peak>1536*1024**2 or time.monotonic()>deadline:stop='RSS precaution' if peak>1536*1024**2 else 'combined wall limit';proc.kill();break
                time.sleep(.025)
            proc.wait();fo.seek(0);fe.seek(0);body,err=fo.read(),fe.read()
        if proc.returncode:
            if stop or proc.returncode<0:stop=stop or 'worker signal/resource';break
            raise RuntimeError((c['id'],phase,err,body))
        phases.append({'phase':phase,'monitored_rss_bytes':peak,**json.loads(body)})
    after=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime
    if cpu>30:stop='combined CPU limit'
    record={'index':i,'id':c['id'],'status':'UNKNOWN' if stop else 'PASS','reason':stop,'wall_seconds':time.monotonic()-started,'cpu_seconds_with_monitor':cpu,'phases':phases};records.append(record)
    (P/('PILOT-RUN.json' if selected else 'ALL-RUN.json')).write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['id','status','reason','wall_seconds']}),flush=True)
    if stop:break
    assert prior_cpu+after.ru_utime+after.ru_stime-baseline.ru_utime-baseline.ru_stime<7200,'aggregate CPU limit'
