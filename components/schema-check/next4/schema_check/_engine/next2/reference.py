"""Trusted reference semantics and canonical character encoding, not a DFA solver.
Shared by producer and verifier; this trust boundary is explicit in the report.
"""
import json,re
CAP=100000
class Unsupported(ValueError): pass
class Limit(ValueError): pass

def parse(p):
    if re.fullmatch(r'\^[A-Za-z][*+?]\$',p): p='^['+p[1]+']'+p[2:]
    m=re.fullmatch(r'\^\[([^\]\\^]+)\](\*|\+|\?|\{\d+,(?:\d+)?\}|\{\d+\})\$',p)
    if m:
        chars,q=m.groups();ranges=[];i=0
        while i<len(chars):
            if i+2<len(chars) and chars[i+1]=='-':
                lo,hi=ord(chars[i]),ord(chars[i+2]);i+=3
                if lo>hi: raise Unsupported('invalid range')
            else: lo=hi=ord(chars[i]);i+=1
            if not (hi<0xD800 or lo>0xDFFF): raise Unsupported('surrogate range')
            ranges.append((lo,hi))
        if q=='*': low,high=0,None
        elif q=='+': low,high=1,None
        elif q=='?': low,high=0,1
        else:
            a=q[1:-1].split(',');low=int(a[0]);high=(int(a[-1]) if a[-1] else None)
        if high is not None and high<low: raise Unsupported('invalid repeat')
        return ('class',ranges,low,high)
    if re.fullmatch(r'\^[^\[\]\\.*+?{}()|^$]*\$',p): return ('literal',p[1:-1])
    raise Unsupported('regex outside declared full-anchor fragment')

def string_guard(s):
    if type(s) is bool: return False
    if s.get('type')=='string': return True
    if any(string_guard(t) for t in s.get('allOf',[])): return True
    return any(k in s and all(string_guard(t) for t in s[k]) for k in ['oneOf','anyOf'])

class Semantics:
    def __init__(self,s):
        self.schema=s;self.atoms=[];self.indices={};self.threshold=0;self.bounds={0,0xD800,0xE000,0x110000}
        def atom(a):
            key=json.dumps(a,ensure_ascii=False)
            if key not in self.indices:
                self.indices[key]=len(self.atoms);self.atoms.append(a)
            if a[0]=='literal':
                if any(0xD800<=ord(c)<=0xDFFF for c in a[1]): raise Unsupported('surrogate literal')
                self.threshold=max(self.threshold,len(a[1]))
                for c in a[1]: self.bounds.update([ord(c),ord(c)+1])
            else:
                self.threshold=max(self.threshold,a[2],a[3] or 0)
                for lo,hi in a[1]: self.bounds.update([lo,hi+1])
        def walk(s,depth=0):
            if depth>20: raise Unsupported('depth')
            if type(s) is bool: return
            if not isinstance(s,dict) or set(s)-{'type','pattern','minLength','maxLength','allOf','anyOf','oneOf','not','enum','const','$schema','title','description'}: raise Unsupported('keyword')
            if s.get('$schema','https://json-schema.org/draft/2020-12/schema')!='https://json-schema.org/draft/2020-12/schema': raise Unsupported('dialect')
            if 'type' in s and s['type'] not in ['string','boolean','null']: raise Unsupported('type')
            for k in ['minLength','maxLength']:
                if k in s:
                    n=s[k]
                    if type(n) not in [int,float] or n<0 or n!=int(n): raise Unsupported('length')
                    self.threshold=max(self.threshold,int(n))
            if 'pattern' in s: atom(parse(s['pattern']))
            for x in s.get('enum',[])+([s['const']] if 'const' in s else []):
                if x is not None and type(x) not in [str,bool,int]: raise Unsupported('enum scalar')
                if isinstance(x,str): atom(('literal',x))
            for k in ['allOf','anyOf','oneOf']:
                if k in s:
                    if not isinstance(s[k],list) or not s[k]: raise Unsupported('applicator')
                    for t in s[k]: walk(t,depth+1)
            if 'not' in s: walk(s['not'],depth+1)
        walk(s)
        if not string_guard(s): raise Unsupported('no necessary string guard')
        if self.threshold>=CAP: raise Limit('character states > cap')
        self.saturation=self.threshold+1
        b=sorted(self.bounds)
        self.categories=[(lo,hi-1) for lo,hi in zip(b,b[1:]) if not 0xD800<=lo<0xE000]
    def initial(self): return (0,)+tuple(0 for _ in self.atoms)
    def step(self,state,cp):
        count=min(state[0]+1,self.saturation);parts=[]
        for a,k in zip(self.atoms,state[1:]):
            if a[0]=='literal':
                text=a[1];parts.append(k+1 if k<len(text) and ord(text[k])==cp else len(text)+1)
            else: parts.append(int(bool(k) or not any(lo<=cp<=hi for lo,hi in a[1])))
        return (count,)+tuple(parts)
    def accepts(self,state):
        n=state[0]
        def atom(a):
            k=state[1+self.indices[json.dumps(a,ensure_ascii=False)]]
            return k==len(a[1]) if a[0]=='literal' else not k and n>=a[2] and (a[3] is None or n<=a[3])
        def test(s):
            if type(s) is bool: return s
            if 'type' in s and s['type']!='string': return False
            if n<s.get('minLength',0) or n>s.get('maxLength',float('inf')): return False
            if 'pattern' in s and not atom(parse(s['pattern'])): return False
            if 'const' in s and not (isinstance(s['const'],str) and atom(('literal',s['const']))): return False
            if 'enum' in s and not any(isinstance(x,str) and atom(('literal',x)) for x in s['enum']): return False
            if any(not test(t) for t in s.get('allOf',[])): return False
            if 'anyOf' in s and not any(test(t) for t in s['anyOf']): return False
            if 'oneOf' in s and sum(test(t) for t in s['oneOf'])!=1: return False
            return not ('not' in s and test(s['not']))
        return test(self.schema)

def lexboxes(a,b):
    if not a: return [()]
    if a[0]==b[0]: return [((a[0],a[0]),)+x for x in lexboxes(a[1:],b[1:])]
    out=[((a[0],a[0]),)+x for x in lexboxes(a[1:],[0xBF]*len(a[1:]))]
    if a[0]+1<b[0]: out.append(((a[0]+1,b[0]-1),)+((0x80,0xBF),)*len(a[1:]))
    out += [((b[0],b[0]),)+x for x in lexboxes([0x80]*len(a[1:]),b[1:])]
    return out

def charboxes(lo,hi):
    # Disjoint normal-form encodings; JSON syntax quote is not a character.
    out=[]
    for cp in range(max(lo,0),min(hi,0x7F)+1):
        raw=json.dumps(chr(cp),ensure_ascii=False)[1:-1].encode()
        out.append(tuple((x,x) for x in raw))
    for left,right in [(0x80,0x7FF),(0x800,0xD7FF),(0xE000,0xFFFF),(0x10000,0x10FFFF)]:
        a,b=max(lo,left),min(hi,right)
        if a<=b: out.extend(lexboxes(list(chr(a).encode()),list(chr(b).encode())))
    return out
