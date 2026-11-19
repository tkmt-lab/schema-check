import json,gzip
from pathlib import Path
P=Path(__file__).resolve().parent;corpus=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()));run=json.loads((P/'ALL-RUN.json').read_text())
assert len(run)==len(corpus)==83
roots=[];mismatch_ids=[];old_live=0;old_states=0;live_prefixes=0;prefixes=0;token_states=0;peaks=[];visits=[];unknown=[];examples=[]
for record,c in zip(run,corpus):
    assert record['id']==c['id']
    if record['status']!='PASS':unknown.append({'id':record['id'],'reason':record['reason']});continue
    result=json.loads((P/'all'/f'{record["index"]:03d}.json').read_text());proof=result['proof'];graph=proof['token_states'];q=proof['quotient'];old=c['byte_certificate'];checks=record['phases'][-1]['token_check'];assert not checks['byte_live_token_dead_original_states']
    dead=[i for i,n in enumerate(old['states']) if n['distance'] is not None and graph[q['mapping'][i]]['distance'] is None]
    if dead:mismatch_ids.append(c['id'])
    old_states+=len(old['states']);old_live+=sum(n['distance'] is not None for n in old['states']);token_states+=len(graph)
    prefixes+=len(result['queries']);live_prefixes+=sum(r['byte_distance'] is not None for r in result['queries'])
    peaks.append(proof['resources']['peak_retained_states_and_arcs']);visits.append(proof['resources']['lexical_pair_visits'])
    root=next(r for r in result['queries'] if not r['prefix']['bytes']);roots.append({'id':c['id'],'byte_distance':root['byte_distance'],'token_distance':root['token_distance'],'completion_token_ids':root['token_completion_ids'],'completion_utf8':root['completion_bytes']['utf8'] if root['completion_bytes'] else None})
    if c['id'] in ['issue-xg858-original','issue-xg895-original','infinite-not','suite3-const-10','pattern-length']:examples.append({'id':c['id'],'resources':proof['resources'],'root':root})
native=json.loads((P/'NATIVE.json').read_text());native_rows=[r for r in native['rows'] if 'tools' in r]
tool_counts={}
for name in ['llguidance','xgrammar','outlines']:
    rows=[r for r in native_rows if name in r['tools']];live=[r for r in rows if r['our_byte_and_token_live']]
    tool_counts[name]={'probe_rows':len(rows),'byte_and_token_live_probe_rows':len(live),'live_prefix_rejections':sum(not r['tools'][name]['admitted'] for r in live),'empty_masks_nonterminal':sum(r['tools'][name]['empty_mask_nonterminal'] for r in rows),'ff_token_allowed_rows':sum(r['tools'][name]['ff_fallback_allowed'] for r in rows),'our_byte_dead_but_backend_admitted':sum(not r['our_byte_and_token_live'] and r['tools'][name]['admitted'] for r in rows)}
result={'status':'PASS' if not unknown else 'PARTIAL','schemas':83,'complete':83-len(unknown),'unknown':unknown,'root_nonempty':sum(r['token_distance'] is not None for r in roots),'byte_live_token_dead_schema_count':len(mismatch_ids),'mismatch_schema_ids':mismatch_ids,'original_byte_states_checked':old_states,'original_byte_live_states_checked':old_live,'quotient_token_states_checked':token_states,'prefixes_checked':prefixes,'byte_live_prefixes_checked':live_prefixes,'max_retained_states_and_arcs':max(peaks),'max_lexical_pair_visits':max(visits),'total_case_cpu_seconds':sum(r['cpu_seconds_with_monitor'] for r in run),'max_case_cpu_seconds':max(r['cpu_seconds_with_monitor'] for r in run),'max_case_wall_seconds':max(r['wall_seconds'] for r in run),'max_monitored_rss_bytes':max(p['rss_monitored_bytes'] for r in run for p in r['phases']),'native':tool_counts,'root_results':roots}
(P/'SUMMARY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(P/'EXAMPLES.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='root_results'},indent=2))
