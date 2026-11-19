"""Fetch only the pinned public tokenizer JSON; refuse hash drift and cap disk usage."""
import json,hashlib,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;s=json.loads((P/'TOKENIZER-SOURCE.json').read_text());root=P.parents[2];target=root/s['path'];env=root/'venvs/schema-check'
if target.exists():
    b=target.read_bytes();assert len(b)==s['bytes'] and hashlib.sha256(b).hexdigest()==s['sha256'],'existing tokenizer does not match pinned bytes'
else:
    used=sum(p.stat().st_size for p in env.rglob('*') if p.is_file()) if env.exists() else 0
    assert used+s['bytes']<1024**3,'tokenizer would exceed 1GiB data budget'
    with urllib.request.urlopen(s['url'],timeout=30) as r:b=r.read(s['bytes']+1)
    assert len(b)==s['bytes'] and hashlib.sha256(b).hexdigest()==s['sha256'],'download did not match pin'
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
print(json.dumps({'status':'PASS','path':str(target),'sha256':s['sha256'],'bytes':len(b),'weights_downloaded':False}))
