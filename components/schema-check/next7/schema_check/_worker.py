"""Private isolated process used by both public commands."""
import sys,json,resource,signal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from schema_check._shared import Failure,failure,parse_schema,sha,dumps,load_json

def main():
    if not __debug__:raise RuntimeError('verification assertions must be enabled')
    resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(30)
    if sys.platform.startswith('linux'):resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    request=json.load(sys.stdin);mode=request['mode']
    try:
        if mode=='verify':
            from schema_check._verify import verify
            result=verify(load_json(request['artifact']),request.get('external_schema'))
        else:
            schema=parse_schema(request['schema']);engine=Path(__file__).resolve().parent/'_engine/next7';sys.path.insert(0,str(engine))
            from generate import generate
            c=generate(schema)
            if c['status'] not in ['EMPTY','NONEMPTY']:result=failure(c['status'],c.get('next3_reason',c.get('reason','outside supported fragment')))
            else:
                from schema_check._format import project
                result=project(schema,sha(request['schema'].encode()),request['prefix'],request['prefix_provided'],c)
    except Failure as e:
        result={'format':'schema-check/v2','verification':e.kind if e.kind in ['UNKNOWN','NOT_APPLICABLE'] else 'FAIL','explanation':e.reason} if mode=='verify' else failure(e.kind,e.reason)
    except MemoryError:result={'format':'schema-check/v2','verification':'UNKNOWN','explanation':'memory budget exhausted'} if mode=='verify' else failure('UNKNOWN','memory budget exhausted')
    except Exception as e:
        result={'format':'schema-check/v2','verification':'FAIL','explanation':f'invalid evidence: {type(e).__name__}: {e}'} if mode=='verify' else failure('ERROR',f'{type(e).__name__}: {e}')
    sys.stdout.buffer.write((dumps(result)+'\n').encode())

if __name__=='__main__':main()
