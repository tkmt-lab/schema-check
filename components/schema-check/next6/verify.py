"""Separate checker: direct all-token lifting, byte-edge/prefix closure, Bellman checks."""
from vocabulary import digest,CAP
def check(c,p,phases):
    if not __debug__:raise RuntimeError('assertions must be enabled')
    assert p['format']=='schema-check-metaspace/v1' and p['byte_sha256']==digest(c)
    old=c['states'];od=c['sink'];q=p['quotient'];m=q['mapping'];ns=q['states'];d=q['sink'];N=len(ns);g=p['graph']
    assert len(m)==len(old) and set(m)==set(range(N)) and m[0]==q['start'] and m[od]==d
    assert len(g)==2*N and not ns[d]['accept'] and not ns[d]['edges']
    assert all(type(t) is int and 0<=t<N for t in m)
    for i,n in enumerate(old):
        n2=ns[m[i]];assert n['accept']==n2['accept']
        for b in n['edges'].keys()|n2['edges'].keys():assert m[n['edges'].get(b,od)]==n2['edges'].get(b,d)
    steps=0
    for index,node in enumerate(g):
        phase,start=divmod(index,N);groups={}
        if start!=d:
            for token,raw in sorted(phases[phase].items()):
                t=start
                for b in raw:
                    t=ns[t]['edges'].get(str(b),d);steps+=1
                    if t==d:break
                if t!=d:groups.setdefault(N+t,[]).append(token)
        expected=[{'target':t,'token_id':ids[0],'count':len(ids),'ids_sha256':digest(ids)} for t,ids in sorted(groups.items())]
        assert node['edges']==expected and type(node['accept']) is bool and node['accept']==ns[start]['accept']
        assert all(type(e[k]) is int for e in node['edges'] for k in ['target','token_id','count'])
        dist=node['distance'];assert dist is None or type(dist) is int and 0<=dist<len(g)
        child=[g[e['target']]['distance'] for e in node['edges'] if g[e['target']]['distance'] is not None]
        assert dist==(0 if node['accept'] else 1+min(child) if child else None)
        completion=node['completion']
        if dist is None:assert completion is None
        else:
            assert type(completion) is list and all(type(i) is int and i in phases[0] for i in completion) and len(completion)==dist
            if dist:assert completion==min([e['token_id']]+g[e['target']]['completion'] for e in node['edges'] if g[e['target']]['distance']==dist-1)
            t=start;ph=phase
            for token in completion:
                for b in phases[ph][token]:t=ns[t]['edges'].get(str(b),d)
                ph=1
            assert ns[t]['accept']
    rows=p['reachable'];pairs={(r['phase'],r['state']) for r in rows};assert len(pairs)==len(rows)
    if old[0]['distance'] is None:assert not rows
    else:assert rows[0]=={'phase':0,'state':0,'parent':None,'token':None}
    # Witnesses prove inclusion; closure below proves exhaustiveness.
    for i,r in enumerate(rows):
        assert type(r['phase']) is type(r['state']) is int and r['phase'] in [0,1] and old[r['state']]['distance'] is not None
        if i:
            assert type(r['parent']) is type(r['token']) is int and 0<=r['parent']<i and r['token'] in phases[0]
            previous=rows[r['parent']];t=previous['state']
            for b in phases[previous['phase']][r['token']]:t=old[t]['edges'].get(str(b),od)
            assert r['phase']==1 and t==r['state']
    prefix_sets=[];terminals=[]
    for pieces in phases:
        words=set(pieces.values());terminals.append(words);prefix_sets.append({b[:i] for b in words for i in range(len(b)+1)})
    closure_steps=0
    for r in rows:
        phase=r['phase'];todo=[(r['state'],b'')]
        while todo:
            t,word=todo.pop();closure_steps+=1
            if word in terminals[phase] and old[t]['distance'] is not None:assert (1,t) in pairs
            for b,target in old[t]['edges'].items():
                nxt=word+bytes([int(b)])
                if target!=od and nxt in prefix_sets[phase]:todo.append((target,nxt))
    dead=[i for i,r in enumerate(rows) if g[r['phase']*N+m[r['state']]]['distance'] is None]
    assert dead==p['dead_reachable_indices']
    assert p['resources']['retained_peak_states_arcs']<=p['resources']['cap']==CAP
    return {'status':'PASS','direct_token_byte_steps':steps,'boundary_closure_steps':closure_steps,'reachable_states':len(rows),'byte_live_token_dead_states':len(dead)}
