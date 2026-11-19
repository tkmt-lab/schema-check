"""Finite word and rational-feature DFA producer, with preserved old fallback."""
import sys,importlib.util
from pathlib import Path
from collections import deque
from extended import syntax,guard,valid,canonical,Unsupported,Limit,CAP
from numeric import Model
from schema_check._shared import dumps,sha
def finish(nodes,sink,schema,mode):
    reverse=[set() for _ in nodes];todo=deque()
    for i,n in enumerate(nodes):
        n['distance']=0 if n['accept'] else None;n['completion']=[] if n['accept'] else None
        if n['accept']:todo.append(i)
        for target in n['edges'].values():reverse[target].add(i)
    order=[]
    while todo:
        t=todo.popleft();order.append(t)
        for i in reverse[t]:
            if nodes[i]['distance'] is None:nodes[i]['distance']=nodes[t]['distance']+1;todo.append(i)
    budget=0
    for i in order:
        n=nodes[i];d=n['distance']
        if d:n['completion']=min([int(b)]+nodes[t]['completion'] for b,t in n['edges'].items() if nodes[t]['distance']==d-1)
        budget+=d
        if budget>2000000:raise Limit('completion evidence budget')
    return {'mode':mode,'status':'EMPTY' if nodes[0]['distance']is None else 'NONEMPTY','states':nodes,'sink':sink,'schema_sha256':sha(dumps(schema).encode())}
def finite(schema,values):
    words=sorted({canonical(v) for v in values if valid(schema,v)});nodes=[{'edges':{},'accept':False}]
    for w in words:
        q=0
        for b in w:
            b=str(b)
            if b not in nodes[q]['edges']:
                if len(nodes)>=CAP-1:raise Limit('finite byte state cap')
                nodes[q]['edges'][b]=len(nodes);nodes.append({'edges':{},'accept':False})
            q=nodes[q]['edges'][b]
        nodes[q]['accept']=True
    sink=len(nodes);nodes.append({'edges':{},'accept':False})
    c=finish(nodes,sink,schema,'finite-number-array');c['candidate_count']=len(values);c['accepted_value_count']=len(words);return c
def numeric(schema):
    model=Model(schema);features=[model.initial()];indices={features[0]:0};nodes=[]
    for f in features:
        edges={}
        for b in [45,46]+list(range(48,58)):
            t=model.step(f,b)
            if t is None:continue
            if t not in indices:
                if len(features)>=CAP-1:raise Limit('numeric feature state cap')
                indices[t]=len(features);features.append(t)
            edges[str(b)]=indices[t]
        nodes.append({'edges':edges,'accept':model.accept(f)})
    sink=len(nodes);nodes.append({'edges':{},'accept':False});return finish(nodes,sink,schema,'rational-numeric-features')
def previous(schema):
    p=Path(__file__).resolve().parent/'../next3';sys.path.insert(0,str(p))
    try:
        sp=importlib.util.spec_from_file_location('old_generator',p/'generate.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m.generate(schema)
    finally:sys.path.remove(str(p))
def generate(schema):
    try:syntax(schema)
    except Unsupported as e:return {'status':'UNSUPPORTED','reason':str(e)}
    try:return finite(schema,guard(schema))
    except (Unsupported,Limit) as initial:
        try:return numeric(schema)
        except Limit as e:return {'status':'UNKNOWN','reason':str(e)}
        except Unsupported as e:
            if isinstance(initial,Limit):return {'status':'UNKNOWN','reason':str(initial)}
            try:return previous(schema)
            except (TypeError,Unsupported) as e:return {'status':'UNSUPPORTED','reason':str(e)}
    except (Limit,MemoryError) as e:return {'status':'UNKNOWN','reason':str(e)}
