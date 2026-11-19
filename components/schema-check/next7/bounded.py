"""Run one auxiliary calculation under the same wall/RSS stop policy."""
import sys,time,resource,subprocess,json
from pathlib import Path
P=Path(__file__).resolve().parent;label=sys.argv[1];cmd=sys.argv[2:];start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);peak=0;stop=None
with (P/(label+'.json')).open('w') as fo,(P/(label+'.stderr')).open('w') as fe:
    proc=subprocess.Popen(cmd,stdout=fo,stderr=fe)
    while proc.poll() is None:
        mem=subprocess.run(['ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True).stdout.strip()
        if mem:peak=max(peak,int(mem)*1024)
        if peak>1536*1024**2 or time.monotonic()-start>30:stop='RSS precaution' if peak>1536*1024**2 else 'wall limit';proc.kill();break
        time.sleep(.025)
    proc.wait()
after=resource.getrusage(resource.RUSAGE_CHILDREN)
record={'status':'PASS' if proc.returncode==0 and stop is None else 'UNKNOWN' if stop or proc.returncode<0 else 'ERROR','returncode':proc.returncode,'stop':stop,'wall_seconds':time.monotonic()-start,'cpu_seconds_with_monitor':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'peak_monitored_rss_bytes':peak}
(P/(label+'-RESOURCE.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(0 if record['status']=='PASS' else 1)
