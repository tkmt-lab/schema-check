"""Pinned, ordinary-token Metaspace decoder, including its first-token state."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
CAP=500000
class Limit(Exception):pass
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def load(key):
    s=next(s for s in json.loads((P/'TOKENIZERS.json').read_text()) if s['key']==key)
    path=P.parents[2]/s['path'];raw=path.read_bytes()
    assert len(raw)==s['bytes'] and hashlib.sha256(raw).hexdigest()==s['sha256']
    j=json.loads(raw);d=j['decoder'];assert d['type']=='Metaspace' and d['replacement']=='▁' and not j['model'].get('byte_fallback',False)
    assert d.get('add_prefix_space',True) and d.get('prepend_scheme','always')!='never'
    excluded={t['id'] for t in j['added_tokens'] if t['special']}|{j['model']['unk_id']}
    vocab={i:w for i,(w,score) in enumerate(j['model']['vocab']) if i not in excluded}
    first={i:w.replace('▁','').encode() for i,w in vocab.items()}
    later={i:w.replace('▁',' ').encode() for i,w in vocab.items()}
    stop=1 if key=='t5-small' else 3
    return first,later,stop,s,j
def trie(pieces):
    t=[{'e':{},'ids':[]}]
    for i,b in sorted(pieces.items()):
        q=0
        for x in b:
            if x not in t[q]['e']:t[q]['e'][x]=len(t);t.append({'e':{},'ids':[]})
            q=t[q]['e'][x]
        t[q]['ids'].append(i)
    return t
def segment(raw,tries):
    # BFS over (decoder phase, exact byte offset); epsilon first pieces are real tokens.
    from collections import deque
    todo=deque([(0,0)]);paths={(0,0):[]}
    while todo:
        phase,pos=todo.popleft();ids=paths[phase,pos]
        if pos==len(raw):return ids,phase
        t=tries[phase];q=0
        for end in range(pos,len(raw)+1):
            if t[q]['ids'] and (1,end) not in paths:
                paths[1,end]=ids+[min(t[q]['ids'])];todo.append((1,end))
            if end==len(raw) or raw[end] not in t[q]['e']:break
            q=t[q]['e'][raw[end]]
    return None,None
