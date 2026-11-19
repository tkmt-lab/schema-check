import json,sys
from pathlib import Path
from native import worker
P=Path(__file__).resolve().parent
examples={'integer-multiple-rational':b'1','array-unique-impossible':b'[0,1,0]','number-exclusive-empty':b'0'}
name=sys.argv[1];c=next(c for c in json.loads((P/'CASES.json').read_text()) if c['id']==name);c['_mask_trace']=list(examples[name]);r=worker(c)
print(json.dumps(r,ensure_ascii=False,indent=2))
