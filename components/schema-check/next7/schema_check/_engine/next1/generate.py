"""Exact finite-guard fragment -> canonical UTF-8 byte trie DFA.
Not an infinite regex-language compiler. Unsupported input is explicit.
"""
import itertools,json,re,time,hashlib
from collections import deque

class Unsupported(ValueError): pass
class Limit(ValueError): pass
MAX_STATES=100000
START=0

def canon(x): return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode('utf-8')
def equal(a,b):
    if isinstance(a,bool) or isinstance(b,bool): return type(a) is type(b) and a==b
    return a==b

def pattern(p):
    if re.fullmatch(r'\^[A-Za-z][*+?]\$',p): p='^['+p[1]+']'+p[2:]
    # Exact ECMAScript full-anchor fragment: literal or explicit finite class, one quantifier.
    if re.fullmatch(r'\^[^\[\]\\.*+?{}()|^$]+\$',p): return ('literal',p[1:-1],1,1)
    m=re.fullmatch(r'\^\[([^\]\\^\-]+)\](\*|\+|\?|\{\d+(?:,\d+)?\})\$',p)
    if not m: raise Unsupported('pattern outside finite-class full-anchor fragment')
    chars,q=m.groups()
    if any(0xD800<=ord(c)<=0xDFFF for c in chars): raise Unsupported('surrogate')
    if q=='*': lo,hi=0,None
    elif q=='+': lo,hi=1,None
    elif q=='?': lo,hi=0,1
    else:
        nums=q[1:-1].split(',');lo=int(nums[0]);hi=int(nums[-1])
    if hi is not None and hi<lo: raise Unsupported('invalid quantifier')
    return ('class',''.join(sorted(set(chars))),lo,hi)

def validate_schema(s,depth=0):
    if depth>20: raise Unsupported('depth')
    if type(s) is bool: return
    if not isinstance(s,dict): raise Unsupported('schema type')
    if set(s)-{'type','enum','const','pattern','minLength','maxLength','allOf','anyOf','oneOf','not','$schema','description','title'}: raise Unsupported('keyword')
    if '$schema' in s and s['$schema']!='https://json-schema.org/draft/2020-12/schema': raise Unsupported('dialect')
    if 'type' in s and s['type'] not in ['string','boolean','null']: raise Unsupported('type restriction')
    for k in ['minLength','maxLength']:
        if k in s and (type(s[k]) is not int or s[k]<0): raise Unsupported('length')
    if 'pattern' in s: pattern(s['pattern'])
    vals=s.get('enum',[])+([s['const']] if 'const' in s else [])
    for x in vals:
        if not (x is None or type(x) in [str,bool,int]) or (type(x) is int and abs(x)>2**53): raise Unsupported('enum scalar')
        canon(x)
    for k in ['allOf','anyOf','oneOf']:
        if k in s:
            if not isinstance(s[k],list) or not s[k]: raise Unsupported('applicator')
            for child in s[k]: validate_schema(child,depth+1)
    if 'not' in s: validate_schema(s['not'],depth+1)

def matches(s,x):
    if type(s) is bool: return s
    if 'type' in s:
        if s['type']=='string' and type(x) is not str: return False
        if s['type']=='boolean' and type(x) is not bool: return False
        if s['type']=='null' and x is not None: return False
    if 'enum' in s and not any(equal(x,v) for v in s['enum']): return False
    if 'const' in s and not equal(x,s['const']): return False
    if type(x) is str:
        if len(x)<s.get('minLength',0) or len(x)>s.get('maxLength',float('inf')): return False
        if 'pattern' in s:
            kind,chars,lo,hi=pattern(s['pattern'])
            if kind=='literal':
                if x!=chars: return False
            elif not (len(x)>=lo and (hi is None or len(x)<=hi) and all(c in chars for c in x)): return False
    if any(not matches(t,x) for t in s.get('allOf',[])): return False
    if 'anyOf' in s and not any(matches(t,x) for t in s['anyOf']): return False
    if 'oneOf' in s and sum(matches(t,x) for t in s['oneOf'])!=1: return False
    if 'not' in s and matches(s['not'],x): return False
    return True

def domain(s):
    # Return a sound finite superset of every satisfying JSON value, or fail closed.
    if s is False: return []
    if s is True: raise Unsupported('no finite guard')
    if s.get('not',False) is True or s.get('not',False)=={}: return []
    if 'oneOf' in s and all(type(x) is bool for x in s['oneOf']) and sum(s['oneOf'])!=1: return []
    if 'enum' in s: return s['enum']
    if 'const' in s: return [s['const']]
    if s.get('type')=='boolean': return [False,True]
    if s.get('type')=='null': return [None]
    if s.get('type')=='string':
        if s.get('maxLength')==0: return ['']
        if 'pattern' in s:
            kind,chars,lo,hi=pattern(s['pattern'])
            if kind=='literal': return [chars]
            maximum=min(hi if hi is not None else 10**9,s.get('maxLength',10**9))
            if maximum>1000 or sum(len(chars)**n for n in range(maximum+1))>100000: raise Limit('finite-domain enumeration cap')
            return [''.join(t) for n in range(maximum+1) for t in itertools.product(chars,repeat=n)]
    for t in s.get('allOf',[]):
        try: return domain(t)
        except Unsupported: pass
    for k in ['oneOf','anyOf']:
        if k in s: return [x for t in s[k] for x in domain(t)]
    raise Unsupported('no finite guard; not is never narrowed to mentioned types')

def generate(schema):
    started=time.process_time()
    try:
        validate_schema(schema);candidates=domain(schema)
        words=sorted({canon(x) for x in candidates if matches(schema,x)})
        states=[{'edges':{},'accept':False}]
        for word in words:
            q=0
            for byte in word:
                edges=states[q]['edges'];key=str(byte)
                if key not in edges:
                    if len(states)>=MAX_STATES: raise Limit('100000 states')
                    edges[key]=len(states);states.append({'edges':{},'accept':False})
                q=edges[key]
            states[q]['accept']=True
            if time.process_time()-started>28: raise Limit('28 CPU seconds')
        # All unspecified byte edges lead to an explicit dead sink.
        sink=len(states)
        if sink>=MAX_STATES: raise Limit('100000 states including sink')
        states.append({'edges':{},'accept':False})
        completion_budget=0
        for q in range(len(states)-1,-1,-1):
            s=states[q]
            if s['accept']: d,w=0,[]
            else:
                options=[(1+states[t]['distance'],[int(b)]+states[t]['completion']) for b,t in s['edges'].items() if states[t].get('distance') is not None]
                d,w=min(options,default=(None,None))
            completion_budget+=len(w) if w is not None else 0
            if completion_budget>2000000:raise Limit('completion evidence budget')
            s['distance'],s['completion']=d,w
        return dict(status='EMPTY' if states[0]['distance'] is None else 'NONEMPTY',states=states,sink=sink,canonical='compact scalar JSON; raw UTF-8; Python JSON escapes; no whitespace',schema_sha256=hashlib.sha256(canon(schema)).hexdigest())
    except UnicodeEncodeError as e: return dict(status='UNSUPPORTED',reason='surrogate')
    except Unsupported as e: return dict(status='UNSUPPORTED',reason=str(e))
    except (Limit,MemoryError) as e: return dict(status='UNKNOWN',reason=str(e))

if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('schema',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();a.out.write_text(json.dumps(generate(json.loads(a.schema.read_text())),ensure_ascii=False,indent=2)+'\n')
