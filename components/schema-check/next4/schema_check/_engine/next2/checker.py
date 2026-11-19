"""No producer import/source read. Shared trusted semantics are reference.py."""
import json,hashlib,importlib.util
from pathlib import Path
from reference import Semantics,charboxes

def check(schema,c):
    if c['mode']=='finite-fallback':
        spec=importlib.util.spec_from_file_location('finite_checker',Path(__file__).resolve().parent/'../next1/checker.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        return m.check(schema,c)
    assert c['mode']=='symbolic-string' and c['status'] in ['EMPTY','NONEMPTY']
    assert c['schema_sha256']==hashlib.sha256(json.dumps(schema,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    # Check the annotated NFA locally; do not call the producer's NFA builder.
    sem=Semantics(schema);labels=[tuple(s) for s in c['meta']['character_labels']]
    assert labels and labels[0]==sem.initial() and len(labels)==len(set(labels))
    labelids={s:i for i,s in enumerate(labels)}
    desc=c['meta']['nfa_descriptions'];nfa=[{int(b):set(t) for b,t in row.items()} for row in c['nfa']];final={1}
    assert len(desc)==len(nfa)<=100000 and desc[:2]==[['initial'],['terminal']]
    assert desc[2:2+len(labels)]==[['boundary',i] for i in range(len(labels))]
    suffixids={}
    for i,d in enumerate(desc[2+len(labels):],2+len(labels)):
        assert d[0]=='suffix' and d[1] and 0<=d[2]<len(nfa)
        key=(tuple(tuple(p) for p in d[1]),d[2]);assert key not in suffixids;suffixids[key]=i
    def suffix(boxes,target):
        return target if not boxes else suffixids[(tuple(tuple(p) for p in boxes),target)]
    for i,d in enumerate(desc):
        expected={}
        def edge(lo,hi,target):
            assert 0<=lo<=hi<256
            for b in range(lo,hi+1): expected.setdefault(b,set()).add(target)
        if d[0]=='initial':
            assert i==0;edge(34,34,2)
        elif d[0]=='terminal': assert i==1
        elif d[0]=='boundary':
            st=labels[d[1]]
            if sem.accepts(st): edge(34,34,1)
            for lo,hi in sem.categories:
                target=2+labelids[sem.step(st,lo)]
                for box in charboxes(lo,hi): edge(*box[0],suffix(box[1:],target))
        else: edge(*d[1][0],suffix(d[1][1:],d[2]))
        assert nfa[i]==expected, ('NFA construction',i)
    nodes=c['states'];sink=c['sink'];sets=[frozenset(s) for s in c['subsets']]
    assert 0<=sink<len(nodes)<=100000 and len(nodes)==len(sets)==len(set(sets))
    assert sets[0]=={0} and sets[sink]==set() and nodes[sink]==dict(edges={},accept=False,distance=None,completion=None)
    for i,(ss,node) in enumerate(zip(sets,nodes)):
        assert all(0<=q<len(nfa) for q in ss)
        assert node['accept']==bool(ss & final)
        assert all(str(int(b))==b and 0<=int(b)<256 and type(t) is int and 0<=t<len(nodes) for b,t in node['edges'].items())
        for b in range(256):
            target=set()
            for q in ss: target.update(nfa[q].get(b,()))
            assert sets[node['edges'].get(str(b),sink)]==target
        ds=[nodes[t]['distance'] for t in node['edges'].values() if nodes[t]['distance'] is not None]
        expected=0 if node['accept'] else 1+min(ds) if ds else None
        assert node['distance']==expected
        w=node['completion']
        if expected is None: assert w is None
        else:
            assert type(expected) is int and expected>=0 and len(w)==expected
            if expected: assert w==min([int(b)]+nodes[t]['completion'] for b,t in node['edges'].items() if nodes[t]['distance']==expected-1)
            q=i
            for b in w: q=nodes[q]['edges'].get(str(b),sink)
            assert nodes[q]['accept']
    todo=[0];seen=set()
    while todo:
        q=todo.pop()
        if q in seen: continue
        seen.add(q);todo.extend(nodes[q]['edges'].values())
        if len(nodes[q]['edges'])<256: todo.append(sink)
    assert len(seen)==len(nodes) and (c['status']=='EMPTY')==(nodes[0]['distance'] is None)
    return {'status':'PASS','states':len(nodes),'shared_trusted_reference':True,'closure_distances_completions':True}

def prefix(c,raw):
    q=0
    for b in raw: q=c['states'][q]['edges'].get(str(b),c['sink'])
    s=c['states'][q]
    return {'state':q,'distance':s['distance'],'completion':s['completion'],'accepting':s['accept']}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('schema',type=Path);p.add_argument('certificate',type=Path);a=p.parse_args()
    print(json.dumps(check(json.loads(a.schema.read_text()),json.loads(a.certificate.read_text()))))
