import json,hashlib,importlib.util
from pathlib import Path
from collections import deque
from reference import Unsupported,Limit,CAP
from nfa_builder import make_nfa

def canonical(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def generate(schema):
    try:
        try: nfa,final,meta=make_nfa(schema)
        except Unsupported:
            # Preserve next1 finite cases without weakening failed infinite input.
            path=Path(__file__).resolve().parent/'../next1/generate.py'
            spec=importlib.util.spec_from_file_location('finite_generator',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            out=m.generate(schema);out['mode']='finite-fallback';return out
        subsets=[frozenset([0])];ids={subsets[0]:0};nodes=[]
        for ss in subsets:
            row={};moves={}
            for q in ss:
                for b,targets in nfa[q].items(): moves.setdefault(b,set()).update(targets)
            for b,t in sorted(moves.items()):
                tt=frozenset(t)
                if tt not in ids:
                    if len(subsets)>=CAP: raise Limit('DFA state cap')
                    ids[tt]=len(subsets);subsets.append(tt)
                row[str(b)]=ids[tt]
            nodes.append({'edges':row,'accept':bool(final & ss),'distance':None,'completion':None})
        sink=len(nodes)
        if sink>=CAP: raise Limit('DFA cap including sink')
        nodes.append({'edges':{},'accept':False,'distance':None,'completion':None});subsets.append(frozenset())
        reverse=[set() for _ in nodes];todo=deque()
        for q,node in enumerate(nodes):
            for t in node['edges'].values(): reverse[t].add(q)
            if node['accept']: node['distance']=0;node['completion']=[];todo.append(q)
        order=[]
        while todo:
            q=todo.popleft();order.append(q)
            for t in reverse[q]:
                if nodes[t]['distance'] is None: nodes[t]['distance']=nodes[q]['distance']+1;todo.append(t)
        completion_budget=0
        for q in order:
            d=nodes[q]['distance']
            if d:
                nodes[q]['completion']=min([int(b)]+nodes[t]['completion'] for b,t in nodes[q]['edges'].items() if nodes[t]['distance']==d-1)
                completion_budget+=d
                if completion_budget>2000000:raise Limit('completion evidence budget')
        return {'status':'EMPTY' if nodes[0]['distance'] is None else 'NONEMPTY','mode':'symbolic-string','schema_sha256':hashlib.sha256(canonical(schema)).hexdigest(),'sink':sink,'states':nodes,'subsets':[sorted(s) for s in subsets],'meta':meta,'nfa':[{str(b):sorted(t) for b,t in row.items()} for row in nfa]}
    except (Limit,MemoryError) as e: return {'status':'UNKNOWN','reason':str(e)}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('schema',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    a.out.write_text(json.dumps(generate(json.loads(a.schema.read_text())),ensure_ascii=False)+'\n')
