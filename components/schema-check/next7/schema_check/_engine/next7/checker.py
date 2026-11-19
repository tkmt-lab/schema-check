"""No producer imports. Independent equivalence traversal and distance checks."""
import sys,importlib.util
from pathlib import Path
from extended import syntax,guard,valid,canonical,CAP
from numeric import Model
from schema_check._shared import dumps,sha
def prefix(c,raw):
    q=0
    for b in raw:q=c['states'][q]['edges'].get(str(b),c['sink'])
    n=c['states'][q];return {'state':q,'distance':n['distance'],'completion':n['completion'],'accepting':n['accept']}
def check(schema,c):
    if not __debug__:raise RuntimeError('assertions must be enabled')
    if c.get('mode') not in ['finite-number-array','rational-numeric-features']:
        p=Path(__file__).resolve().parent/'../next3';sys.path.insert(0,str(p))
        try:
            sp=importlib.util.spec_from_file_location('old_checker',p/'checker.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m.check(schema,c)
        finally:sys.path.remove(str(p))
    syntax(schema);assert c['status'] in ['EMPTY','NONEMPTY'] and c['schema_sha256']==sha(dumps(schema).encode())
    states=c['states'];sink=c['sink'];assert type(sink)is int and 0<=sink<len(states)<=CAP
    assert states[sink]==dict(edges={},accept=False,distance=None,completion=None)
    budget=0
    for i,n in enumerate(states):
        assert set(n)=={'edges','accept','distance','completion'} and type(n['accept'])is bool
        assert all(type(b)is str and str(int(b))==b and 0<=int(b)<256 and type(t)is int and 0<=t<len(states) for b,t in n['edges'].items())
        ds=[states[t]['distance'] for t in n['edges'].values() if states[t]['distance']is not None]
        d=0 if n['accept'] else 1+min(ds) if ds else None
        assert n['distance']==d and (d is None or type(n['distance'])is int and 0<=d<len(states))
        if d is None:assert n['completion']is None
        else:
            w=n['completion'];assert type(w)is list and len(w)==d and all(type(b)is int and 0<=b<256 for b in w)
            if d:assert w==min([int(b)]+states[t]['completion'] for b,t in n['edges'].items() if states[t]['distance']==d-1)
            assert prefix({**c,'states':states},[])['state']==0
            q=i
            for b in w:q=states[q]['edges'].get(str(b),sink)
            assert states[q]['accept'];budget+=len(w)
        assert budget<=2000000
    if c['mode']=='finite-number-array':
        words={canonical(v) for v in guard(schema) if valid(schema,v)};trie=[{}];accept=set()
        for w in words:
            q=0
            for b in w:
                if b not in trie[q]:trie[q][b]=len(trie);trie.append({})
                q=trie[q][b]
            accept.add(q)
        start=0
        def transition(t,b):return trie[t].get(b,-1) if t>=0 else -1
        def accepting(t):return t in accept
    else:
        model=Model(schema);start=model.initial();transition=model.step;accepting=model.accept
    todo=[(0,start)];queued=set(todo);seen=set()
    while todo:
        q,t=todo.pop();seen.add(q);assert states[q]['accept']==accepting(t)
        for b in range(256):
            pair=(states[q]['edges'].get(str(b),sink),transition(t,b))
            if pair not in queued:queued.add(pair);assert len(queued)<=CAP;todo.append(pair)
    assert seen==set(range(len(states))) and (c['status']=='EMPTY')==(states[0]['distance']is None)
    return {'status':'PASS','states':len(states),'all_byte_equivalence_pairs':len(queued),'shared_reference_semantics':True,'distances_completions_checked':True}
