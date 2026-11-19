"""Verification entry: producer files are not imported or read."""
import sys,re
from pathlib import Path
from ._shared import Failure,FORMAT,COMPLETION_LIMIT,PREFIX_LIMIT,byte_list,dumps,sha,parse_schema
from ._format import project

def block_producers():
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(args[0].decode() if isinstance(args[0],bytes) else args[0])
            if p.name in ['generate.py','nfa_builder.py'] or p.name.startswith(('generate.','nfa_builder.')):
                raise RuntimeError('verifier attempted to read producer code')
    sys.addaudithook(audit)

def verify(bundle,external_text=None):
    block_producers()
    if bundle.get('format')!=FORMAT:raise Failure('INVALID_INPUT','unrecognized evidence format')
    if bundle.get('support')!='SUPPORTED':raise Failure('NOT_APPLICABLE','only SUPPORTED artifacts contain mathematical certificates')
    source=bundle['input'];schema=parse_schema(dumps(source['schema']));doc=source['schema_document_sha256']
    if type(doc) is not str or re.fullmatch('[0-9a-f]{64}',doc) is None:raise Failure('INVALID_INPUT','invalid document digest')
    if external_text is not None:
        if sha(external_text.encode())!=doc or dumps(parse_schema(external_text))!=dumps(schema):raise Failure('INVALID_INPUT','external schema does not match this artifact')
    raw=byte_list(source['prefix_bytes']);provided=source['prefix_provided']
    if type(provided) is not bool or (not provided and raw) or len(raw)>PREFIX_LIMIT:raise Failure('INVALID_INPUT','invalid prefix binding')
    c=bundle['certificate'];nodes=c['states'];budget=0
    if type(nodes) is not list or not 1<=len(nodes)<=100000:raise Failure('INVALID_INPUT','invalid state count')
    if type(c['sink']) is not int or not 0<=c['sink']<len(nodes):raise Failure('INVALID_INPUT','invalid sink')
    for node in nodes:
        if set(node)!=set(['edges','accept','distance','completion']) or type(node['accept']) is not bool:raise Failure('INVALID_INPUT','invalid state record')
        if type(node['edges']) is not dict or len(node['edges'])>256:raise Failure('INVALID_INPUT','invalid byte transitions')
        for b,t in node['edges'].items():
            if type(b) is not str or not b.isascii() or not b.isdecimal() or str(int(b))!=b or not 0<=int(b)<256 or type(t) is not int or not 0<=t<len(nodes):raise Failure('INVALID_INPUT','invalid transition')
        d=node['distance'];w=node['completion']
        if d is None:
            if w is not None:raise Failure('INVALID_INPUT','null distance requires null completion')
        else:
            if type(d) is not int or not 0<=d<len(nodes):raise Failure('INVALID_INPUT','invalid distance')
            byte_list(w);budget+=len(w)
            if len(w)!=d:raise Failure('INVALID_INPUT','completion length differs from distance')
        if budget>COMPLETION_LIMIT:raise Failure('UNKNOWN','completion evidence exceeds budget')
    engine=Path(__file__).resolve().parent/'_engine/next7';sys.path.insert(0,str(engine))
    try:
        from checker import check
        checked=check(schema,c)
    finally:sys.path.remove(str(engine))
    expected=project(schema,doc,raw,provided,c)
    if dumps(bundle)!=dumps(expected):raise Failure('INVALID_INPUT','output claims, schema digest, prefix trace, or formatting metadata were changed')
    return {'format':FORMAT,'verification':'PASS','schema_document_sha256':doc,
            'schema_canonical_sha256':source['schema_canonical_sha256'],'external_schema_bound':external_text is not None,
            'language_and_query_checked':True,'producer_access_blocked':True,'engine_check':checked,
            'explanation':'PASS: canonical language, shortest distances, completions, and prefix claims verified. The declared shared semantic kernels remain trusted.'}
