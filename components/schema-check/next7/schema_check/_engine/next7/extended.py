"""Declared shared finite/rational meaning kernel, not an automaton producer."""
import importlib.util,itertools,math
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from schema_check._shared import dumps,schema_syntax,Failure,normalize
sp=importlib.util.spec_from_file_location('prior_finite_kernel',Path(__file__).resolve().parent/'../next3/finite_semantics.py')
old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
Unsupported,Limit,CAP,parse=old.Unsupported,old.Limit,100000,old.parse
def syntax(s):
    try:schema_syntax(s)
    except Failure as e:raise Unsupported(e.reason) from e
    def walk(t):
        if type(t)is bool:return
        if 'pattern'in t:parse(t['pattern'])
        for child in t.get('properties',{}).values():walk(child)
        for k in ['items','additionalProperties','not']:
            if k in t:walk(t[k])
        for k in ['allOf','anyOf','oneOf']:
            for child in t.get(k,[]):walk(child)
    walk(s)
def number(x):return type(x) in [int,float,Decimal,Fraction]
def rat(x):return Fraction(Decimal(str(x))) if isinstance(x,float) else Fraction(x)
def decimal(x):
    x=rat(x);den=x.denominator;a=b=0
    while den%2==0:a+=1;den//=2
    while den%5==0:b+=1;den//=5
    if den!=1:raise Unsupported('nonterminating decimal')
    scale=max(a,b);v=x.numerator*2**(scale-a)*5**(scale-b)
    # Construct exactly; Decimal arithmetic under its default context would round.
    return Decimal((int(v<0),tuple(map(int,str(abs(v)))), -scale))
def canonical(x):
    if isinstance(x,Fraction):x=decimal(x)
    if isinstance(x,list):return b'['+b','.join(canonical(v) for v in x)+b']'
    if isinstance(x,dict):return b'{'+b','.join(dumps(k).encode()+b':'+canonical(v) for k,v in sorted(x.items()))+b'}'
    return dumps(x).encode()
def equal(a,b):
    if type(a) is bool or type(b) is bool:return type(a) is type(b) and a==b
    if number(a) and number(b):return rat(a)==rat(b)
    if type(a) is not type(b):return False
    if isinstance(a,list):return len(a)==len(b) and all(equal(v,w) for v,w in zip(a,b))
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    return a==b
def valid(s,x):
    if type(s) is bool:return s
    num=number(x)
    types={'number':num,'integer':num and rat(x).denominator==1,'string':type(x)is str,'object':type(x)is dict,'array':type(x)is list,'boolean':type(x)is bool,'null':x is None}
    if 'type'in s and not any(types[t] for t in (s['type'] if isinstance(s['type'],list) else [s['type']])):return False
    if 'const'in s and not equal(x,s['const']):return False
    if 'enum'in s and not any(equal(x,v) for v in s['enum']):return False
    if num:
        v=rat(x)
        if 'minimum'in s and v<rat(s['minimum']) or 'maximum'in s and v>rat(s['maximum']):return False
        if 'exclusiveMinimum'in s and v<=rat(s['exclusiveMinimum']) or 'exclusiveMaximum'in s and v>=rat(s['exclusiveMaximum']):return False
        if 'multipleOf'in s and (v/rat(s['multipleOf'])).denominator!=1:return False
    if type(x)is str:
        if not s.get('minLength',0)<=len(x)<=s.get('maxLength',math.inf):return False
        if 'pattern'in s:
            p=parse(s['pattern'])
            if p[0]=='literal':
                if x!=p[1]:return False
            elif len(x)<p[2] or p[3] is not None and len(x)>p[3] or any(not any(lo<=ord(c)<=hi for lo,hi in p[1]) for c in x):return False
    if type(x)is list:
        if not s.get('minItems',0)<=len(x)<=s.get('maxItems',math.inf):return False
        if not all(valid(s.get('items',True),v) for v in x):return False
        if s.get('uniqueItems',False) and any(equal(x[i],x[j]) for i in range(len(x)) for j in range(i)):return False
    if type(x)is dict:
        if not set(s.get('required',[]))<=x.keys() or not s.get('minProperties',0)<=len(x)<=s.get('maxProperties',math.inf):return False
        if any(not valid(s.get('properties',{}).get(k,s.get('additionalProperties',True)),v) for k,v in x.items()):return False
    if any(not valid(t,x) for t in s.get('allOf',[])):return False
    if 'anyOf'in s and not any(valid(t,x) for t in s['anyOf']):return False
    if 'oneOf'in s and sum(valid(t,x) for t in s['oneOf'])!=1:return False
    return not ('not'in s and valid(s['not'],x))
