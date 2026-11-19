"""Token-boundary inverse image of a byte DFA; producer implementation."""
from collections import deque
from vocabulary import CAP,Limit,digest,bytes_word

def quotient(c):
    nodes=c['states'];sink=c['sink'];labels=[int(n['accept']) for n in nodes];iterations=0
    while True:
        classes={};new=[];dead=labels[sink]
        for n in nodes:
            key=(n['accept'],tuple(sorted((int(b),labels[t]) for b,t in n['edges'].items() if labels[t]!=dead)))
            if key not in classes:classes[key]=len(classes)
            new.append(classes[key])
        iterations+=1
        if new==labels:break
        labels=new
    result=[None]*(max(labels)+1);dead=labels[sink]
    for i,n in enumerate(nodes):
        if result[labels[i]] is None:result[labels[i]]={'accept':n['accept'],'edges':{b:labels[t] for b,t in n['edges'].items() if labels[t]!=dead}}
    return {'mapping':labels,'states':result,'start':labels[0],'sink':dead,'refinement_rounds':iterations}

def generate(c,pieces,eos,trie,state_cap=CAP):
    q=quotient(c);nodes=q['states'];dead=q['sink'];base=len(c['states'])+2*len(nodes)+len(trie)
    if base>state_cap:raise Limit('byte + quotient + vocabulary state cap')
    graph=[];arc_count=0;visits=0;peak=base
    for source,node in enumerate(nodes):
        groups={};todo=[] if source==dead else [(source,0)]
        while todo:
            peak=max(peak,base+len(todo)+arc_count)
            if peak>state_cap:raise Limit('token construction frontier/arc state cap')
            state,t=todo.pop();visits+=1;token=trie[t]['token']
            if token is not None:groups.setdefault(state,[]).append(token)
            edges=nodes[state]['edges'];children=trie[t]['edges']
            for b,target in children.items():
                nxt=edges.get(str(b),dead)
                if nxt!=dead:todo.append((nxt,target))
        edges=[]
        for target,ids in sorted(groups.items()):
            ids.sort();edges.append({'target':target,'token_id':ids[0],'count':len(ids),'ids_sha256':digest(ids)})
        arc_count+=len(edges);peak=max(peak,base+arc_count)
        if peak>state_cap:raise Limit('retained token arc state cap')
        graph.append({'accept':node['accept'],'edges':edges,'distance':None,'completion':None})
    reverse=[set() for _ in graph];todo=deque()
    for i,n in enumerate(graph):
        for e in n['edges']:reverse[e['target']].add(i)
        if n['accept']:n['distance']=0;n['completion']=[];todo.append(i)
    order=[]
    while todo:
        t=todo.popleft();order.append(t)
        for i in reverse[t]:
            if graph[i]['distance'] is None:graph[i]['distance']=graph[t]['distance']+1;todo.append(i)
    budget=0
    for i in order:
        d=graph[i]['distance']
        if d:
            graph[i]['completion']=min([e['token_id']]+graph[e['target']]['completion'] for e in graph[i]['edges'] if graph[e['target']]['distance']==d-1)
            budget+=d
            if budget>2_000_000:raise Limit('token completion evidence budget')
    return {'format':'schema-check-token/v1','byte_certificate_sha256':digest(c),'quotient':q,'token_states':graph,
            'eos_token_id':eos,'distance_convention':'ordinary tokens to an accepting state; explicit EOS adds one',
            'resources':{'byte_states':len(c['states']),'quotient_states':len(nodes),'vocabulary_trie_states':len(trie),'token_arcs':arc_count,'lexical_pair_visits':visits,'peak_retained_states_and_arcs':peak,'state_cap':state_cap}}

def query(c,proof,raw,pieces,eos,fallback):
    state=0
    for b in raw:state=c['states'][state]['edges'].get(str(b),c['sink'])
    q=proof['quotient']['mapping'][state];node=proof['token_states'][q];ids=node['completion']
    return {'prefix':bytes_word(raw),'prefix_token_ids':[fallback[b] for b in raw] if fallback is not None else None,
            'byte_state':state,'token_state':q,'byte_distance':c['states'][state]['distance'],'token_distance':node['distance'],
            'token_completion_ids':ids,'completion_bytes':bytes_word(b''.join(pieces[t] for t in ids)) if ids is not None else None,
            'completion_with_eos_ids':ids+[eos] if ids is not None else None,'distance_including_eos':len(ids)+1 if ids is not None else None}


def make_trie(pieces):
    trie=[{'edges':{},'token':None}]
    for token,raw in sorted(pieces.items()):
        q=0
        for b in raw:
            if b not in trie[q]['edges']:
                if len(trie)>=CAP:raise Limit('vocabulary trie state cap')
                trie[q]['edges'][b]=len(trie);trie.append({'edges':{},'token':None})
            q=trie[q]['edges'][b]
        assert trie[q]['token'] is None;trie[q]['token']=token
    return trie
