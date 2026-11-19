"""Check the complete detached producer, byte prefixes, and the public wall-stop result."""
import tempfile,shutil,subprocess,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent.parent;rows=[];started=time.monotonic()
with tempfile.TemporaryDirectory(dir=P,prefix='.portable-') as tmp:
    root=Path(tmp);bundle=root/'bundle';bundle.mkdir();shutil.copy2(P/'schema-check',bundle/'schema-check');shutil.copytree(P/'schema_check',bundle/'schema_check',ignore=shutil.ignore_patterns('__pycache__'))
    elsewhere=root/'elsewhere';elsewhere.mkdir();schema=root/'schema.json';artifact=root/'artifact.json'
    for s,mode in [({'const':{'x':[True,1]}},'finite-object-enum'),({'type':'string','pattern':'^[ab]*$','minLength':2},'symbolic-string'),({'oneOf':[True,True]},'finite-fallback')]:
        schema.write_text(json.dumps(s));base=[sys.executable,'-I','-S','-B',str(bundle/'schema-check')]
        r=subprocess.run(base+[str(schema),'-o',str(artifact),'--quiet'],cwd=elsewhere,capture_output=True,text=True,timeout=30)
        out=json.loads(artifact.read_text());assert r.returncode==0 and out['certificate']['mode']==mode,(r.stderr,out)
        v=subprocess.run(base+['verify',str(artifact),'--schema',str(schema),'--quiet'],cwd=elsewhere,capture_output=True,text=True,timeout=30);assert v.returncode==0 and json.loads(v.stdout)['verification']=='PASS'
        rows.append({'mode':mode,'detached_producer_and_verifier':'PASS'})
    r=subprocess.run(base+[str(schema),'--timeout','0.000001','--quiet'],cwd=elsewhere,capture_output=True,text=True,timeout=5)
    stopped=json.loads(r.stdout);assert r.returncode==3 and stopped['support']=='UNKNOWN' and stopped['language']['empty'] is None
    rows.append({'check':'public wall stop is UNKNOWN, never EMPTY','status':'PASS'})
print(json.dumps({'status':'PASS','checks':rows,'wall_seconds':time.monotonic()-started},indent=2))
