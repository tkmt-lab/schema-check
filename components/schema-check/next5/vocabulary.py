"""Fixed GPT-2 ByteLevel bytes before UTF-8 loss replacement; no model or encoder call."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
CAP=500000
class Limit(ValueError):pass
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def load():
    source=json.loads((P/'TOKENIZER-SOURCE.json').read_text());path=P.parents[2]/source['path'];raw=path.read_bytes()
    assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
    j=json.loads(raw);assert j['decoder']['type']=='ByteLevel' and j['normalizer'] is None
    assert not j['model'].get('continuing_subword_prefix') and not j['model'].get('end_of_word_suffix')
    base=list(range(33,127))+list(range(161,173))+list(range(174,256));chars=base.copy();n=0
    for b in range(256):
        if b not in base:base.append(b);chars.append(256+n);n+=1
    inverse={chr(c):b for b,c in zip(base,chars)}
    special={t['id'] for t in j['added_tokens'] if t['special']};assert special=={50256}
    pieces={i:bytes(inverse[c] for c in token) for token,i in j['model']['vocab'].items() if i not in special}
    assert len(pieces)==50256 and all(pieces.values())
    fallback={v[0]:i for i,v in pieces.items() if len(v)==1};assert set(fallback)==set(range(256))
    return pieces,50256,fallback,source
def bytes_word(raw):
    try:text=raw.decode('utf-8')
    except UnicodeDecodeError:text=None
    return {'bytes':list(raw),'hex':raw.hex(),'utf8':text,'length_bytes':len(raw)}
