"""Scientific certificate corruption checks."""
import json,copy,subprocess,sys,time,resource
from pathlib import Path
P=Path(__file__).resolve().parent;start=time.process_time();path=P/'t5-small/all/073.json';base=json.loads(path.read_text());proof=base['proof'];root=proof['quotient']['start']
from vocabulary import load,trie,Limit
from produce import generate
import produce,gzip
first,later,_,_,_=load('t5-small');corpus=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()))
def change_distance(x):x['proof']['graph'][root]['distance']=1
def change_group(x):next(n for n in x['proof']['graph'] if n['edges'])['edges'][0]['count']+=1
def change_quotient(x):x['proof']['quotient']['mapping'][0]=x['proof']['quotient']['sink']
def change_closure(x):x['proof']['reachable'].pop();x['proof']['dead_reachable_indices'].pop()
def change_parent(x):x['proof']['reachable'][2]['token']=next(i for i,b in later.items() if b==b'a')
def change_dead_set(x):x['proof']['dead_reachable_indices']=[]
def change_bool(x):x['proof']['graph'][root]['distance']=True
def change_completion(x):x['proof']['graph'][root]['completion']=[]
out=[];folder=P/'mutation-controls';folder.mkdir(exist_ok=True)
for mutate in [change_distance,change_group,change_quotient,change_closure,change_parent,change_dead_set,change_bool,change_completion]:
    x=copy.deepcopy(base);mutate(x);f=folder/(mutate.__name__+'.json');f.write_text(json.dumps(x,separators=(',',':'))+'\n')
    proc=subprocess.run([sys.executable,'-B',str(P/'worker.py'),'verify','t5-small','73',str(f),'10'],capture_output=True,text=True,timeout=12)
    assert proc.returncode!=0 and 'AssertionError' in proc.stderr,(mutate.__name__,proc.stderr)
    out.append({'mutation':mutate.__name__,'rejected':True,'returncode':proc.returncode,'exception':'AssertionError'})
oldcap=produce.CAP;produce.CAP=2
try:
    generate(corpus[73]['byte_certificate'],[trie(first),trie(later)]);raise AssertionError('low cap not enforced')
except Limit:pass
finally:produce.CAP=oldcap
print(json.dumps({'status':'PASS','mutation_rejections':out,'low_cap_returns_Limit':True,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
