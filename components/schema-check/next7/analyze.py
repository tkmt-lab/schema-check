import sys,json,csv
from pathlib import Path
from collections import Counter
from decimal import Decimal
P=Path(__file__).resolve().parent;sys.path[:0]=[str(P),str(P/'schema_check/_engine/next7')]
from schema_check._shared import load_json,parse_schema
from extended import valid
cases=json.loads((P/'CASES.json').read_text());runs=json.loads((P/'ALL-RUN.json').read_text());assert len(runs)==len(cases)==214 and all(r['status']=='PASS' for r in runs)
old={r['id']:r for r in json.loads((P.parent/'next3/RESULTS.json').read_text())};rows=[];failures=[];tools={e:{'all':[],'new_eligible':[],'compile_errors':[],'empty_language_acceptance':[],'malformed_json_acceptance':[]} for e in ['llguidance','xgrammar','outlines']}
coverage={}
for i,c in enumerate(cases):
    x=load_json((P/'all'/f'{i:03d}.json').read_text());b=x['bundle'];support=b['support'];status=b['certificate']['status'] if support=='SUPPORTED' else support
    coverage.setdefault(c['scope'],Counter())[status]+=1
    newly=support=='SUPPORTED' and (c['id']not in old or old[c['id']]['ours']['status']not in ['EMPTY','NONEMPTY'])
    row={'id':c['id'],'scope':c['scope'],'status':status,'newly_eligible':newly,'states':len(b['certificate']['states']) if support=='SUPPORTED' else 0}
    if support=='SUPPORTED':
        native=json.loads((P/'native'/f'{i:03d}.json').read_text());s=parse_schema(json.dumps(c['schema']))
        for e in tools:
            t=native[e];bad=[];semantic=[];malformed=[]
            if t['compile_error']:tools[e]['compile_errors'].append(c['id']);row[e]='COMPILE_REFUSAL';continue
            for q in t['prefixes']:
                if not q['accepting']:continue
                try:
                    value=json.loads(bytes(q['bytes']),parse_float=Decimal);good=valid(s,value)
                    if not good:semantic.append(q['bytes'])
                except (ValueError,UnicodeDecodeError):good=False;malformed.append(q['bytes'])
                if not good:bad.append(q['bytes'])
            row[e]='FALSE_ACCEPT' if bad else 'NO_OBSERVED_ERROR'
            if bad:
                tools[e]['all'].append(c['id'])
                if newly:tools[e]['new_eligible'].append(c['id'])
                if b['language']['empty']:tools[e]['empty_language_acceptance'].append(c['id'])
                if malformed:tools[e]['malformed_json_acceptance'].append(c['id'])
                failures.append({'id':c['id'],'scope':c['scope'],'newly_eligible':newly,'engine':e,'empty_language':b['language']['empty'],'semantic_false_acceptances':semantic,'malformed_acceptances':malformed,'schema':c['schema']})
    rows.append(row)
summary={'coverage':coverage,'supported':sum(r['status']in ['EMPTY','NONEMPTY'] for r in rows),'newly_eligible':sum(r['newly_eligible'] for r in rows),'tools':tools,
    'resources':{'total_case_cpu_with_monitor':sum(r['cpu_seconds_with_monitor'] for r in runs),'max_case_cpu':max(r['cpu_seconds_with_monitor'] for r in runs),'max_case_wall':max(r['wall_seconds'] for r in runs),'max_rss_bytes':max(max(ph.get('monitored_rss_bytes',0),ph.get('rss_bytes',0)) for r in runs for ph in r['phases']),'max_byte_states':max(r['states'] for r in rows)}}
(P/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(P/'FAILURES.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n')
with (P/'TABLE.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=['id','scope','status','newly_eligible','states','llguidance','xgrammar','outlines'],lineterminator='\n');w.writeheader();w.writerows(rows)
print(json.dumps({**{k:v for k,v in summary.items() if k!='tools'},'tool_counts':{e:{k:len(v) for k,v in t.items()} for e,t in tools.items()}},indent=2))
