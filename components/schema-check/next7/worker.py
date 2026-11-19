import sys,json,time,resource,signal
from pathlib import Path
P=Path(__file__).resolve().parent
phase,index,seconds=sys.argv[1],int(sys.argv[2]),float(sys.argv[3]);start=time.process_time()
import math
resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(seconds)),max(1,math.ceil(seconds))));signal.alarm(max(1,math.ceil(seconds)))
sys.path[:0]=[str(P),str(P/'schema_check/_engine/next7')]
from schema_check._shared import parse_schema,dumps,sha,Failure,failure
cases=json.loads((P/'CASES.json').read_text());c=cases[index];schema_text=json.dumps(c['schema'],ensure_ascii=False)
out=P/'all'/f'{index:03d}.json'
if phase=='produce':
    from generate import generate
    from schema_check._format import project
    from schema_check._shared import failure
    try:
        s=parse_schema(schema_text);cert=generate(s)
        bundle=project(s,sha(schema_text.encode()),[],True,cert) if cert['status']in ['EMPTY','NONEMPTY'] else failure(cert['status'],cert.get('reason',cert.get('next3_reason','unsupported')))
    except Failure as e:cert={'status':e.kind};bundle=failure(e.kind,e.reason)
    out.write_text(dumps({'id':c['id'],'scope':c['scope'],'bundle':bundle})+'\n')
    result={'status':cert['status'],'states':len(cert.get('states',[]))}
elif phase=='verify':
    from schema_check._shared import load_json
    from schema_check._verify import verify
    # Audit installed before certificate checker import, in a separate process.
    from schema_check._verify import block_producers
    block_producers();r=load_json(out.read_text());b=r['bundle']
    if b['support']=='SUPPORTED':
        result=verify(b,schema_text)
        from checker import prefix
        from extended import canonical,valid
        for t in c['tests']:
            assert prefix(b['certificate'],canonical(t['data']))['accepting']==t['valid'],(c['id'],t)
        result['fixtures_checked']=len(c['tests'])
    else:result={'status':b['support'],'not_applicable':True}
elif phase=='native':
    from native import worker
    result=worker(c);(P/'native'/f'{index:03d}.json').write_text(json.dumps(result,ensure_ascii=False)+'\n');result={'status':'RECORDED'}
else:raise ValueError(phase)
result.update(cpu_seconds=time.process_time()-start,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);print(json.dumps(result))
