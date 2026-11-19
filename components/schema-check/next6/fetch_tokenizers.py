"""Fetch only the pinned public tokenizer JSONs. Never fetch weights/configs."""
import json,hashlib,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;root=P.parents[2]
for s in json.loads((P/'TOKENIZERS.json').read_text()):
    path=root/s['path']
    if path.exists():raw=path.read_bytes()
    else:
        with urllib.request.urlopen(s['url'],timeout=30) as response:raw=response.read(8*1024**2+1)
        assert len(raw)<=8*1024**2
        assert sum(f.stat().st_size for f in (root/'venvs/schema-check').rglob('*') if f.is_file())+len(raw)<1024**3
    assert len(raw)==s['bytes'] and hashlib.sha256(raw).hexdigest()==s['sha256']
    if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print(s['key'],s['sha256'])
