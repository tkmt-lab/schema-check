"""Finite semantic features for exact canonical decimal numeric languages.

Shared reference transitions, not a certificate producer. No floats, truncation
of numeric magnitude, or forced digit bound. Length/comparison features saturate
only after comparison with every finite schema constant is already decided.
"""
from extended import rat,decimal,number,Unsupported,Limit,CAP
def numeric_guard(s):
    if type(s)is bool:return s is False
    ts=s.get('type');ts=ts if isinstance(ts,list) else [ts]
    if ts and all(t in ['number','integer'] for t in ts):return True
    if 'const'in s:return number(s['const'])
    if 'enum'in s:return all(number(x) for x in s['enum'])
    if any(numeric_guard(t) for t in s.get('allOf',[])):return True
    return any(k in s and all(numeric_guard(t) for t in s[k]) for k in ['anyOf','oneOf'])
class Model:
    def __init__(self,s):
        if not numeric_guard(s):raise Unsupported('no necessary numeric type guard')
        self.s=s;constants=set();multiples=set()
        def walk(t):
            if type(t)is bool:return
            for k in ['minimum','maximum','exclusiveMinimum','exclusiveMaximum']:
                if k in t:constants.add(rat(t[k]))
            for v in t.get('enum',[])+([t['const']] if 'const'in t else []):
                if number(v):constants.add(rat(v))
            if 'multipleOf'in t:multiples.add(rat(t['multipleOf']))
            for k in ['allOf','anyOf','oneOf']:
                for child in t.get(k,[]):walk(child)
            if 'not'in t:walk(t['not'])
        walk(s);self.constants=sorted(constants);self.index={v:i for i,v in enumerate(self.constants)}
        self.ip=[];self.fp=[]
        for v in self.constants:
            w=format(decimal(abs(v)),'f');a,_,b=w.partition('.');self.ip.append(a);self.fp.append(b)
        self.imax=max(map(len,self.ip),default=1);self.fmax=max(map(len,self.fp),default=0)
        self.mult=sorted(multiples);self.mod=[]
        for v in self.mult:
            w=format(decimal(v),'f');a,_,b=w.partition('.');scale=len(b);mod=int(a+b)
            if mod>CAP or scale>4096:raise Limit('numeric modulus/precision cap')
            self.mod.append((mod,scale))
    def initial(self):return ('start',False,0,tuple(0 for _ in self.ip),0,tuple(0 for _ in self.fp),tuple(0 for _ in self.mod))
    def step(self,state,b):
        if state is None:return None
        mode,neg,ilen,ci,flen,cf,rems=state
        if b==45 and mode=='start':return ('minus',True,0,ci,0,cf,rems)
        if b==46 and mode in ['izero','int']:return ('dot',neg,ilen,ci,0,cf,rems)
        if not 48<=b<=57:return None
        digit=b-48
        if mode in ['start','minus','int']:
            if mode in ['start','minus']:nmode='izero' if digit==0 else 'int'
            else:nmode='int'
            ci=tuple(c if c else (digit>int(w[ilen]))-(digit<int(w[ilen])) if ilen<len(w) else c for c,w in zip(ci,self.ip))
            ilen=min(ilen+1,self.imax+1)
        elif mode in ['dot','fzero','frac']:
            nmode='fzero' if digit==0 else 'frac'
            cf=tuple(c if c else (digit>int(w[flen] if flen<len(w) else '0'))-(digit<int(w[flen] if flen<len(w) else '0')) for c,w in zip(cf,self.fp))
            flen=min(flen+1,max(self.fmax,max((scale for mod,scale in self.mod),default=0))+1)
        else:return None
        rems=tuple((r*10+digit)%mod for r,(mod,scale) in zip(rems,self.mod))
        return (nmode,neg,ilen,ci,flen,cf,rems)
    def features(self,state):
        if state is None:return None
        mode,neg,ilen,ci,flen,cf,rems=state
        if mode not in ['izero','int','frac'] or mode=='izero' and neg:return None
        fractional=mode=='frac';comparisons=[]
        for i,v in enumerate(self.constants):
            if neg and v>=0:cmp=-1
            elif not neg and v<0:cmp=1
            else:
                cmp=(ilen>len(self.ip[i]))-(ilen<len(self.ip[i])) if ilen!=len(self.ip[i]) else ci[i]
                if cmp==0:
                    cmp=cf[i]
                    # Remaining unseen bound digits are compared against implicit zero.
                    if cmp==0 and any(c!='0' for c in self.fp[i][flen:]):cmp=-1
                if neg:cmp=-cmp
            comparisons.append(cmp)
        divisible=[]
        for r,(mod,scale) in zip(rems,self.mod):
            divisible.append(flen<=scale and (r*pow(10,scale-flen,mod))%mod==0)
        return fractional,comparisons,divisible
    def accept(self,state):
        f=self.features(state)
        if f is None:return False
        fractional,cs,ds=f
        def cmp(v):return cs[self.index[rat(v)]]
        def evaluate(s):
            if type(s)is bool:return s
            ts=s.get('type');ts=ts if isinstance(ts,list) else [ts] if ts else ['number']
            if not any(t=='number' or t=='integer' and not fractional for t in ts):return False
            if 'enum'in s and not any(number(v) and cmp(v)==0 for v in s['enum']):return False
            if 'const'in s and not (number(s['const']) and cmp(s['const'])==0):return False
            if 'minimum'in s and cmp(s['minimum'])<0 or 'maximum'in s and cmp(s['maximum'])>0:return False
            if 'exclusiveMinimum'in s and cmp(s['exclusiveMinimum'])<=0 or 'exclusiveMaximum'in s and cmp(s['exclusiveMaximum'])>=0:return False
            if 'multipleOf'in s and not ds[self.mult.index(rat(s['multipleOf']))]:return False
            if any(not evaluate(t) for t in s.get('allOf',[])):return False
            if 'anyOf'in s and not any(evaluate(t) for t in s['anyOf']):return False
            if 'oneOf'in s and sum(evaluate(t) for t in s['oneOf'])!=1:return False
            return not ('not'in s and evaluate(s['not']))
        return bool(evaluate(self.s))
