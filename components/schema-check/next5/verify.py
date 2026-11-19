"""No producer import. Directly walk every ordinary token from every quotient state."""
from vocabulary import digest,bytes_word

def check(c,proof,pieces,eos):
    if not __debug__:raise RuntimeError('verification requires assertions enabled')
    assert proof['format']=='schema-check-token/v1' and proof['byte_certificate_sha256']==digest(c)
    assert proof['distance_convention']=='ordinary tokens to an accepting state; explicit EOS adds one'
    assert proof['eos_token_id']==eos
    q=proof['quotient'];mapping=q['mapping'];nodes=q['states'];dead=q['sink'];old=c['states'];olddead=c['sink']
    assert type(q['start']) is type(dead) is int
    assert len(mapping)==len(old) and all(type(x) is int and 0<=x<len(nodes) for x in mapping)
    assert set(mapping)==set(range(len(nodes))) and q['start']==mapping[0] and dead==mapping[olddead]
    assert not nodes[dead]['accept'] and not nodes[dead]['edges']
    for n in nodes:
        assert type(n['accept']) is bool
        assert all(type(b) is str and str(int(b))==b and 0<=int(b)<256 and type(t) is int and 0<=t<len(nodes) for b,t in n['edges'].items())
    for i,n in enumerate(old):
        quotient=nodes[mapping[i]];assert n['accept']==quotient['accept']
        for b in n['edges'].keys()|quotient['edges'].keys():
            assert mapping[n['edges'].get(b,olddead)]==quotient['edges'].get(b,dead)
    graph=proof['token_states'];assert len(graph)==len(nodes)
    # This path does not build or use the producer's vocabulary trie.
    walked=0
    for start,n in enumerate(graph):
        groups={}
        if start!=dead:
            for token,raw in sorted(pieces.items()):
                state=start
                for b in raw:
                    walked+=1;state=nodes[state]['edges'].get(str(b),dead)
                    if state==dead:break
                if state!=dead:groups.setdefault(state,[]).append(token)
        expected=[{'target':state,'token_id':ids[0],'count':len(ids),'ids_sha256':digest(ids)} for state,ids in sorted(groups.items())]
        assert type(n['accept']) is bool and all(type(e['target']) is type(e['token_id']) is type(e['count']) is int for e in n['edges'])
        assert n['distance'] is None or (type(n['distance']) is int and 0<=n['distance']<len(graph))
        assert n['completion'] is None or (type(n['completion']) is list and all(type(i) is int and i in pieces for i in n['completion']))
        assert n['edges']==expected and n['accept']==nodes[start]['accept']
        children=[graph[e['target']]['distance'] for e in n['edges'] if graph[e['target']]['distance'] is not None]
        d=0 if n['accept'] else 1+min(children) if children else None
        assert n['distance']==d
        if d is None:assert n['completion'] is None
        else:
            assert type(d) is int and len(n['completion'])==d
            if d:assert n['completion']==min([e['token_id']]+graph[e['target']]['completion'] for e in n['edges'] if graph[e['target']]['distance']==d-1)
            state=start
            for token in n['completion']:
                assert token in pieces and token!=eos
                for b in pieces[token]:state=nodes[state]['edges'].get(str(b),dead)
            assert nodes[state]['accept']
    assert proof['resources']['peak_retained_states_and_arcs']<=proof['resources']['state_cap']<=500000
    mismatches=[i for i,n in enumerate(old) if n['distance'] is not None and graph[mapping[i]]['distance'] is None]
    return {'status':'PASS','byte_states':len(old),'token_states':len(graph),'token_transition_bytes_walked':walked,'byte_live_token_dead_original_states':mismatches}

def check_queries(c,proof,queries,pieces,eos,fallback):
    if not __debug__:raise RuntimeError('verification requires assertions enabled')
    for r in queries:
        assert all(type(i) is int and 0<=i<256 for i in r['prefix']['bytes'])
        assert type(r['prefix']['length_bytes']) is int
        assert type(r['byte_state']) is type(r['token_state']) is int
        for field in ['byte_distance','token_distance','distance_including_eos']:
            assert r[field] is None or (type(r[field]) is int and r[field]>=0)
        raw=bytes(r['prefix']['bytes']);assert r['prefix']==bytes_word(raw);state=0
        for b in raw:state=c['states'][state]['edges'].get(str(b),c['sink'])
        q=proof['quotient']['mapping'][state];n=proof['token_states'][q]
        assert (r['byte_state'],r['token_state'],r['byte_distance'],r['token_distance'])==(state,q,c['states'][state]['distance'],n['distance'])
        assert r['token_completion_ids']==n['completion']
        if fallback is not None:
            assert all(type(i) is int and i in pieces for i in r['prefix_token_ids'])
            assert r['prefix_token_ids']==[fallback[b] for b in raw]
            assert b''.join(pieces[t] for t in r['prefix_token_ids'])==raw
        ids=n['completion']
        if ids is None:assert r['completion_bytes'] is None and r['completion_with_eos_ids'] is None and r['distance_including_eos'] is None
        else:
            assert all(type(i) is int and i in pieces for i in r['token_completion_ids'])
            assert type(r['completion_with_eos_ids']) is list and all(type(i) is int for i in r['completion_with_eos_ids'])
            assert type(r['completion_bytes']['length_bytes']) is int and all(type(i) is int for i in r['completion_bytes']['bytes'])
            suffix=b''.join(pieces[t] for t in ids);assert r['completion_bytes']==bytes_word(suffix)
            assert r['completion_with_eos_ids']==ids+[eos] and r['distance_including_eos']==len(ids)+1
            for b in suffix:state=c['states'][state]['edges'].get(str(b),c['sink'])
            assert c['states'][state]['accept']
    return len(queries)
