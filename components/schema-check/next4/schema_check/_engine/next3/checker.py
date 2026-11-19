"""Separate finite-language verifier; no producer source access/import."""
import json,hashlib,sys,importlib.util
from pathlib import Path
from finite_semantics import syntax,guard,valid,canonical

def check(schema,c):
    if c.get('mode')!='finite-object-enum':
        p=Path(__file__).resolve().parent/'../next2';sys.path.insert(0,str(p))
        try:
            sp=importlib.util.spec_from_file_location('previous_checker',p/'checker.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
            return m.check(schema,c)
        finally: sys.path.remove(str(p))
    syntax(schema)
    assert c.get('status') in ['EMPTY','NONEMPTY']
    assert c['schema_sha256']==hashlib.sha256(json.dumps(schema,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    states=c['states'];sink=c['sink'];assert 0<=sink<len(states)<=100000
    assert states[sink]==dict(edges={},accept=False,distance=None,completion=None)
    for s in states:
        assert type(s['accept'])is bool
        assert all(str(int(b))==b and 0<=int(b)<256 and type(t)is int and 0<=t<len(states) for b,t in s['edges'].items())
        ds=[states[t]['distance'] for t in s['edges'].values() if states[t]['distance']is not None]
        expected=0 if s['accept'] else 1+min(ds) if ds else None
        assert s['distance']==expected
        w=s['completion']
        if expected is None:assert w is None
        else:
            assert type(expected)is int and len(w)==expected
            if expected:assert w==min([int(b)]+states[t]['completion'] for b,t in s['edges'].items() if states[t]['distance']==expected-1)
    # Reconstruct accepted words from the shared finite semantics; then language equivalence.
    words={canonical(x) for x in guard(schema) if valid(schema,x)}
    trie=[{}];accept=set()
    for w in words:
        q=0
        for b in w:
            if b not in trie[q]:trie[q][b]=len(trie);trie.append({})
            q=trie[q][b]
        accept.add(q)
    todo=[(0,0)];seen=set();queued={(0,0)}
    while todo:
        q,t=todo.pop()
        if (q,t)in seen:continue
        seen.add((q,t));assert states[q]['accept']==(t in accept)
        for b in range(256):
            pair=(states[q]['edges'].get(str(b),sink),trie[t].get(b,-1) if t>=0 else -1)
            if pair not in queued:
                queued.add(pair);assert len(queued)<=100000;todo.append(pair)
    assert {q for q,t in seen}==set(range(len(states)))
    assert (c['status']=='EMPTY')==(not words)==(states[0]['distance']is None)
    for q,s in enumerate(states):
        if s['completion']is not None:
            for b in s['completion']:q=states[q]['edges'].get(str(b),sink)
            assert states[q]['accept']
    return {'status':'PASS','states':len(states),'values':len(words),'shared_finite_semantics':True,'all_byte_language_equivalence':True,'distances_and_completions':True}

def prefix(c,raw):
    q=0
    for b in raw:q=c['states'][q]['edges'].get(str(b),c['sink'])
    n=c['states'][q];return {'state':q,'distance':n['distance'],'completion':n['completion'],'accepting':n['accept']}
