#!/usr/bin/env python3
"""Offline replay of every bundled byte/token certificate, without producer imports."""
import argparse,json,hashlib,pathlib,sys,time,shutil,tempfile,os
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P/'tools'))
from limits import run,RSS_STOP
C=P/'components/schema-check';logs=[];started=time.monotonic()

def require(condition,message):
 if not condition:raise RuntimeError(message)

def manifest():
 m=json.loads((P/'MANIFEST.json').read_text());seen=set()
 for row in m['files']:
  path=pathlib.PurePosixPath(row['path']);require(not path.is_absolute() and '..'not in path.parts,'unsafe manifest path')
  f=P/path;require(not f.is_symlink(),'symlink in payload');raw=f.read_bytes()
  require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'manifest mismatch: '+str(path));seen.add(str(path))
 actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file() and not any(k in ['.git','.cache','__pycache__','.comparison-env'] for k in p.relative_to(P).parts)}-{'MANIFEST.json'}
 require(actual==seen,'unlisted or missing payload files: '+str(actual^seen));return len(seen)

def command(label,argv,code=0,timeout=65):
 r=run(argv,timeout=timeout);logs.append(dict(label=label,**r))
 require(not r['resource_stop'],label+': '+str(r['resource_stop']));require(r['returncode']==code,label+': '+r['stderr'][-1000:]+r['stdout'][-1000:])
 try:return json.loads(r['stdout'])
 except ValueError:raise RuntimeError(label+': invalid JSON output')

