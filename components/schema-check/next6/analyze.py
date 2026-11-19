import json,gzip,csv
from pathlib import Path
from vocabulary import load
P=Path(__file__).resolve().parent;corpus=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()));summaries=[]
for key in ['t5-small','albert-base-v2']:
    first,later,stop,s,j=load(key);records=[];examples=[]
    runs=json.loads((P/key/'ALL-RUN.json').read_text());assert len(runs)==len(corpus)==83 and all(r['status']=='PASS' for r in runs)
    for i,r in enumerate(corpus):
        x=json.loads((P/key/f'all/{i:03}.json').read_text());p=x['proof'];N=len(p['quotient']['states']);root=p['graph'][p['quotient']['start']]['distance'];c=r['byte_certificate']
        ds=p['dead_reachable_indices'];prefix_witnesses=[]
        for d in ds:
            ids=[];t=d
            while p['reachable'][t]['parent'] is not None:
                ids.append(p['reachable'][t]['token']);t=p['reachable'][t]['parent']
            ids.reverse();raw=b''.join((first if k==0 else later)[tok] for k,tok in enumerate(ids));rr=p['reachable'][d]
            assert raw or not ids or all(not first[t] for t in ids)
            examples.append({'key':key,'id':r['id'],'reachable_index':d,'phase':rr['phase'],'byte_state':rr['state'],'token_prefix_ids':ids,'prefix_hex':raw.hex(),'prefix_utf8':raw.decode(),
                 'byte_completion':c['states'][rr['state']]['completion'],'byte_distance':c['states'][rr['state']]['distance'],'root_token_live':root is not None})
            prefix_witnesses.append(raw)
        queries=x['queries'];deadq=[q for q in queries if q['byte_live'] and q['token_ids'] is not None and q['token_live'] is False]
        record={'id':r['id'],'byte_nonempty':c['states'][0]['distance'] is not None,'root_token_live':root is not None,'reachable_product_states':len(p['reachable']),
            'reachable_dead_product_states':len(ds),'distinct_original_dead_states':len({p['reachable'][d]['state'] for d in ds}),
            'dead_states_with_nonempty_emitted_witness':sum(bool(b) for b in prefix_witnesses),'root_viable_with_reachable_dead_state':bool(root is not None and ds),
            'recorded_prefixes':len(queries),'recorded_byte_live_prefixes':sum(q['byte_live'] for q in queries),
            'recorded_byte_live_tokenizable_prefixes':sum(q['byte_live'] and q['token_ids'] is not None for q in queries),
            'recorded_byte_live_untokenizable_prefixes':sum(q['byte_live'] and q['token_ids'] is None for q in queries),
            'recorded_reachable_dead_prefixes':len(deadq),'recorded_nonempty_reachable_dead_prefixes':sum(bool(q['bytes']) for q in deadq),
            'retained_peak_states_arcs':p['resources']['retained_peak_states_arcs']}
        records.append(record)
    totals={k:sum(int(r[k]) for r in records) for k in records[0] if k not in ['id','retained_peak_states_arcs']}
    totals.update(key=key,schemas=83,schemas_with_reachable_dead_states=sum(bool(r['reachable_dead_product_states']) for r in records),
       root_byte_live_token_dead_schemas=sum(r['byte_nonempty'] and not r['root_token_live'] for r in records),
       all_pass=True,unknown=0,max_retained_states_arcs=max(r['retained_peak_states_arcs'] for r in records),
       cpu_seconds_with_monitor=sum(r['cpu_seconds_with_monitor'] for r in runs),max_case_cpu_seconds=max(r['cpu_seconds_with_monitor'] for r in runs),
       max_case_wall_seconds=max(r['wall_seconds'] for r in runs),max_rss_bytes=max(max(ph['rss_monitored_bytes'],ph['rss_bytes']) for r in runs for ph in r['phases']))
    summaries.append(totals)
    (P/key/'SUMMARY.json').write_text(json.dumps({'totals':totals,'cases':records,'dead_state_witnesses':examples},ensure_ascii=False,indent=2)+'\n')
    with (P/key/'TABLE.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');writer.writeheader();writer.writerows(records)
(P/'SUMMARY.json').write_text(json.dumps(summaries,indent=2)+'\n');print(json.dumps(summaries,indent=2))
