"""Sequential runner with per-case combined wall/CPU, RSS, and whole-run limits."""
import sys,json,gzip,subprocess,time,resource,os
from pathlib import Path
P=Path(__file__).resolve().parent;allrows=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()))
selected=sys.argv[1:];verify_only='--verify-only' in selected;selected=[s for s in selected if s!='--verify-only'];indices=[i for i,r in enumerate(allrows) if not selected or r['id'] in selected];mode='pilot' if selected else 'all';out=P/mode;out.mkdir(exist_ok=True);records=[];baseline=resource.getrusage(resource.RUSAGE_CHILDREN);record_name='RECHECK-RUN.json' if verify_only else f'{mode.upper()}-RUN.json'
for index in indices:
    r=allrows[index];deadline=time.monotonic()+60;started=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);phases=[];failed=None;artifact=out/f'{index:03d}.json'
    for phase in (['verify'] if verify_only else ['produce','verify']):
        remaining=deadline-time.monotonic()
        if remaining<=0:failed='combined wall limit';break
        with (out/f'{index:03d}-{phase}.stdout').open('w+') as fo,(out/f'{index:03d}-{phase}.stderr').open('w+') as fe:
            proc=subprocess.Popen([sys.executable,'-B',str(P/'worker.py'),phase,str(index),str(artifact),str(remaining)],stdout=fo,stderr=fe,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'})
            peak=0;reason=None
            while proc.poll() is None:
                s=subprocess.run(['ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True).stdout.strip()
                if s:peak=max(peak,int(s)*1024)
                if peak>1536*1024**2 or time.monotonic()>=deadline:reason='RSS precaution' if peak>1536*1024**2 else 'combined wall limit';proc.kill();break
                time.sleep(.025)
            proc.wait();fo.seek(0);fe.seek(0);body,err=fo.read(),fe.read()
        if proc.returncode:
            if reason or proc.returncode<0:failed=reason or 'worker resource/signal stop';break
            raise RuntimeError((r['id'],phase,proc.returncode,err))
        value=json.loads(body);phases.append({'phase':phase,'rss_monitored_bytes':peak,**value})
        if phase=='produce' and value['status']=='UNKNOWN':failed=json.loads(artifact.read_text())['reason'];break
    after=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime
    record={'index':index,'id':r['id'],'status':'UNKNOWN' if failed else 'PASS','reason':failed,'wall_seconds':time.monotonic()-started,'cpu_seconds_with_monitor':cpu,'phases':phases}
    if cpu>60:record.update(status='UNKNOWN',reason='combined CPU limit')
    records.append(record);(P/record_name).write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['id','status','reason','wall_seconds','cpu_seconds_with_monitor']}),flush=True)
    assert after.ru_utime+after.ru_stime-baseline.ru_utime-baseline.ru_stime<10800,'whole-run CPU limit'