def unique(values):return list({canonical(v):v for v in values}.values())
def guard(s,depth=0):
    if depth>20:raise Unsupported('finite guard depth')
    if s is False:return []
    if s is True:raise Unsupported('unbounded true')
    if 'enum'in s:return s['enum']
    if 'const'in s:return [s['const']]
    if s.get('not',False)is True or s.get('not',False)=={}:return []
    tt=s.get('type')
    if isinstance(tt,list):
        result=[]
        for t in tt:result.extend(guard({**s,'type':t},depth+1))
        if len(result)>CAP:raise Limit('type union candidate cap')
        return result
    if tt=='boolean':return [False,True]
    if tt=='null':return [None]
    if tt in ['number','integer']:
        lows=[rat(s[k]) for k in ['minimum','exclusiveMinimum'] if k in s];highs=[rat(s[k]) for k in ['maximum','exclusiveMaximum'] if k in s]
        if lows and highs:
            low,high=max(lows),min(highs)
            if low>high:return []
            step=Fraction(1) if tt=='integer' else rat(s['multipleOf']) if 'multipleOf'in s else None
            if low==high:return [decimal(low)]
            if step is not None:
                lo=math.ceil(low/step);hi=math.floor(high/step)
                if hi-lo+1>CAP:raise Limit('finite numeric candidate cap')
                return [decimal(k*step) for k in range(lo,hi+1)]
    if tt=='array':
        low=s.get('minItems',0);high=s.get('maxItems')
        if high is not None and low>high:return []
        if high==0:return [[]]
        try:values=unique(v for v in guard(s.get('items',True),depth+1) if valid(s.get('items',True),v))
        except Unsupported:
            if s.get('items')is False:return [[]] if low==0 else []
            raise
        if not values:return [[]] if low==0 else []
        if s.get('uniqueItems',False):high=min(high,len(values)) if high is not None else len(values)
        if high is None:raise Unsupported('unbounded finite-alphabet array without uniqueItems')
        if high>1000:raise Limit('array length cap')
        count=0
        for n in range(low,high+1):
            count+=math.perm(len(values),n) if s.get('uniqueItems',False) else len(values)**n
            if count>CAP:raise Limit('finite array candidate cap')
        return [list(t) for n in range(low,high+1) for t in (itertools.permutations(values,n) if s.get('uniqueItems',False) else itertools.product(values,repeat=n))]
    if tt=='object' and s.get('additionalProperties')is False:
        props=s.get('properties',{});required=set(s.get('required',[]))
        if not required<=props.keys():return []
        candidates=[{}]
        for k,child in sorted(props.items()):
            vs=unique(v for v in guard(child,depth+1) if valid(child,v));choices=len(vs)+(k not in required)
            if len(candidates)*choices>CAP:raise Limit('finite object candidate cap')
            candidates=[{**c,k:v} for c in candidates for v in vs]+(candidates if k not in required else [])
        return candidates
    if tt=='string':return old.guard(s,depth)
    for child in s.get('allOf',[]):
        try:return guard(child,depth+1)
        except Unsupported:pass
    for k in ['anyOf','oneOf']:
        if k in s:
            out=[]
            for child in s[k]:
                out.extend(guard(child,depth+1))
                if len(out)>CAP:raise Limit('finite union candidate cap')
            return out
    raise Unsupported('no necessary finite guard')
