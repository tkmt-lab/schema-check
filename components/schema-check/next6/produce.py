"""Sparse token lifting and original-byte-state boundary reachability."""
from collections import deque
from vocabulary import CAP,Limit,digest
def quotient(c):
    nodes=c['states'];labels=[int(n['accept']) for n in nodes]
    while True:
        classes={};new=[];dead=labels[c['sink']]
        for n in nodes:
            key=(n['accept'],tuple(sorted((int(b),labels[t]) for b,t in n['edges'].items() if labels[t]!=dead)))
            if key not in classes:classes[key]=len(classes)
            new.append(classes[key])
        if new==labels:break
        labels=new
    result=[None]*(max(labels)+1);dead=labels[c['sink']]
    for i,n in enumerate(nodes):
        if result[labels[i]] is None:result[labels[i]]={'accept':n['accept'],'edges':{b:labels[t] for b,t in n['edges'].items() if labels[t]!=dead}}
    return {'mapping':labels,'states':result,'start':labels[0],'sink':dead}

def matches(nodes,dead,source,trie,guard):
    groups={};todo=[(source,0)];visits=0
    while todo:
        guard(len(todo)+len(groups));q,t=todo.pop();visits+=1
        if trie[t]['ids']:groups.setdefault(q,[]).extend(trie[t]['ids'])
        for b,child in trie[t]['e'].items():
            target=nodes[q]['edges'].get(str(b),dead)
            if target!=dead:todo.append((target,child))
    return groups,visits

def generate(c,tries):
    q=quotient(c);nodes=q['states'];dead=q['sink'];N=len(nodes)
    base=len(c['states'])+4*N+sum(map(len,tries));peak=base;arcs=0;work=0
    def guard(extra):
        nonlocal peak
        peak=max(peak,base+arcs+extra)
        if peak>CAP:raise Limit('retained states/arcs/frontier exceed 500000')
    guard(0);graph=[]
    for phase in range(2):
        for i,n in enumerate(nodes):
            groups,v=matches(nodes,dead,i,tries[phase],guard) if i!=dead else ({},0);work+=v
            edges=[]
            for target,ids in sorted(groups.items()):
                ids.sort();edges.append({'target':N+target,'token_id':ids[0],'count':len(ids),'ids_sha256':digest(ids)})
            arcs+=len(edges);guard(0);graph.append({'accept':n['accept'],'edges':edges,'distance':None,'completion':None})
    reverse=[set() for _ in graph];todo=deque()
    for i,n in enumerate(graph):
        for e in n['edges']:reverse[e['target']].add(i)
        if n['accept']:n['distance']=0;n['completion']=[];todo.append(i)
    order=[]
    while todo:
        t=todo.popleft();order.append(t)
        for i in reverse[t]:
            if graph[i]['distance'] is None:graph[i]['distance']=graph[t]['distance']+1;todo.append(i)
    for i in order:
        d=graph[i]['distance']
        if d:graph[i]['completion']=min([e['token_id']]+graph[e['target']]['completion'] for e in graph[i]['edges'] if graph[e['target']]['distance']==d-1)
    # Enumerate actual original states at token boundaries, without retaining all arcs.
    original=c['states'];olddead=c['sink'];reachable=[];seen={};todo=deque()
    if original[0]['distance'] is not None:
        seen[0,0]=0;reachable.append({'phase':0,'state':0,'parent':None,'token':None});todo.append(0)
    while todo:
        i=todo.popleft();r=reachable[i];groups,v=matches(original,olddead,r['state'],tries[r['phase']],lambda extra:guard(extra+len(reachable)));work+=v
        for target,ids in sorted(groups.items()):
            if original[target]['distance'] is None:continue
            if (1,target) not in seen:
                seen[1,target]=len(reachable);todo.append(len(reachable));reachable.append({'phase':1,'state':target,'parent':i,'token':min(ids)})
        guard(len(reachable))
    deadrows=[i for i,r in enumerate(reachable) if graph[r['phase']*N+q['mapping'][r['state']]]['distance'] is None]
    return {'format':'schema-check-metaspace/v1','byte_sha256':digest(c),'quotient':q,'graph':graph,'reachable':reachable,'dead_reachable_indices':deadrows,
            'resources':{'retained_peak_states_arcs':peak,'cap':CAP,'lexical_pair_visits':work,'trie_states':sum(map(len,tries))}}
