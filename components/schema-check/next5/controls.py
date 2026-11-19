"""Synthetic vocabulary controls are not observations about GPT-2."""
import sys,json,copy,signal,resource,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(59);start=time.process_time()
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent/'next4/schema_check/_engine/next3'))
from generate import generate as byte_generate
from produce import generate,make_trie,query
from verify import check,check_queries
from vocabulary import Limit
c=byte_generate({'enum':['ab','c']});eos=99
pieces={0:b'"ab"',1:b'"',2:b'c'};proof=generate(c,pieces,eos,make_trie(pieces));assert check(c,proof,pieces,eos)['status']=='PASS'
q=query(c,proof,b'',pieces,eos,None);assert q['token_distance']==1 and q['token_completion_ids']==[0] and q['completion_bytes']['length_bytes']==4 and q['byte_distance']==3
complete=query(c,proof,b'"c"',pieces,eos,None);assert complete['token_distance']==0 and complete['completion_with_eos_ids']==[eos];check_queries(c,proof,[q,complete],pieces,eos,None)
short_pieces={0:b'"a'};negative=generate(c,short_pieces,eos,make_trie(short_pieces));v=check(c,negative,short_pieces,eos);assert v['byte_live_token_dead_original_states'];negative_query=query(c,negative,b'',short_pieces,eos,None);assert negative_query['byte_distance'] is not None and negative_query['token_distance'] is None
try:generate(c,pieces,eos,make_trie(pieces),state_cap=2)
except Limit as e:stopped={'status':'UNKNOWN','reason':str(e),'state_cap':2}
else:raise AssertionError('cap was ignored')
mutations={};root=proof['quotient']['start'];target=proof['token_states'][root]['edges'][0]['target']
b=copy.deepcopy(proof);b['token_states'][root]['distance']+=1;mutations['distance']=b
b=copy.deepcopy(proof);b['token_states'][root]['completion']=[1];mutations['token_completion']=b
b=copy.deepcopy(proof);b['token_states'][root]['edges'][0]['count']+=1;mutations['token_transition_group']=b
b=copy.deepcopy(proof);b['quotient']['mapping'][0]=target;mutations['quotient']=b
b=copy.deepcopy(proof);b['token_states'][root]['distance']=True;mutations['boolean_distance']=b
rejected=[]
for name,bad in mutations.items():
    try:check(c,bad,pieces,eos)
    except AssertionError:rejected.append(name)
    else:raise AssertionError(name)
bad=copy.deepcopy(q);bad['token_distance']=8
try:check_queries(c,proof,[bad],pieces,eos,None)
except AssertionError:rejected.append('query_claim')
else:raise AssertionError('query claim')
bad=copy.deepcopy(q);bad['token_distance']=True
try:check_queries(c,proof,[bad],pieces,eos,None)
except AssertionError:rejected.append('boolean_query_distance')
else:raise AssertionError('boolean query distance')
print(json.dumps({'status':'PASS','scope':'synthetic controls only; excluded from GPT-2 counts','shortest_token_can_have_more_bytes_than_shortest_byte':q,'completed_prefix_eos':complete,'byte_live_token_dead_control':negative_query,'state_stop':stopped,'mutations_rejected':rejected,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))
