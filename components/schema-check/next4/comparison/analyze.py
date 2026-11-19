import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"schema_check/_engine/next3"))
from finite_semantics import valid,canonical,Unsupported
P=Path(__file__).resolve().parent
rr=json.loads((P/'RESULTS.json').read_text());cc=json.loads((P/'CASES.json').read_text())
assert len(rr)==len(cc),('unfinished',len(rr),len(cc))
assert not any('worker_error'in r for r in rr)
out={};failures=[]
for engine in ['llguidance','outlines','xgrammar']:
    fa=[];fr=[];decl=[];dead=[];empty=[]
    for r,c in zip(rr,cc):
        if r['ours']['status']not in ['EMPTY','NONEMPTY']:continue
        e=r[engine]
        if e['compile_error']:decl.append({'id':r['id'],'messages':e.get('messages',[])});continue
        bad=[]
        for p in e['prefixes']:
            if p['admitted'] and not p['accepting'] and not p['allowed']:dead.append({'id':r['id'],'bytes':p['bytes']})
            if p['accepting']:
                try:okay=valid(c['schema'],json.loads(bytes(p['bytes'])))
                except (ValueError,UnicodeDecodeError):okay=False
                if not okay:bad.append(p['bytes'])
        if bad:
            fa.append({'id':r['id'],'examples':bad})
            b=bad[0];proof=next(p for p in r['prefixes'] if p['bytes']==b)
            failures.append({'engine':engine,'id':r['id'],'source':c.get('source'),'schema':c['schema'],'bytes':b,'json_text':bytes(b).decode(),'our_prefix':proof,'worker_stderr':r['stderr']})
        if r['ours']['status']=='EMPTY' and bad:empty.append(r['id'])
        for t in c['tests']:
            if not t['valid']:continue
            try:raw=canonical(t['data'])
            except Unsupported:continue
            row=next((p for p in e['prefixes'] if p['bytes']==list(raw)),None)
            if row and not row['accepting']:fr.append({'id':r['id'],'bytes':list(raw)})
    out[engine]={'false_accept_schemas':fa,'compile_errors':decl,'observed_empty_masks':dead,'empty_schema_with_invalid_acceptance':empty,'canonical_valid_fixture_rejections':fr}
out['ours']={k:{s:sum(r['kind']==k and r['ours']['status']==s for r in rr) for s in ['EMPTY','NONEMPTY','UNSUPPORTED','UNKNOWN']} for k in sorted({r['kind'] for r in rr})}
out['resources']={'sum_worker_cpu':sum(r['cpu'] for r in rr),'max_case_cpu':max(r['cpu'] for r in rr),'max_case_wall':max(r['wall'] for r in rr),'max_case_rss':max(r['rss_bytes'] for r in rr),'max_dfa_states':max(len(r['ours'].get('states',[])) for r in rr)}
(P/'SUMMARY.json').write_text(json.dumps(out,indent=2)+'\n');(P/'FAILURES.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n')
for e in ['llguidance','outlines','xgrammar']:print(e,{k:len(v) for k,v in out[e].items()})
