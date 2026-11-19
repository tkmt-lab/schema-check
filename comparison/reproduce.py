"""Frozen-input replay in a disposable copy; explicit, provenance-bound version updates."""
import argparse,pathlib,shutil,sys,json,hashlib
P=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from limits import run
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
a=argparse.ArgumentParser();a.add_argument('kind',choices=['byte-v1','byte-v2','gpt2','metaspace','reports']);a.add_argument('--python',default=sys.executable);a.add_argument('--output',type=pathlib.Path,required=True);a.add_argument('--versions-file',type=pathlib.Path,help='explicit seven-package snapshot; keep the published reference pins unchanged');a.add_argument('--baseline',type=pathlib.Path,help='byte-v1 output directory produced with the same explicit version snapshot');x=a.parse_args()
dest=x.output.resolve()
if dest.is_relative_to(P) and dest.relative_to(P).parts[:1]!=('.cache',):a.error('in-packet output must be under .cache to prevent recursive copies')
if x.output.exists():a.error('output must be a new directory; preserve earlier observations')
if x.versions_file and x.kind in ['gpt2','metaspace']:a.error('these fixed native-token probes contain pinned adapter assertions; version-update mode supports byte-v1, byte-v2 and reports')
if x.versions_file and x.kind=='byte-v2' and not x.baseline:a.error('byte-v2 version update requires --baseline from a same-version byte-v1 run; never reuse the old 83 observations')
if x.baseline and x.kind!='byte-v2':a.error('--baseline is only for byte-v2')
cmd=[x.python,'-B',P/'comparison/check_environment.py']+(['--versions-file',x.versions_file] if x.versions_file else [])
r=run(cmd,timeout=10)
if r['returncode'] or r['resource_stop']:print(r['stdout'],r['stderr']);raise SystemExit(1)
meta=json.loads(r['stdout']);baseline=None
if x.baseline:
 baseline_env=json.loads((x.baseline/'ENVIRONMENT.json').read_text())
 if baseline_env['kind']!='byte-v1' or baseline_env['installed_versions']!=meta['installed']:a.error('baseline environment does not match the selected package versions')
 baseline=x.baseline/'packet/components/schema-check/next4/comparison/RESULTS.json';rows=json.loads(baseline.read_text())
 if len(rows)!=134 or any('worker_error' in r or r.get('returncode')!=0 for r in rows):a.error('baseline must contain all 134 successful worker records')
x.output.mkdir(parents=True);bundle=x.output/'packet';shutil.copytree(P,bundle,ignore=shutil.ignore_patterns('.git','.cache','.comparison-env','__pycache__'));C=bundle/'components/schema-check'
inputs={str(p.relative_to(P)):sha(p) for p in [P/'components/schema-check/next4/comparison/CASES.json',P/'components/schema-check/next7/CASES.json']}
metadata=dict(kind=x.kind,expected_versions=meta['expected'],installed_versions=meta['installed'],input_hashes=inputs,versions_file_sha256=sha(x.versions_file) if x.versions_file else None,baseline_sha256=sha(baseline) if baseline else None,scope='new experiment copy, not the sealed packet; old observations remain archived',preflight=r)
(x.output/'ENVIRONMENT.json').write_text(json.dumps(metadata,indent=2)+'\n')
if baseline:shutil.copyfile(baseline,C/'next3/RESULTS.json')
if x.kind=='byte-v1':commands=[[C/'next4/comparison/experiment.py'],[C/'next4/comparison/analyze.py']]
elif x.kind=='byte-v2':commands=[[C/'next7/run.py'],[C/'next7/analyze.py']]
elif x.kind=='gpt2':commands=[[C/'next5/native_smoke.py']]
elif x.kind=='reports':commands=[[bundle/'comparison/reports/xgrammar_repro.py'],[bundle/'comparison/reports/outlines_repro.py']]
else:commands=[[C/'next6/native_metadata.py']]+[[C/'next6/native_probe.py',key,str(i)] for key in ['t5-small','albert-base-v2'] for i in [0,34,73,74]]+[[C/'next6/native_probe.py',key,'34','--simple-object'] for key in ['t5-small','albert-base-v2']]
records=[]
for i,cmd in enumerate(commands):
 r=run([x.python,'-B',*cmd],timeout=7205 if x.kind.startswith('byte') else 62);records.append(r)
 (x.output/'RUN.json').write_text(json.dumps(records,indent=2)+'\n')
 if r['resource_stop'] or r['returncode']:raise SystemExit(1)
 print('finished',i+1,len(commands),flush=True)
if baseline:
 for f in (C/'next7/native').glob('*.json'):
  row=json.loads(f.read_text())
  if 'reused_input_commit' in row:
   row['historical_runner_baseline_label']=dict(input_commit=row.pop('reused_input_commit'),path=row.pop('reused_path'))
   row['baseline_used']=dict(sha256=metadata['baseline_sha256'],versions=meta['installed'],scope='same-version byte-v1 replay supplied to this wrapper')
   f.write_text(json.dumps(row,ensure_ascii=False)+'\n')
(x.output/'COMPLETE.json').write_text(json.dumps(dict(status='PASS',kind=x.kind,commands_completed=len(records),baseline_sha256=metadata['baseline_sha256'],metadata='ENVIRONMENT.json'),indent=2)+'\n')
