"""Presentation from a byte automaton. No producer imports."""
from ._shared import FORMAT,UNITS,LIMITS,dumps,sha

def word(values):
    if values is None:return None
    raw=bytes(values)
    try:text=raw.decode('utf-8')
    except UnicodeDecodeError:text=None
    return {'bytes':values,'hex':raw.hex(),'utf8':text,'length_bytes':len(raw)}

def display(w):
    v=repr(w['utf8']) if w['utf8'] is not None else 'hex:'+w['hex']
    return v if len(v)<=200 else v[:197]+'...'

def project(schema,document_hash,prefix,provided,c):
    nodes=c['states'];start=nodes[0];example=word(start['completion']);q=0;trace=[0]
    for b in prefix:q=nodes[q]['edges'].get(str(b),c['sink']);trace.append(q)
    state=nodes[q]
    query=None
    if provided:
        possible=state['distance'] is not None
        query={'input':word(prefix),'state':q,'trace':trace,'accepting':state['accept'],'can_complete':possible,
               'shortest_completion':word(state['completion']),
               'evidence':{'kind':'shortest_distance_and_replay' if possible else 'closed_nonaccepting_states',
                           'state':q,'distance':state['distance']}}
    explanation='SUPPORTED: empty canonical language.' if c['status']=='EMPTY' else f"SUPPORTED: nonempty canonical language; shortest example is {example['length_bytes']} bytes: {display(example)}."
    if provided:
        explanation+=(' Prefix cannot be completed to this canonical language; its reached state has a closure certificate.' if not query['can_complete'] else f" Prefix has a shortest completion of {query['shortest_completion']['length_bytes']} bytes: {display(query['shortest_completion'])}.")
    return {'format':FORMAT,'support':'SUPPORTED','input':{'schema':schema,'schema_document_sha256':document_hash,
             'schema_canonical_sha256':sha(dumps(schema).encode()),'prefix_bytes':prefix,'prefix_provided':provided},
            'language':{'empty':c['status']=='EMPTY','shortest_example':example},'prefix':query,
            'certificate':c,'verification':'NOT_RUN','explanation':explanation,'units':UNITS,'limits':LIMITS}
