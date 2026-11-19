"""A single bounded phase: producing and verifying are different processes."""
import sys,json,gzip,time,resource,signal,math
from pathlib import Path
P=Path(__file__).resolve().parent
phase,index,outfile,seconds=sys.argv[1],int(sys.argv[2]),Path(sys.argv[3]),float(sys.argv[4]);start=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(seconds)),max(1,math.ceil(seconds))));signal.alarm(max(1,math.ceil(seconds)))
if sys.platform.startswith('linux'):resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
from vocabulary import load,Limit,digest
corpus=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()));r=corpus[index];c=r['byte_certificate'];pieces,eos,fallback,source=load()
if phase=='produce':
    from produce import generate,make_trie,query
    try:
        trie=make_trie(pieces);proof=generate(c,pieces,eos,trie)
        queries=[query(c,proof,bytes(p['bytes']),pieces,eos,fallback) for p in r['prefixes']]
        result={'id':r['id'],'status':'COMPLETE','tokenizer_sha256':source['sha256'],'byte_input_id':r['id'],'proof':proof,'queries':queries}
    except Limit as e:result={'id':r['id'],'status':'UNKNOWN','reason':str(e)}
    result['cpu_seconds']=time.process_time()-start;result['rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    outfile.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n');print(json.dumps({'id':r['id'],'status':result['status']}))
else:
    def no_producer(event,args):
        if event=='open' and isinstance(args[0],str) and Path(args[0]).name.startswith(('produce.','generate.','nfa_builder.')):raise RuntimeError('producer read blocked')
    sys.addaudithook(no_producer)
    sys.path.insert(0,str(P.parent/'next4'))
    from schema_check._verify import block_producers
    block_producers();sys.path.insert(0,str(P.parent/'next4/schema_check/_engine/next3'))
    from checker import check as byte_check
    checked_byte=byte_check(r['schema'],c)
    from verify import check,check_queries
    result=json.loads(outfile.read_text());assert result['id']==r['id'] and result['tokenizer_sha256']==source['sha256']
    proof=result['proof'];checked=check(c,proof,pieces,eos);n=check_queries(c,proof,result['queries'],pieces,eos,fallback)
    print(json.dumps({'id':r['id'],'status':'PASS','byte_check':checked_byte,'token_check':checked,'queries_checked':n,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
