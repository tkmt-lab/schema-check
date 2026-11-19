"""Producer-only NFA construction, split from the trusted meaning kernel."""
from reference import Semantics,charboxes,Limit,CAP

def make_nfa(s):
    sem=Semantics(s);states=[sem.initial()];index={states[0]:0};trans=[];accept=[]
    for st in states:
        row=[];accept.append(sem.accepts(st))
        for lo,hi in sem.categories:
            nxt=sem.step(st,lo)
            if nxt not in index:
                if len(states)>=CAP: raise Limit('character cap')
                index[nxt]=len(states);states.append(nxt)
            row.append(index[nxt])
        trans.append(row)
    # NFA 0 = opening quote, 1 = terminal, character boundary i = i+2.
    nfa=[{} for _ in range(len(states)+2)];final={1};cache={}
    descriptions=[['initial'],['terminal']]+[['boundary',i] for i in range(len(states))]
    def edge(q,lo,hi,t):
        for b in range(lo,hi+1): nfa[q].setdefault(b,set()).add(t)
    def suffix(boxes,target):
        if not boxes: return target
        key=(boxes,target)
        if key not in cache:
            if len(nfa)>=CAP: raise Limit('byte NFA cap')
            q=len(nfa);cache[key]=q;nfa.append({});descriptions.append(['suffix',boxes,target])
            t=suffix(boxes[1:],target);edge(q,*boxes[0],t)
        return cache[key]
    edge(0,34,34,2)
    for i,row in enumerate(trans):
        if accept[i]: edge(i+2,34,34,1)
        for (lo,hi),j in zip(sem.categories,row):
            for box in charboxes(lo,hi): edge(i+2,*box[0],suffix(box[1:],j+2))
    return nfa,final,{'character_states':len(states),'nfa_states':len(nfa),'unicode_categories':sem.categories,'character_labels':states,'nfa_descriptions':descriptions}
