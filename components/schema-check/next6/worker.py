import sys,json,gzip,time,resource,signal,math
from pathlib import Path
P=Path(__file__).resolve().parent
phase,key,index,outfile,seconds=sys.argv[1],sys.argv[2],int(sys.argv[3]),Path(sys.argv[4]),float(sys.argv[5]);start=time.process_time()
resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(seconds)),max(1,math.ceil(seconds))));signal.alarm(max(1,math.ceil(seconds)))
from vocabulary import load,trie,segment,Limit,digest
first,later,stop,source,j=load(key);pieces=[first,later]
r=json.loads(gzip.decompress((P/'CORPUS.json.gz').read_bytes()))[index];c=r['byte_certificate']
if phase=='produce':
    from produce import generate
    try:
        tries=[trie(x) for x in pieces];proof=generate(c,tries);queries=[];N=len(proof['quotient']['states'])
        for prefix in r['prefixes']:
            raw=bytes(prefix['bytes']);ids,ph=segment(raw,tries);state=0
            for b in raw:state=c['states'][state]['edges'].get(str(b),c['sink'])
            queries.append({'bytes':list(raw),'token_ids':ids,'phase':ph,'byte_state':state,'byte_live':c['states'][state]['distance'] is not None,'token_live':None if ids is None else proof['graph'][ph*N+proof['quotient']['mapping'][state]]['distance'] is not None})
        result={'id':r['id'],'key':key,'status':'COMPLETE','tokenizer_sha256':source['sha256'],'proof':proof,'queries':queries}
    except Limit as e:result={'id':r['id'],'key':key,'status':'UNKNOWN','reason':str(e)}
    outfile.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({'status':result['status'],'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
else:
    def no_producer(event,args):
        if event=='open' and isinstance(args[0],str) and Path(args[0]).name.startswith(('produce.','generate.','nfa_builder.')):raise RuntimeError('producer read blocked')
    sys.addaudithook(no_producer);sys.path.insert(0,str(P.parent/'next4'))
    from schema_check._verify import block_producers
    block_producers();sys.path.insert(0,str(P.parent/'next4/schema_check/_engine/next3'))
    from checker import check as byte_check
    checked=byte_check(r['schema'],c)
    from verify import check
    result=json.loads(outfile.read_text());assert result['key']==key and result['id']==r['id'] and result['tokenizer_sha256']==source['sha256']
    checked2=check(c,result['proof'],pieces);N=len(result['proof']['quotient']['states']);tries=[trie(x) for x in pieces]
    for prefix,qr in zip(r['prefixes'],result['queries'],strict=True):
        raw=bytes(prefix['bytes']);assert qr['bytes']==list(raw);state=0
        for b in raw:state=c['states'][state]['edges'].get(str(b),c['sink'])
        assert qr['byte_state']==state and qr['byte_live']==(c['states'][state]['distance'] is not None)
        ids,ph=segment(raw,tries);assert qr['token_ids']==ids and qr['phase']==ph
        if ids is not None:
            assert b''.join(pieces[0 if i==0 else 1][token] for i,token in enumerate(ids))==raw
            assert qr['token_live']==(result['proof']['graph'][ph*N+result['proof']['quotient']['mapping'][state]]['distance'] is not None)
        else:assert qr['token_live'] is None
    print(json.dumps({'status':'PASS','byte_check':checked,'token_check':checked2,'queries_checked':len(result['queries']),'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
