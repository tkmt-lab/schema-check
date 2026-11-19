import json,hashlib,importlib.util,sys
from pathlib import Path
from finite_semantics import syntax,guard,valid,canonical,Unsupported,Limit,CAP,parse_input

def previous(schema):
    p=Path(__file__).resolve().parent/'../next2';sys.path.insert(0,str(p))
    try:
        spec=importlib.util.spec_from_file_location('previous_generator',p/'generate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        return m.generate(schema)
    finally: sys.path.remove(str(p))

def generate(schema):
    try:
        syntax(schema);values=guard(schema)
        words=sorted({canonical(x) for x in values if valid(schema,x)})
        nodes=[{'edges':{},'accept':False}]
        for word in words:
            q=0
            for b in word:
                key=str(b)
                if key not in nodes[q]['edges']:
                    if len(nodes)>=CAP-1:raise Limit('byte state cap')
                    nodes[q]['edges'][key]=len(nodes);nodes.append({'edges':{},'accept':False})
                q=nodes[q]['edges'][key]
            nodes[q]['accept']=True
        sink=len(nodes);nodes.append({'edges':{},'accept':False})
        completion_budget=0
        for node in reversed(nodes):
            candidates=[(1+nodes[t]['distance'],[int(b)]+nodes[t]['completion']) for b,t in node['edges'].items() if nodes[t].get('distance')is not None]
            d,w=(0,[]) if node['accept'] else min(candidates,default=(None,None))
            completion_budget+=len(w) if w is not None else 0
            if completion_budget>2000000:raise Limit('completion evidence budget')
            node['distance'],node['completion']=d,w
        return {'mode':'finite-object-enum','status':'EMPTY' if nodes[0]['distance']is None else 'NONEMPTY','states':nodes,'sink':sink,'schema_sha256':hashlib.sha256(json.dumps(schema,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'finite_candidate_count':len(values),'accepted_value_count':len(words)}
    except Unsupported as e:
        old=previous(schema)
        if old['status']=='UNSUPPORTED':old['next3_reason']=str(e)
        return old
    except (Limit,MemoryError) as e:
        old=previous(schema)
        return old if old['status']in ['EMPTY','NONEMPTY'] else {'status':'UNKNOWN','reason':str(e)}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('schema',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try: result=generate(parse_input(a.schema.read_text()))
    except Unsupported as e:result={'status':'UNSUPPORTED','reason':str(e)}
    a.out.write_text(json.dumps(result,ensure_ascii=False)+'\n')