def main():
 a=argparse.ArgumentParser();a.add_argument('--output',default='.cache/verification.json');args=a.parse_args()
 require(__debug__,'assertions must be enabled; do not use python -O')
 file_count=manifest();required=['README.md','claims.json','LICENSE','Apache-2.0.txt','CC-BY-4.0.txt','CITATION.cff','.zenodo.json','THIRD-PARTY-NOTICES.md','PROVENANCE.json']
 require(all((P/f).is_file() for f in required),'missing release metadata')
 claims=json.loads((P/'claims.json').read_text());require(claims['release_status']=='RELEASE','unexpected release state')
 require(not any(k in json.loads((P/'.zenodo.json').read_text()) for k in ['doi','prereserve_doi']),'invented DOI metadata')
 annotation=command('observation-map',[sys.executable,'-S','-B',P/'comparison/classify_observations.py','--check'])
 require(annotation['status']=='PASS' and annotation['records']==369,'stale observation provenance')
 # Check all saved v2 artifacts, including status-only unsupported/unknown records.
 cases=json.loads((C/'next7/CASES.json').read_text());supported=0;not_applicable=0
 for i,c in enumerate(cases):
  saved=json.loads((C/'next7/all'/f'{i:03}.json').read_text());support=saved['bundle']['support']
  v=command(f'byte-v2/{i:03}',[sys.executable,'-S','-B',C/'next7/worker.py','verify',str(i),'30'],timeout=32)
  if support=='SUPPORTED':require(v['verification']=='PASS','byte check failed');supported+=1
  else:require(v['status']==support and v.get('not_applicable')is True,'status-only artifact was treated as proof');not_applicable+=1
  if i%40==0:print(f'byte records {i+1}/{len(cases)}',flush=True)
 require(len(cases)==214 and supported==123 and not_applicable==91,'unexpected frozen byte corpus')
 token_counts={}
 for key in ['gpt2','t5-small','albert-base-v2']:
  for i in range(83):
   v=command(f'{key}/{i:03}',[sys.executable,'-S','-B',P/'tools/check_corpus.py',key,str(i)],timeout=62);require(v['status']=='PASS','token proof failed')
   if i%20==0:print(f'{key} records {i+1}/83',flush=True)
  token_counts[key]=83
 cache=P/'.cache';cache.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(dir=cache,prefix='examples-') as t:
  t=pathlib.Path(t);obj=t/'object.json';num=t/'number.json';byte=t/'legacy.json';token=t/'token.json'
  for name,prefix,out in [('object',['--prefix','{"modifier":'],obj),('tenths',['--prefix','0.'],num),('empty-number',[],t/'empty.json'),('emoji',['--prefix-hex','22f09f'],t/'emoji.json')]:
   # Production writes a file and no stdout, so invoke with stdout then save exact JSON bytes.
   result=command(name+'/produce',[sys.executable,'-S','-B',P/'schema-check',P/'examples'/f'{name}.json',*prefix,'--quiet'])
   out.write_text(json.dumps(result,ensure_ascii=False)+'\n')
   v=command(name+'/verify',[sys.executable,'-S','-B',P/'schema-check','verify',out,'--schema',P/'examples'/f'{name}.json','--quiet']);require(v['verification']=='PASS','public verification failed')
  require(json.loads(num.read_text())['prefix']['shortest_completion']['utf8']=='1','exact decimal example differs')
  legacy=command('v1/produce',[sys.executable,'-S','-B',P/'schema-check-v1',P/'examples/object.json','--prefix','{"modifier":','--quiet']);byte.write_text(json.dumps(legacy)+'\n')
  tok=command('gpt2/public-produce',[sys.executable,'-S','-B',P/'token-check',byte,'--quiet']);token.write_text(json.dumps(tok)+'\n')
  require(command('gpt2/public-verify',[sys.executable,'-S','-B',P/'token-check','verify',token,'--schema',P/'examples/object.json','--quiet'])['verification']=='PASS','public token verifier failed')
  rejected=command('v2-not-v1',[sys.executable,'-S','-B',P/'token-check',obj,'--quiet'],code=1);require(rejected.get('verification')=='ERROR','v2 unexpectedly accepted by v1 token entry')
  bad=json.loads(obj.read_text());bad['certificate']['states'][0]['distance']+=1;mutation=t/'bad.json';mutation.write_text(json.dumps(bad)+'\n')
  require(command('mutation',[sys.executable,'-S','-B',P/'schema-check','verify',mutation,'--quiet'],code=1)['verification']=='FAIL','corrupted evidence accepted')
  detached=t/'detached';detached.mkdir();shutil.copyfile(C/'next7/schema-check',detached/'schema-check');shutil.copytree(C/'next7/schema_check',detached/'schema_check')
  removed=[]
  for f in (detached/'schema_check/_engine').rglob('*.py'):
   if f.name in ['generate.py','nfa_builder.py']:removed.append(f.relative_to(detached).as_posix());f.unlink()
  require(command('producer-removed',[sys.executable,'-I','-S','-B',detached/'schema-check','verify',obj,'--schema',P/'examples/object.json','--quiet'])['verification']=='PASS','detached verifier failed')
 total_cpu=sum(r['cpu_seconds'] for r in logs);require(total_cpu<3600,'one-hour verification CPU budget exceeded')
 result=dict(status='PASS',manifest_files=file_count,classified_tool_schema_records=369,byte_v2_records=214,byte_v2_certificates=supported,status_only_records=not_applicable,byte_v1_certificates_rechecked_per_vocabulary=83,token_certificates=token_counts,public_examples=4,token_public_roundtrip=True,v2_rejected_by_v1_token_entry=True,mutation_rejected=True,producer_files_removed=removed,producer_removed_verification='PASS',comparisons='saved observations hashed; external backends not rerun',peak_tree_rss_bytes=max(r['peak_tree_rss_bytes'] for r in logs),rss_precaution_bytes=RSS_STOP,user_memory_ceiling_bytes=2*1024**3,memory_limit_mode='polled aggregate RSS; Linux also per-process AS; not a hard macOS address-space guarantee',worker_cpu_seconds_with_monitor=total_cpu,wall_seconds=time.monotonic()-started,commands=logs)
 out=pathlib.Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='commands'},indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps(dict(status='FAIL',error=f'{type(e).__name__}: {e}')),file=sys.stderr);raise SystemExit(1)
