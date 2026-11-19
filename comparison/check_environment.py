"""Read distribution versions only; explicit version files allow a separate update run."""
import importlib.metadata as m,json,pathlib,argparse
P=pathlib.Path(__file__).resolve().parent
reference=dict(line.strip().split('==') for line in (P/'requirements.txt').read_text().splitlines() if line.strip())
a=argparse.ArgumentParser();a.add_argument('--versions-file',type=pathlib.Path);x=a.parse_args()
expected=json.loads(x.versions_file.read_text()) if x.versions_file else reference
if set(expected)!=set(reference) or not all(isinstance(v,str) and v for v in expected.values()):a.error('version file must explicitly name all seven distributions with nonempty version strings')
got={}
for name in expected:
 try:got[name]=m.version(name)
 except m.PackageNotFoundError:got[name]=None
print(json.dumps(dict(status='PASS' if got==expected else 'FAIL',expected=expected,installed=got,scope='metadata only; no source/wheel equivalence attestation'),indent=2))
raise SystemExit(0 if got==expected else 1)
