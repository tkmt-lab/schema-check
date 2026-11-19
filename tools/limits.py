"""One worker at a time; stop below 2GiB, counting the orchestrator and descendants."""
import subprocess,os,signal,sys,time,tempfile,json,resource
from pathlib import Path
RSS_STOP=1536*1024**2

def tree_rss(root):
 r=subprocess.run(['ps','-axo','pid=,ppid=,rss='],capture_output=True,text=True,check=True,timeout=2)
 rows=[tuple(map(int,l.split())) for l in r.stdout.splitlines() if l.strip()];keep={root};changed=True
 while changed:
  before=len(keep);keep.update(pid for pid,parent,rss in rows if parent in keep);changed=len(keep)!=before
 return sum(rss*1024 for pid,parent,rss in rows if pid in keep)

def run(command,timeout=65,input_text=None,log=None):
 if not __debug__:raise RuntimeError('run without python -O')
 started=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);peak=0;reason=None
 env={**os.environ,'PYTHONPATH':'','PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','RAYON_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'}
 def linux_cap():
  if sys.platform.startswith('linux'):resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 with tempfile.TemporaryFile('w+') as fo,tempfile.TemporaryFile('w+') as fe,tempfile.TemporaryFile('w+') as fi:
  if input_text is not None:fi.write(input_text);fi.seek(0)
  p=subprocess.Popen(list(map(str,command)),stdin=fi,stdout=fo,stderr=fe,env=env,start_new_session=True,preexec_fn=linux_cap if sys.platform.startswith('linux') else None)
  try:
   while p.poll() is None:
    try:peak=max(peak,tree_rss(os.getpid()))
    except Exception as e:reason='memory monitor unavailable: '+str(e)
    if peak>RSS_STOP:reason='RSS precaution stop below 2GiB'
    if time.monotonic()-started>timeout:reason='wall limit'
    if reason:os.killpg(p.pid,signal.SIGKILL);break
    time.sleep(.025)
   p.wait()
  finally:
   if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
  fo.seek(0);fe.seek(0);stdout=fo.read();stderr=fe.read()
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 row=dict(command=list(map(str,command)),returncode=p.returncode,resource_stop=reason,wall_seconds=time.monotonic()-started,cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,peak_tree_rss_bytes=peak,stdout=stdout,stderr=stderr)
 if log:Path(log).write_text(json.dumps(row,indent=2)+'\n')
 return row
