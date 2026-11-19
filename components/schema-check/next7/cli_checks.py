"""Public CLI round trips, exact input preservation and fail-closed controls."""
import sys,json,copy,subprocess,time,resource
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from schema_check._shared import load_json,dumps
start=time.process_time();folder=P/'cli-controls';folder.mkdir(exist_ok=True);rows=[]
def command(args):
    r=subprocess.run([sys.executable,'-B',str(P/'schema-check'),*map(str,args),'--quiet'],capture_output=True,text=True,timeout=10)
    b=load_json(r.stdout);return r.returncode,b
examples={
    'tenths':'{"type":"number","minimum":0.1,"maximum":0.3,"multipleOf":0.1}',
    'precise':'{"const":0.1000000000000000000000000000000001}',
    'array':'{"type":"array","items":{"enum":[true,1,1.0,false]},"uniqueItems":true}',
    'numeric-unbounded':'{"type":"number","minimum":-1.25,"exclusiveMaximum":2.5}',
    'empty':'{"type":"array","items":{"enum":[0,1]},"uniqueItems":true,"minItems":3}',
    'no-type':'{"minimum":1}',
    'open-array':'{"type":"array","maxItems":1}',
    'large-modulus':'{"type":"integer","multipleOf":0.123456789}',
    'invalid-multiple':'{"type":"number","multipleOf":0}',
    'invalid-items':'{"type":"array","minItems":true}',
}
for name,text in examples.items():
    schema=folder/(name+'.schema.json');schema.write_text(text+'\n');args=[schema]
    if name=='tenths':args+=['--prefix','0.']
    rc,b=command(args);expected='UNKNOWN' if name=='large-modulus' else 'UNSUPPORTED' if name in ['no-type','open-array'] else 'INVALID_INPUT' if name.startswith('invalid-') else 'SUPPORTED'
    assert b['support']==expected,(name,b)
    artifact=folder/(name+'.artifact.json');artifact.write_text(dumps(b)+'\n')
    if expected=='SUPPORTED':
        assert command(['verify',artifact,'--schema',schema])[0]==0
        if name=='precise':assert b['language']['shortest_example']['utf8']=='0.1000000000000000000000000000000001'
        if name=='tenths':assert b['prefix']['shortest_completion']['utf8']=='1'
        if name=='empty':assert b['language']['empty'] is True
    rows.append({'case':name,'support':b['support'],'returncode':rc})
base=load_json((folder/'numeric-unbounded.artifact.json').read_text());mutations=[]
def distance(b):b['certificate']['states'][0]['distance']=True
def completion(b):b['certificate']['states'][0]['completion']=[120]
def transition(b):b['certificate']['states'][0]['edges']['48']=b['certificate']['sink']
def claim(b):b['language']['empty']=True
def schema_value(b):b['input']['schema']['minimum']=-100
for mutate in [distance,completion,transition,claim,schema_value]:
    b=copy.deepcopy(base);mutate(b);f=folder/(mutate.__name__+'.mutated.json');f.write_text(dumps(b)+'\n');rc,r=command(['verify',f]);assert rc==1 and r['verification']=='FAIL',(mutate.__name__,r);mutations.append(mutate.__name__)
# A schema-document whitespace edit must fail exact document binding.
schema=folder/'numeric-unbounded.schema.json';altered=folder/'whitespace.schema.json';altered.write_text(' '+schema.read_text())
assert command(['verify',folder/'numeric-unbounded.artifact.json','--schema',altered])[0]==1
# Optimized Python must not silently turn verification assertions off.
r=subprocess.run([sys.executable,'-O','-B',str(P/'schema-check'),'verify',str(folder/'distance.mutated.json'),'--quiet'],capture_output=True,text=True,timeout=10)
assert r.returncode==1 and load_json(r.stdout)['verification']=='FAIL'
r=subprocess.run([sys.executable,'-O','-B',str(P/'schema_check/_worker.py')],input='{}',capture_output=True,text=True,timeout=10)
assert r.returncode!=0 and 'verification assertions must be enabled'in r.stderr
print(json.dumps({'status':'PASS','roundtrips':rows,'corruptions_rejected':mutations,'schema_document_binding':True,'optimized_frontend_still_rejects_corruption':True,'optimized_checker_worker_refused':True,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
