"""Preflight only: never download a tokenizer/model or execute an inference backend."""
import importlib.metadata as m,json,sys
expected={'llguidance':'1.9.1','outlines-core':'0.2.14','xgrammar':'0.2.8','torch':'2.15.0'}
got={}
for name in expected:
    try:got[name]=m.version(name)
    except m.PackageNotFoundError:got[name]=None
okay=got==expected
print(json.dumps({'status':'PASS' if okay else 'FAIL','expected':expected,'installed':got,'scope':'package metadata, not a binary/source-build attestation'},indent=2))
raise SystemExit(0 if okay else 1)
