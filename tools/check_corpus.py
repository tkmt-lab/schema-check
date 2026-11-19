"""Replay one frozen token certificate, guarded even when invoked on its own."""
from pathlib import Path
import sys,json,argparse
P=Path(__file__).resolve().parents[1];C=P/'components/schema-check'
sys.path.insert(0,str(P/'tools'))
from limits import run
a=argparse.ArgumentParser();a.add_argument('vocabulary',choices=['gpt2','t5-small','albert-base-v2']);a.add_argument('index',type=int);x=a.parse_args()
if not 0<=x.index<83:a.error('index must be 0..82')
if x.vocabulary=='gpt2':target=C/'next5';args=['verify',str(x.index),str(target/'all'/f'{x.index:03}.json'),'60']
else:target=C/'next6';args=['verify',x.vocabulary,str(x.index),str(target/x.vocabulary/'all'/f'{x.index:03}.json'),'60']
r=run([sys.executable,'-S','-B',target/'worker.py',*args],timeout=61)
if r['resource_stop'] or r['returncode']<0:
 print(json.dumps(dict(status='UNKNOWN',explanation=r['resource_stop'] or f"worker signal {r['returncode']}")));raise SystemExit(3)
sys.stdout.write(r['stdout']);sys.stderr.write(r['stderr']);raise SystemExit(r['returncode'])
