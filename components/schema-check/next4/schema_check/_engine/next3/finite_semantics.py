"""Finite object/enum meaning kernel; no byte-DFA construction."""
import json,math,itertools,sys,importlib.util
from decimal import Decimal
from pathlib import Path
sp=importlib.util.spec_from_file_location('regex_reference',Path(__file__).resolve().parent/'../next2/reference.py')
ref=importlib.util.module_from_spec(sp);sp.loader.exec_module(ref)
parse,Unsupported,Limit=ref.parse,ref.Unsupported,ref.Limit
CAP=100000

def normalize(x):
    if isinstance(x,float):
        if not math.isfinite(x) or not x.is_integer() or abs(x)>2**53: raise Unsupported('fractional numeric constants')
        return int(x)
    if isinstance(x,str):
        if any(0xD800<=ord(c)<=0xDFFF for c in x): raise Unsupported('surrogate')
        return x
    if isinstance(x,list): return [normalize(v) for v in x]
    if isinstance(x,dict):
        if any(not isinstance(k,str) for k in x): raise Unsupported('key type')
        return {k:normalize(v) for k,v in sorted(x.items())}
    if x is None or type(x) in [int,bool]: return x
    raise Unsupported('JSON value')

def canonical(x): return json.dumps(normalize(x),ensure_ascii=False,separators=(',',':')).encode()
def equal(a,b):
    if isinstance(a,bool) or isinstance(b,bool): return type(a) is type(b) and a==b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)): return a==b
    if type(a) is not type(b): return False
    if isinstance(a,list): return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,dict): return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    return a==b

def syntax(s,depth=0):
    if depth>20: raise Unsupported('depth')
    if type(s) is bool:return
    allowed={'$schema','$comment','title','description','type','properties','required','additionalProperties','minProperties','maxProperties','enum','const','pattern','minLength','maxLength','allOf','anyOf','oneOf','not','minimum','maximum'}
    if not isinstance(s,dict) or set(s)-allowed: raise Unsupported('keyword')
    if s.get('$schema','https://json-schema.org/draft/2020-12/schema')!='https://json-schema.org/draft/2020-12/schema': raise Unsupported('dialect')
    if 'type' in s:
        tt=s['type'] if isinstance(s['type'],list) else [s['type']]
        if not tt or any(t not in ['string','boolean','null','integer','number','object','array'] for t in tt): raise Unsupported('type')
    for k in ['minLength','maxLength','minProperties','maxProperties']:
        if k in s and (type(s[k]) not in [int,float] or s[k]<0 or s[k]!=int(s[k])): raise Unsupported('integer bound')
    if 'pattern' in s: parse(s['pattern'])
    for v in s.get('enum',[])+([s['const']] if 'const' in s else []):normalize(v)
    if 'properties' in s:
        if not isinstance(s['properties'],dict): raise Unsupported('properties')
        for key,t in s['properties'].items(): normalize(key);syntax(t,depth+1)
    if 'required' in s and (not isinstance(s['required'],list) or any(type(k) is not str for k in s['required'])): raise Unsupported('required')
    if 'additionalProperties' in s: syntax(s['additionalProperties'],depth+1)
    for k in ['oneOf','allOf','anyOf']:
        if k in s:
            if not isinstance(s[k],list) or not s[k]:raise Unsupported('applicator')
            for t in s[k]:syntax(t,depth+1)
    if 'not' in s:syntax(s['not'],depth+1)

