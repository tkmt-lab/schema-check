"""Public-contract checks plus all frozen next3 cases and producer-blocked legacy replay."""
import json,gzip,subprocess,tempfile,shutil,sys,time,resource,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent.parent;start=time.monotonic();usage=resource.getrusage(resource.RUSAGE_CHILDREN);rows=[]

def command(args,code=0,cwd=None,optimized=False):
    exe=[sys.executable]+(['-O'] if optimized else [])+['-B',str(P/'schema-check')]
    r=subprocess.run(exe+list(map(str,args)),capture_output=True,text=True,timeout=40,cwd=cwd)
    assert r.returncode==code,(args,r.returncode,r.stdout[:500],r.stderr)
    return json.loads(r.stdout) if r.stdout.strip() else None

def progress(msg):
    now=resource.getrusage(resource.RUSAGE_CHILDREN);assert now.ru_utime+now.ru_stime-usage.ru_utime-usage.ru_stime<1800
    print(msg,flush=True)

cache=P/'.cache';cache.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=cache,prefix='.tests-') as temp:
    t=Path(temp);schema=t/'schema.json';artifact=t/'result.json'
    cases=json.loads((P/'comparison/CASES.json').read_text());expected=json.loads((P/'tests/expected-statuses.json').read_text());supported=0;fixture_checks=0
    def wire(x):
        if type(x) is float and x.is_integer():return int(x)
        if type(x) is list:return [wire(y) for y in x]
        if type(x) is dict:return {k:wire(v) for k,v in x.items()}
        return x
    for i,c in enumerate(cases):
        schema.write_text(json.dumps(c['schema'],ensure_ascii=False)+'\n');want=expected[c['id']]
        command([schema,'--quiet','-o',artifact],0 if want in ['EMPTY','NONEMPTY'] else 3)
        result=json.loads(artifact.read_text())
        if want in ['EMPTY','NONEMPTY']:
            assert result['support']=='SUPPORTED' and result['language']['empty']==(want=='EMPTY'),c['id']
            assert command(['verify',artifact,'--schema',schema,'--quiet'])['verification']=='PASS';supported+=1
            cert=result['certificate']
            for f in c['tests']:
                raw=json.dumps(wire(f['data']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();q=0
                for b in raw:q=cert['states'][q]['edges'].get(str(b),cert['sink'])
                assert cert['states'][q]['accept']==f['valid'],(c['id'],f);fixture_checks+=1
        else:assert result['support']==want,(c['id'],result['support'],want)
        if i%25==0:progress(f'CLI corpus {i+1}/{len(cases)}')
    assert supported==83
    rows.append({'check':'frozen corpus through public CLI and separate verify','schemas':len(cases),'supported':supported,'fixture_value_checks':fixture_checks,'status':'PASS'})
    legacy=json.loads(gzip.decompress((P/'tests/legacy-proofs.json.gz').read_bytes()))
    for i,r in enumerate(legacy):
        proc=subprocess.run([sys.executable,'-I','-S','-B',str(P/'tests/legacy_check.py')],input=json.dumps(r),capture_output=True,text=True,timeout=30)
        assert proc.returncode==0 and json.loads(proc.stdout)['status']=='PASS',(r['id'],proc.stderr)
        if i%25==0:progress(f'legacy proof {i+1}/{len(legacy)}')
    rows.append({'check':'original next3 certificates with producer access blocked','certificates':len(legacy),'status':'PASS'})

    def produce(s,*args,want='SUPPORTED'):
        schema.write_text(json.dumps(s,ensure_ascii=False)+'\n')
        command([schema,'--quiet','-o',artifact,*args],0 if want=='SUPPORTED' else 3)
        r=json.loads(artifact.read_text());assert r['support']==want
        if want=='SUPPORTED':assert command(['verify',artifact,'--schema',schema,'--quiet'])['verification']=='PASS'
        return r
    r=produce({'type':'string','pattern':'^[ab]*$','minLength':2},'--prefix','"a')
    assert r['prefix']['shortest_completion']['bytes']==[97,34] and r['certificate']['mode']=='symbolic-string'
    r=produce({'type':'string','pattern':'^[ab]*$','minLength':2},'--prefix','"c')
    assert not r['prefix']['can_complete'] and r['prefix']['evidence']['distance'] is None
    produce({'oneOf':[True,True]});assert json.loads(artifact.read_text())['certificate']['mode']=='finite-fallback'
    r=produce({'const':'😀'},'--prefix-hex','22f09f')
    assert r['prefix']['shortest_completion']['bytes']==[152,128,34] and r['prefix']['shortest_completion']['utf8'] is None
    prefix=t/'prefix.bin';prefix.write_bytes(bytes.fromhex('22f09f'));r=produce({'const':'😀'},'--prefix-file',prefix)
    assert r['prefix']['input']['bytes']==[34,240,159]
    prefix.write_bytes(b'"a\n');r=produce({'const':'a'},'--prefix-file',prefix);assert not r['prefix']['can_complete']
    r=produce(False,'--prefix','');assert r['language']['empty'] and r['language']['shortest_example'] is None and not r['prefix']['can_complete']
    r=produce({'const':'a'},'--prefix','"a"');assert r['prefix']['accepting'] and r['prefix']['shortest_completion']['bytes']==[]
    r=produce({'type':'object'},want='UNSUPPORTED');assert command(['verify',artifact,'--quiet'],3)['verification']=='NOT_APPLICABLE'
    produce({'type':'object','additionalProperties':False,'properties':{f'k{i}':{'type':'boolean'} for i in range(12)}},want='UNKNOWN')
    rows.append({'check':'infinite and finite fallback, empty language, exact/partial UTF-8, raw newline, empty suffix, unsupported and resource stop','status':'PASS'})

    for text in ['{"type":','null','{"type":{}}','{"enum":true}','{"minLength":true}','{"required":[1]}','{"const":NaN}','{"const":1,"const":2}']:
        schema.write_text(text);r=command([schema,'--quiet'],2);assert r['support']=='INVALID_INPUT',r
    for text in ['{"const":1.25}','{"const":"\\ud800"}']:
        schema.write_text(text);assert command([schema,'--quiet'],3)['support']=='UNSUPPORTED'
    schema.write_text('{"const":1e23}');r=command([schema,'--quiet']);assert r['language']['shortest_example']['utf8']==str(10**23)
    assert command([schema,'--prefix-hex','ZZ','--quiet'],2)['support']=='INVALID_INPUT'
    before=schema.read_bytes();assert command([schema,'-o',schema,'--quiet'],2)['support']=='INVALID_INPUT';assert schema.read_bytes()==before
    rows.append({'check':'invalid JSON/keyword shapes, duplicates, nonfinite/fractional numbers, surrogates, exact exponent parsing, input overwrite guard','status':'PASS'})

    produce({'type':'object','properties':{'a':{'enum':['x','y']}},'required':['a'],'additionalProperties':False},'--prefix','{"a":')
    original=json.loads(artifact.read_text());rejected=[]
    mutations={}
    def copy():return json.loads(json.dumps(original))
    bad=copy();bad['certificate']['states'][0]['distance']+=1;mutations['distance']=bad
    bad=copy();bad['certificate']['states'][0]['completion']=[0];mutations['completion']=bad
    bad=copy();bad['certificate']['states'][0]['edges']['255']=0;mutations['edge']=bad
    bad=copy();bad['certificate']['status']='EMPTY';mutations['false_empty']=bad
    bad=copy();bad['prefix']['can_complete']=False;mutations['query_claim']=bad
    bad=copy();bad['prefix']['trace'][-1]=0;mutations['prefix_trace']=bad
    bad=copy();bad['language']['shortest_example']['bytes']=[0];mutations['example_claim']=bad
    bad=copy();bad['input']['schema']['required']=[];mutations['schema']=bad
    bad=copy();bad['certificate']['states'][0]['distance']=True;mutations['boolean_distance']=bad
    for name,bad in mutations.items():
        artifact.write_text(json.dumps(bad));v=command(['verify',artifact,'--quiet'],1);assert v['verification']=='FAIL';rejected.append(name)
    artifact.write_text(json.dumps(mutations['edge']))
    assert command(['verify',artifact,'--quiet'],1,optimized=True)['verification']=='FAIL'
    artifact.write_text(json.dumps(original));schema.write_text('{"const":7}')
    assert command(['verify',artifact,'--schema',schema,'--quiet'],1)['verification']=='FAIL'
    rows.append({'check':'tampered evidence and mismatched external schema rejected, including optimized parent interpreter','mutations':rejected,'status':'PASS'})

    # A physically detached copy cannot resolve any previous study or producer source.
    detached=t/'detached';detached.mkdir();shutil.copy2(P/'schema-check',detached/'schema-check');shutil.copytree(P/'schema_check',detached/'schema_check',ignore=shutil.ignore_patterns('__pycache__'))
    for f in list((detached/'schema_check/_engine').rglob('generate.py'))+list((detached/'schema_check/_engine').rglob('nfa_builder.py')):f.unlink()
    artifact.write_text(json.dumps(original));elsewhere=t/'elsewhere';elsewhere.mkdir()
    r=subprocess.run([sys.executable,'-I','-S','-B',str(detached/'schema-check'),'verify',str(artifact),'--quiet'],capture_output=True,text=True,timeout=30,cwd=elsewhere)
    # -I removes a script's directory from sys.path, so the launcher explicitly adds its own root.
    assert r.returncode==0 and json.loads(r.stdout)['verification']=='PASS',r.stderr
    rows.append({'check':'detached verifier with every producer and NFA builder file removed','status':'PASS'})

now=resource.getrusage(resource.RUSAGE_CHILDREN)
result={'status':'PASS','checks':rows,'wall_seconds':time.monotonic()-start,'child_cpu_seconds':now.ru_utime+now.ru_stime-usage.ru_utime-usage.ru_stime}
(cache/'TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
