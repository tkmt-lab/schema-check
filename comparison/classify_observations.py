"""Annotate frozen case records; do not infer new bugs or execute a backend."""
from pathlib import Path
import json,csv,io,argparse,collections
P=Path(__file__).resolve().parents[1];C=P/'components/schema-check'
TOOLS=[('llguidance','llguidance','1.9.1'),('xgrammar','XGrammar','0.2.8'),('outlines','outlines-core','0.2.14')]
def normalize(s):
 if isinstance(s,dict):s={k:v for k,v in s.items() if k not in ['$schema','$comment','title','description']}
 return json.dumps(s,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def build():
 source=json.loads((P/'comparison/classification-source.json').read_text());index={(r['engine'],normalize(r['schema'])):r for r in source};reported={r['engine']:r for r in json.loads((P/'comparison/reported-issues.json').read_text())}
 supplements={(r['engine'],normalize(r['schema'])):reported[r['engine']] for r in source if r['category']=='D'}
 cases=json.loads((C/'next7/CASES.json').read_text());fails={(r['engine'],r['id']):r for r in json.loads((C/'next7/FAILURES.json').read_text())};rows=[];overview=[]
 for engine,name,version in TOOLS:
  own=[]
  for i,c in enumerate(cases):
   if json.loads((C/'next7/all'/f'{i:03}.json').read_text())['bundle']['support']!='SUPPORTED':continue
   native=json.loads((C/'next7/native'/f'{i:03}.json').read_text())[engine]
   result='COMPILE_REFUSAL' if native['compile_error'] else 'NO_INVALID_ACCEPTANCE_OBSERVED';category='NOT_APPLICABLE';refs=[];family='';classification_key=''
   if (engine,c['id']) in fails:
    result='INVALID_ACCEPTANCE_OBSERVED';old=index[engine,normalize(c['schema'])];classification_key=old['key'];family=old['family'];refs=list(old['references'])
    if old['category']=='A':category='EXISTING_ISSUE_OR_PR'
    elif old['category']=='B':category='OFFICIAL_REPOSITORY_RECORD'
    elif old['category']=='D':category='NEWLY_REPORTED';refs=[reported[engine]['url']]+refs
    else:raise ValueError('unexpected historical category')
   rep=supplements.get((engine,normalize(c['schema'])))
   own.append(dict(project_report=rep['url'] if rep else '',report_witness_in_original_invalid_rows=rep['witness_in_original_invalid_acceptance_rows'] if rep else None,tool=name,engine=engine,version=version,case_id=c['id'],result=result,classification=category,family=family,classification_key=classification_key,references=refs))
  assert len(own)==123
  overview.append(dict(tool=name,version=version,case_records=123,compile_refusals=sum(r['result']=='COMPILE_REFUSAL' for r in own),invalid_acceptance_records=sum(r['result']=='INVALID_ACCEPTANCE_OBSERVED' for r in own),existing_issue_or_pr=sum(r['classification']=='EXISTING_ISSUE_OR_PR' for r in own),official_repository_record=sum(r['classification']=='OFFICIAL_REPOSITORY_RECORD' for r in own),newly_reported_within_saved_invalid_rows=sum(r['classification']=='NEWLY_REPORTED' for r in own)))
  rows+=own
 expected=[(0,0,0,0),(58,46,12,0),(17,16,0,1)]
 assert [tuple(r[k] for k in ['invalid_acceptance_records','existing_issue_or_pr','official_repository_record','newly_reported_within_saved_invalid_rows']) for r in overview]==expected
 data=dict(format='schema-check-observation-map/v1',versions_as_of='2026-11-02',unit='tool/schema records in the original 123-case supported native matrix; not unique bugs',source_classification_commit='fabbe0a73',source_scope='Historical 85-pair union, used only to annotate matching schemas; its totals are not this matrix.',classification_definitions=dict(EXISTING_ISSUE_OR_PR='Related existing upstream issue or PR; mechanism match need not be the identical instance.',OFFICIAL_REPOSITORY_RECORD='Official merged PR/test/warning record; not necessarily a user manual or a warning on every call.',NEWLY_REPORTED='A report newly filed by the project; does not establish novelty or maintainer agreement.'),overview=overview,rows=rows,reported_supplements=list(reported.values()))
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows({**r,'references':' '.join(r['references'])} for r in rows)
 lines=['# Fixed-version observations and their provenance','', 'These results illustrate schema-preservation inspection. They are case records, not a ranking or a count of distinct bugs. Each tool uses the same columns and the same 123 supported reference schemas.','', '|Tool|Version|Case records|Compile refusals|Invalid acceptance records|Existing issue/PR|Official repository record|Newly reported within saved invalid rows|','|---|---|---:|---:|---:|---:|---:|---:|']
 for r in overview:lines.append('|'+ '|'.join(str(r[k]) for k in ['tool','version','case_records','compile_refusals','invalid_acceptance_records','existing_issue_or_pr','official_repository_record','newly_reported_within_saved_invalid_rows'])+'|')
 lines+=['','Zero means no accepted-invalid probe was observed in this fixed set; it is not a proof of backend-language equivalence or general conformance. Compile refusals include correct refusals of empty languages and are not automatically errors. Warnings are preserved.','', '**Existing issue/PR** includes the empty-enum report in Outlines PR #269; it is explicitly a PR, not a fabricated issue number. **Official repository record** includes merged PRs #672, #134 and #670 (warning/fallback behavior); it does not assert that the same limitation appears in a user manual or that every invocation warns. Closed issue status alone does not mean a released version fixed the behavior.','', 'The source annotation snapshot has 85 normalized tool/schema pairs from several saved audits; the table above uses the 123-case native matrix instead. Root annotations are removed only to join provenance. The actual schema, input, runner and observed bytes are unchanged. An issue-family match is not a claim that each exact input had already appeared in the issue.','', '## Newly reported examples','', '|Tool|Fixed version|Report|Witness in the original invalid-acceptance rows?|','|---|---|---|---|']
 for engine,name,version in TOOLS:
  r=reported.get(engine)
  lines.append(f'|{name}|{version}|'+(f"[#{r['issue']}]({r['url']})|{'Yes' if r['witness_in_original_invalid_acceptance_rows'] else 'No: supplemental witness for a schema already in this matrix'}|" if r else 'None (0)|No new report|'))
 lines+=['', 'The XGrammar #1029 schema is already in the 123-case matrix, but its violating value was not in the original probe set. The supplemental witness is not added to the original 58. Outlines #277 is the anyOf/required witness already among the 17. Both reports were filed by the project on 2026-11-02; linking them does not establish bug priority or maintainer confirmation. Their standalone reproducers are in comparison/reports/.','', '## Per-case provenance','', 'The complete 369 tool/schema rows, including all zero-observation and refusal rows, are in [observation-map.csv](../comparison/observation-map.csv) and [observation-map.json](../comparison/observation-map.json). The observed invalid-acceptance rows below link their issue or official record.','', '|Tool|Version|Case|Class|Family|References|','|---|---|---|---|---|---|']
 for r in rows:
  if r['result']=='INVALID_ACCEPTANCE_OBSERVED':lines.append('|'+ '|'.join([r['tool'],r['version'],r['case_id'],r['classification'],r['family'],', '.join(f'[{u.split("/")[-1]}]({u})' for u in r['references'])])+'|')
 return data,s.getvalue(),'\n'.join(lines)+'\n'
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');x=a.parse_args();data,csvtext,md=build();outputs={'comparison/observation-map.json':json.dumps(data,indent=2)+'\n','comparison/observation-map.csv':csvtext,'docs/OBSERVATIONS.md':md}
 for name,text in outputs.items():
  if x.check:assert (P/name).read_text()==text,name+' is stale'
  else:(P/name).write_text(text)
 print(json.dumps(dict(status='PASS',records=len(data['rows']),overview=data['overview'])))