def valid(s,x):
    if type(s) is bool:return s
    isnum=type(x) in [int,float]
    types={'string':isinstance(x,str),'boolean':type(x)is bool,'null':x is None,'object':type(x)is dict,'array':type(x)is list,'integer':isnum and x==int(x),'number':isnum}
    if 'type' in s and not any(types[t] for t in (s['type'] if isinstance(s['type'],list) else [s['type']])):return False
    if 'enum' in s and not any(equal(x,v) for v in s['enum']):return False
    if 'const' in s and not equal(x,s['const']):return False
    if type(x)is str:
        if not s.get('minLength',0)<=len(x)<=s.get('maxLength',float('inf')):return False
        if 'pattern'in s:
            p=parse(s['pattern'])
            if p[0]=='literal':
                if x!=p[1]:return False
            elif len(x)<p[2] or (p[3]is not None and len(x)>p[3]) or any(not any(lo<=ord(c)<=hi for lo,hi in p[1]) for c in x):return False
    if type(x)is dict:
        if not set(s.get('required',[]))<=x.keys():return False
        if not s.get('minProperties',0)<=len(x)<=s.get('maxProperties',float('inf')):return False
        props=s.get('properties',{})
        if any(not valid(props.get(k,s.get('additionalProperties',True)),v) for k,v in x.items()):return False
    if isnum and not s.get('minimum',-float('inf'))<=x<=s.get('maximum',float('inf')):return False
    if any(not valid(t,x) for t in s.get('allOf',[])):return False
    if 'anyOf'in s and not any(valid(t,x) for t in s['anyOf']):return False
    if 'oneOf'in s and sum(valid(t,x) for t in s['oneOf'])!=1:return False
    return not ('not'in s and valid(s['not'],x))

def guard(s,depth=0):
    if depth>20:raise Unsupported('depth')
    if s is False:return []
    if s is True:raise Unsupported('unbounded true')
    if s.get('not',False)is True or s.get('not',False)=={}:return []
    if 'enum'in s:return s['enum']
    if 'const'in s:return [s['const']]
    if s.get('type')=='boolean':return [True,False]
    if s.get('type')=='null':return [None]
    if s.get('type')=='object':
        if s.get('maxProperties')==0:return [{}]
        if s.get('additionalProperties')is False:
            props=s.get('properties',{});required=set(s.get('required',[]))
            if not required<=props.keys() or s.get('minProperties',0)>len(props):return []
            candidates=[{}]
            for key,t in sorted(props.items()):
                values=[v for v in guard(t,depth+1) if valid(t,v)]
                choices=len(values)+(key not in required)
                if len(candidates)*choices>CAP:raise Limit('finite object candidate cap')
                candidates=[{**c,key:v} for c in candidates for v in values]+(candidates if key not in required else [])
            return candidates
    if s.get('type')=='string':
        if s.get('maxLength')==0:return ['']
        if 'pattern'in s:
            p=parse(s['pattern'])
            if p[0]=='literal':return [p[1]]
            maximum=min(p[3] if p[3]is not None else 10**9,int(s.get('maxLength',10**9)))
            size=sum(hi-lo+1 for lo,hi in p[1])
            if maximum==10**9:raise Unsupported('unbounded string child')
            if maximum>1000 or size>CAP or sum(size**n for n in range(maximum+1))>CAP:raise Limit('finite string candidate cap')
            chars=sorted({chr(i) for lo,hi in p[1] for i in range(lo,hi+1)})
            return [''.join(t) for n in range(maximum+1) for t in itertools.product(chars,repeat=n)]
    for t in s.get('allOf',[]):
        try:return guard(t,depth+1)
        except Unsupported:pass
    for k in ['oneOf','anyOf']:
        if k in s:
            result=[]
            for t in s[k]:
                result.extend(guard(t,depth+1))
                if len(result)>CAP:raise Limit('union candidate cap')
            return result
    raise Unsupported('no finite guard (open object is not silently closed)')


def parse_input(text):
    # Avoid silently rounding a JSON numeric constant through binary64 at the CLI.
    def exact(v):
        if isinstance(v,Decimal):
            if v!=v.to_integral_value():raise Unsupported('fractional numeric schema input')
            return int(v)
        if isinstance(v,list):return [exact(x) for x in v]
        if isinstance(v,dict):return {k:exact(x) for k,x in v.items()}
        return v
    def invalid(v):raise Unsupported('non-JSON number')
    return exact(json.loads(text,parse_float=Decimal,parse_constant=invalid))
