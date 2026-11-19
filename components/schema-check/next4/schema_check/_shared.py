"""Input contract and deterministic JSON. No automaton producer imports."""
import hashlib,json
from decimal import Decimal

FORMAT='schema-check/v1'
SCHEMA_LIMIT=1024**2
PREFIX_LIMIT=1024**2
ARTIFACT_LIMIT=32*1024**2
COMPLETION_LIMIT=2_000_000
LIMITS={'states':100000,'completion_entries':COMPLETION_LIMIT,'cpu_seconds':30,'wall_seconds':30,
        'schema_bytes':SCHEMA_LIMIT,'prefix_bytes':PREFIX_LIMIT,'artifact_bytes':ARTIFACT_LIMIT}
UNITS={'alphabet':'byte','distance':'bytes','encoding':'UTF-8','language':'canonical compact JSON with sorted object keys, integer numbers, Python JSON string escapes, raw Unicode scalars, and no whitespace'}

class Failure(ValueError):
    def __init__(self,kind,reason):self.kind=kind;self.reason=reason;super().__init__(reason)

def dumps(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(x):return hashlib.sha256(x).hexdigest()

def pairs(items):
    out={}
    for k,v in items:
        if k in out:raise Failure('INVALID_INPUT',f'duplicate JSON key: {k!r}')
        out[k]=v
    return out

def integer(s):
    if len(s.lstrip('-'))>4096:raise Failure('UNKNOWN','number exceeds 4096 digits')
    return int(s)

def decimal(s):
    v=Decimal(s)
    if v and (v.adjusted()>4095 or v.adjusted()<-4096):raise Failure('UNKNOWN','numeric exponent exceeds input budget')
    if v!=v.to_integral_value():raise Failure('UNSUPPORTED','fractional schema numbers are outside this release')
    return int(v)

def invalid_constant(s):raise Failure('INVALID_INPUT',f'non-JSON number: {s}')

def load_json(text):
    try:return json.loads(text,object_pairs_hook=pairs,parse_int=integer,parse_float=decimal,parse_constant=invalid_constant)
    except Failure:raise
    except (ValueError,RecursionError) as e:raise Failure('INVALID_INPUT',f'invalid JSON: {e}') from e

def normalize(x,depth=0):
    if depth>64:raise Failure('UNKNOWN','JSON nesting exceeds 64 levels')
    if isinstance(x,str):
        if any(0xD800<=ord(c)<=0xDFFF for c in x):raise Failure('UNSUPPORTED','surrogates are not Unicode scalars')
    if isinstance(x,list):return [normalize(v,depth+1) for v in x]
    if isinstance(x,dict):return {normalize(k,depth+1):normalize(v,depth+1) for k,v in sorted(x.items())}
    return x

def schema_syntax(s,path='$',depth=0):
    if depth>20:raise Failure('UNSUPPORTED',f'{path}: schema depth exceeds 20')
    if type(s) is bool:return
    if not isinstance(s,dict):raise Failure('INVALID_INPUT',f'{path}: schema must be an object or boolean')
    for k in ['title','description','$comment','$schema']:
        if k in s and not isinstance(s[k],str):raise Failure('INVALID_INPUT',f'{path}.{k}: expected string')
    if 'type' in s:
        types=s['type'] if isinstance(s['type'],list) else [s['type']]
        if not types or any(type(t) is not str or t not in ['string','boolean','null','integer','number','object','array'] for t in types) or len(types)!=len(set(types)):
            raise Failure('INVALID_INPUT',f'{path}.type: expected a JSON Schema type or distinct nonempty type array')
    for k in ['minLength','maxLength','minProperties','maxProperties']:
        if k in s and (type(s[k]) is not int or s[k]<0):raise Failure('INVALID_INPUT',f'{path}.{k}: expected nonnegative integer')
    for k in ['minimum','maximum']:
        if k in s and type(s[k]) is not int:raise Failure('INVALID_INPUT',f'{path}.{k}: expected number')
    if 'pattern' in s and type(s['pattern']) is not str:raise Failure('INVALID_INPUT',f'{path}.pattern: expected string')
    if 'enum' in s and type(s['enum']) is not list:raise Failure('INVALID_INPUT',f'{path}.enum: expected array')
    if 'properties' in s:
        if type(s['properties']) is not dict:raise Failure('INVALID_INPUT',f'{path}.properties: expected object')
        for k,v in s['properties'].items():schema_syntax(v,f'{path}.properties[{k!r}]',depth+1)
    if 'required' in s:
        r=s['required']
        if type(r) is not list or any(type(k) is not str for k in r) or len(r)!=len(set(r)):
            raise Failure('INVALID_INPUT',f'{path}.required: expected distinct strings')
    for k in ['not','additionalProperties']:
        if k in s:schema_syntax(s[k],f'{path}.{k}',depth+1)
    for k in ['allOf','anyOf','oneOf']:
        if k in s:
            if type(s[k]) is not list or not s[k]:raise Failure('INVALID_INPUT',f'{path}.{k}: expected nonempty schema array')
            for i,t in enumerate(s[k]):schema_syntax(t,f'{path}.{k}[{i}]',depth+1)
    allowed={'$schema','$comment','title','description','type','properties','required','additionalProperties','minProperties','maxProperties','enum','const','pattern','minLength','maxLength','allOf','anyOf','oneOf','not','minimum','maximum'}
    if set(s)-allowed:raise Failure('UNSUPPORTED',f'{path}: unsupported keyword {sorted(set(s)-allowed)[0]!r}')
    if s.get('$schema','https://json-schema.org/draft/2020-12/schema')!='https://json-schema.org/draft/2020-12/schema':
        raise Failure('UNSUPPORTED',f'{path}: only the declared Draft 2020-12 fragment is supported')

def parse_schema(text):
    s=normalize(load_json(text));schema_syntax(s);return s

def failure(kind,reason):
    return {'format':FORMAT,'support':kind,'language':{'empty':None,'shortest_example':None},'prefix':None,
            'certificate':None,'explanation':f'{kind}: {reason}','diagnostic':reason,'units':UNITS,'limits':LIMITS}

def byte_list(x):
    if type(x) is not list or any(type(v) is not int or not 0<=v<256 for v in x):raise Failure('INVALID_INPUT','expected an array of integer bytes')
    return x
