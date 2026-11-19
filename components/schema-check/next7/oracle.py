"""Third-party jsonschema adjudication with exact Fractions, separate from meaning kernel."""
import sys,json,time,resource,signal,random
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
P=Path(__file__).resolve().parent;sys.path[:0]=[str(P),str(P/'schema_check/_engine/next7')]
from schema_check._shared import parse_schema,load_json,dumps
from extended import canonical,valid,guard,Unsupported,Limit
from checker import prefix
from jsonschema import Draft202012Validator,validators
import importlib.metadata
def exact(x):
    if isinstance(x,(float,Decimal)):return Fraction(str(x))
    if isinstance(x,list):return [exact(v) for v in x]
    if isinstance(x,dict):return {k:exact(v) for k,v in x.items()}
    return x
def isnum(checker,x):return type(x) in [int,Fraction]
def isint(checker,x):return isnum(checker,x) and Fraction(x).denominator==1
def schema_exact(s):
    if type(s)is bool:return s
    out={k:exact(v) for k,v in s.items() if k!='$schema'}
    # The already checked dialect is fixed. Remove only schema-location dialect
    # declarations, so evolve() keeps our rational integer checker in subschemas.
    # Do not remove data properties named $schema inside enum/const instances.
    for k in ['allOf','anyOf','oneOf']:
        if k in s:out[k]=[schema_exact(t) for t in s[k]]
    for k in ['not','items','additionalProperties']:
        if k in s:out[k]=schema_exact(s[k])
    if 'properties'in s:out['properties']={k:schema_exact(v) for k,v in s['properties'].items()}
    return out
Validator=validators.extend(Draft202012Validator,type_checker=Draft202012Validator.TYPE_CHECKER.redefine('number',isnum).redefine('integer',isint))
cases=json.loads((P/'CASES.json').read_text());rows=[];failures=[];random.seed(5417);start=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(29)
for i,c in enumerate(cases):
    if c['scope']not in ['new-original-42','new-typed-lifts','new-controls']:continue
    f=P/'all'/f'{i:03d}.json'
    if not f.exists():continue
    r=load_json(f.read_text());b=r['bundle']
    if b['support']!='SUPPORTED':continue
    s=parse_schema(json.dumps(c['schema']));validator=Validator(schema_exact(s));count=0
    for t in c['tests']:
        assert validator.is_valid(exact(t['data']))==t['valid'],(c['id'],t)
        assert valid(s,exact(t['data']))==t['valid'],(c['id'],t)
        count+=1
    if b['certificate']['mode']=='rational-numeric-features':
        probes=[Fraction(k,10**scale) for scale in range(4) for k in range(-150,151)]
        probes += [Fraction(random.randrange(-1000000,1000000),10**random.randrange(1,8)) for _ in range(100)]
        probes += [Fraction(10**100),Fraction(-10**100),Fraction(1,10**100),Fraction(25,10)+Fraction(1,10**100),Fraction(25,10)-Fraction(1,10**100)]
        for x in probes:
            expected=validator.is_valid(x);actual=prefix(b['certificate'],canonical(x))['accepting']
            assert actual==expected==valid(s,x),(c['id'],str(x),expected,actual);count+=1
    elif b['certificate']['mode']=='finite-number-array':
        values=guard(s)
        for x in values:
            assert validator.is_valid(exact(x))==valid(s,x)==prefix(b['certificate'],canonical(x))['accepting'],(c['id'],x);count+=1
    elif not b['language']['empty']:
        witness=bytes(b['certificate']['states'][0]['completion']);value=json.loads(witness,parse_float=Fraction)
        assert validator.is_valid(value);count+=1
    nf=P/'native'/f'{i:03d}.json'
    if nf.exists():
        native=json.loads(nf.read_text())
        for engine in ['llguidance','xgrammar','outlines']:
            for p in native[engine]['prefixes']:
                if not p['accepting']:continue
                try:data=json.loads(bytes(p['bytes']),parse_float=Fraction,parse_int=int);good=validator.is_valid(data)
                except (ValueError,UnicodeDecodeError):good=False
                if not good:failures.append({'id':c['id'],'engine':engine,'bytes':p['bytes']})
    rows.append({'id':c['id'],'exact_fixture_candidate_numeric_checks':count})
print(json.dumps({'status':'PASS','jsonschema_version':importlib.metadata.version('jsonschema'),'exact_rational_typechecker':True,'records':rows,'independently_confirmed_invalid_acceptances':failures,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
