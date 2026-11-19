"""Separate entry point: no generator import/source access.
Reconstruct finite guard and use Python fullmatch for the declared regex subset.
"""
import itertools,json,re,hashlib
from collections import deque

def encoded(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def eq(a,b): return (type(a) is type(b) and a==b) if isinstance(a,bool) or isinstance(b,bool) else a==b

def valid(s,x):
    if isinstance(s,bool): return s
    typ=s.get('type')
    if typ and not {'string':isinstance(x,str),'boolean':isinstance(x,bool),'null':x is None}[typ]: return False
    if 'const' in s and not eq(s['const'],x): return False
    if 'enum' in s and not any(eq(v,x) for v in s['enum']): return False
    if isinstance(x,str):
        if not s.get('minLength',0)<=len(x)<=s.get('maxLength',float('inf')): return False
        if 'pattern' in s and re.fullmatch(s['pattern'][1:-1],x) is None: return False
    for op in ['allOf','anyOf','oneOf']:
        if op in s:
            bits=[valid(t,x) for t in s[op]]
            if op=='allOf' and not all(bits): return False
            if op=='anyOf' and not any(bits): return False
            if op=='oneOf' and bits.count(True)!=1: return False
    return not ('not' in s and valid(s['not'],x))

def guard(s):
    if s is False: return []
    if s is True: raise ValueError('unbounded')
    if s.get('not',False) is True or s.get('not',False)=={}: return []
    if 'oneOf' in s and all(isinstance(x,bool) for x in s['oneOf']) and s['oneOf'].count(True)!=1: return []
    if 'const' in s: return [s['const']]
    if 'enum' in s: return s['enum']
    if s.get('type')=='null': return [None]
    if s.get('type')=='boolean': return [True,False]
    if s.get('type')=='string':
        if s.get('maxLength')==0: return ['']
        p=s.get('pattern','')
        if re.fullmatch(r'\^[A-Za-z][*+?]\$',p): p='^['+p[1]+']'+p[2:]
        if p.startswith('^['):
            close=p.index(']');letters=sorted(set(p[2:close]));q=p[close+1:-1]
            upper=1 if q=='?' else None
            if q.startswith('{'): upper=int(q[1:-1].split(',')[-1])
            upper=min(upper if upper is not None else 10**9,s.get('maxLength',10**9))
            if upper>1000 or sum(len(letters)**n for n in range(upper+1))>100000: raise ValueError('cap')
            return [''.join(t) for n in range(upper+1) for t in itertools.product(letters,repeat=n)]
        if p: return [p[1:-1]]
    for t in s.get('allOf',[]):
        try: return guard(t)
        except ValueError: pass
    for key in ['anyOf','oneOf']:
        if key in s: return sum((guard(t) for t in s[key]),[])
    raise ValueError('unbounded')

def check(schema,cert):
    def syntax(s,depth=0):
        assert depth<=20
        if type(s) is bool: return
        assert isinstance(s,dict) and not (set(s)-{'type','enum','const','pattern','minLength','maxLength','allOf','anyOf','oneOf','not','$schema','description','title'})
        assert s.get('$schema','https://json-schema.org/draft/2020-12/schema')=='https://json-schema.org/draft/2020-12/schema'
        assert 'type' not in s or s['type'] in ['string','boolean','null']
        for k in ['minLength','maxLength']:
            assert k not in s or (type(s[k]) is int and s[k]>=0)
        for v in s.get('enum',[])+([s['const']] if 'const' in s else []):
            assert v is None or type(v) in [str,bool,int]
            assert type(v) is not int or abs(v)<=2**53
            encoded(v)
        if 'pattern' in s:
            p=s['pattern']
            assert re.fullmatch(r'\^(?:[^\[\]\\.*+?{}()|^$]+|[A-Za-z][*+?]|\[[^\]\\^\-]+\](?:[*+?]|\{\d+(?:,\d+)?\}))\$',p)
        for k in ['allOf','anyOf','oneOf']:
            for t in s.get(k,[]): syntax(t,depth+1)
        if 'not' in s: syntax(s['not'],depth+1)
    syntax(schema)
    assert cert["schema_sha256"]==hashlib.sha256(encoded(schema)).hexdigest()
    assert cert['status'] in ['NONEMPTY','EMPTY']
    nodes=cert['states'];sink=cert['sink'];assert 0<=sink<len(nodes)<=100000
    for s in nodes:
        assert type(s['accept']) is bool
        assert all(str(int(b))==b and 0<=int(b)<256 and type(t) is int and 0<=t<len(nodes) for b,t in s['edges'].items())
    assert nodes[sink]==dict(edges={},accept=False,distance=None,completion=None)
    for i,s in enumerate(nodes):
        children=[nodes[t]['distance'] for t in s['edges'].values() if nodes[t]['distance'] is not None]
        expected=0 if s['accept'] else (1+min(children) if children else None)
        assert s['distance']==expected,(i,'Bellman')
        w=s['completion']
        if expected is None: assert w is None
        else:
            assert len(w)==expected
            if expected:
                choices=[([int(b)]+nodes[t]['completion']) for b,t in s['edges'].items() if nodes[t]['distance']==expected-1]
                assert w==min(choices)
            q=i
            for b in w: q=nodes[q]['edges'].get(str(b),sink)
            assert nodes[q]['accept']
    # Independent expected trie, then product equivalence over all 256 byte symbols.
    truth={encoded(v) for v in guard(schema) if valid(schema,v)}
    trie=[{}];final=set()
    for word in truth:
        q=0
        for b in word:
            if b not in trie[q]: trie[q][b]=len(trie);trie.append({})
            q=trie[q][b]
        final.add(q)
    todo=[(0,0)];seen=set();queued={(0,0)}
    while todo:
        q,t=todo.pop()
        if (q,t) in seen: continue
        seen.add((q,t));assert nodes[q]['accept']==(t in final)
        for b in range(256):
            pair=(nodes[q]['edges'].get(str(b),sink),trie[t].get(b,-1) if t>=0 else -1)
            if pair not in queued:
                queued.add(pair);assert len(queued)<=100000;todo.append(pair)
    assert {q for q,_ in seen}==set(range(len(nodes))), 'unreachable states'
    assert (cert['status']=='EMPTY')==(not truth)==(nodes[0]['distance'] is None)
    return {'status':'PASS','states':len(nodes),'values':len(truth),'all_byte_language_equivalence':True,'distances_and_completions':True}

if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('schema',type=Path);p.add_argument('certificate',type=Path)
    a=p.parse_args();print(json.dumps(check(json.loads(a.schema.read_text()),json.loads(a.certificate.read_text()))))
