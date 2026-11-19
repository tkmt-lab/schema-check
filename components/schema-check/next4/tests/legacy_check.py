"""Bounded replay of an original certificate, before frontend normalization."""
import sys,json,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(30)
P=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(P))
from schema_check._verify import block_producers
block_producers();sys.path.insert(0,str(P/'schema_check/_engine/next3'))
from checker import check
r=json.load(sys.stdin);print(json.dumps(check(r['schema'],r['certificate'])))
