"""Public command. Mathematical work runs in a bounded isolated interpreter."""
import argparse,json,os,subprocess,sys,tempfile,time,shutil
from pathlib import Path
from . import __version__
from ._shared import Failure,failure,SCHEMA_LIMIT,PREFIX_LIMIT,ARTIFACT_LIMIT,dumps

class Parser(argparse.ArgumentParser):
    def error(self,message):raise Failure('INVALID_INPUT',message)

def read(path,limit,text=True):
    with Path(path).open('rb') as f:b=f.read(limit+1)
    if len(b)>limit:raise Failure('UNKNOWN',f'{path}: input exceeds {limit} bytes')
    if text:
        try:return b.decode('utf-8')
        except UnicodeDecodeError as e:raise Failure('INVALID_INPUT',f'{path}: expected UTF-8') from e
    return b

def run(request,timeout):
    worker=Path(__file__).resolve().parent/'_worker.py';start=time.monotonic()
    proc=subprocess.Popen([sys.executable,'-I','-S','-B',str(worker)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    data=json.dumps(request,ensure_ascii=True).encode();first=True;ps=shutil.which('ps');reason=None
    while True:
        try:
            out,err=proc.communicate(data if first else None,timeout=min(.15,timeout))
            break
        except subprocess.TimeoutExpired:
            first=False
            if time.monotonic()-start>=timeout:reason='wall time budget exhausted'
            if ps and not reason:
                try:
                    usage=subprocess.run([ps,'-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=1).stdout.strip()
                    if usage and int(usage)*1024>1536*1024**2:reason='RSS precaution limit exceeded'
                except (OSError,ValueError,subprocess.TimeoutExpired):pass
            if reason:
                proc.kill();proc.communicate();break
    if reason or proc.returncode:
        why=reason or f'worker stopped with exit {proc.returncode} (no emptiness conclusion)'
        return {'format':'schema-check/v1','verification':'UNKNOWN','explanation':why} if request['mode']=='verify' else failure('UNKNOWN',why)
    if len(out)>ARTIFACT_LIMIT:
        return {'format':'schema-check/v1','verification':'UNKNOWN','explanation':'artifact exceeds output budget'} if request['mode']=='verify' else failure('UNKNOWN','artifact exceeds output budget')
    try:return json.loads(out)
    except ValueError as e:raise Failure('ERROR','worker did not return JSON') from e

def emit(result,output,quiet,inputs):
    data=(dumps(result)+'\n').encode('utf-8')
    if output and output!='-':
        target=Path(output)
        if target.resolve() in [Path(p).resolve() for p in inputs if p]:raise Failure('INVALID_INPUT','output must not overwrite an input file')
        name=None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.'+target.name+'.',delete=False) as f:name=f.name;f.write(data)
            os.replace(name,target);name=None
        finally:
            if name:Path(name).unlink(missing_ok=True)
    else:sys.stdout.buffer.write(data)
    if not quiet:sys.stderr.write(result.get('explanation','')+'\n')

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv);mode='verify' if args[:1]==['verify'] else 'check'
    if mode=='verify':args=args[1:]
    parser=Parser(prog='schema-check verify' if mode=='verify' else 'schema-check',description='Check the documented canonical UTF-8 byte fragment of JSON Schema.' if mode=='check' else 'Verify saved evidence without reading producer code.')
    parser.add_argument('--version',action='version',version=__version__)
    parser.add_argument('artifact' if mode=='verify' else 'schema')
    parser.add_argument('-o','--output',help='write JSON atomically to this file (default: stdout)')
    parser.add_argument('--quiet',action='store_true',help='suppress the short stderr explanation')
    parser.add_argument('--timeout',type=float,default=30,help='wall time budget, 0 < seconds <= 30')
    if mode=='verify':parser.add_argument('--schema',help='also bind evidence to this exact UTF-8 schema document')
    else:
        group=parser.add_mutually_exclusive_group();group.add_argument('--prefix',help='exact UTF-8 prefix text, including JSON quotes');group.add_argument('--prefix-file',help='raw prefix bytes; no newline is stripped');group.add_argument('--prefix-hex',help='prefix bytes in hexadecimal; permits partial UTF-8')
    output=None;quiet=False;inputs=[]
    try:
        a=parser.parse_args(args);output=a.output;quiet=a.quiet
        if not 0<a.timeout<=30:raise Failure('INVALID_INPUT','timeout must be in (0,30]')
        if mode=='verify':
            inputs=[a.artifact,a.schema];request={'mode':'verify','artifact':read(a.artifact,ARTIFACT_LIMIT)}
            if a.schema:request['external_schema']=read(a.schema,SCHEMA_LIMIT)
        else:
            inputs=[a.schema,a.prefix_file];prefix=b'';provided=any(x is not None for x in [a.prefix,a.prefix_file,a.prefix_hex])
            if a.prefix is not None:prefix=a.prefix.encode('utf-8')
            elif a.prefix_file is not None:prefix=read(a.prefix_file,PREFIX_LIMIT,False)
            elif a.prefix_hex is not None:
                try:prefix=bytes.fromhex(a.prefix_hex)
                except ValueError as e:raise Failure('INVALID_INPUT','invalid hexadecimal prefix') from e
            if len(prefix)>PREFIX_LIMIT:raise Failure('UNKNOWN','prefix exceeds byte budget')
            request={'mode':'check','schema':read(a.schema,SCHEMA_LIMIT),'prefix':list(prefix),'prefix_provided':provided}
        result=run(request,a.timeout)
        emit(result,output,quiet,inputs)
    except (Failure,OSError,UnicodeError,ValueError) as e:
        kind=e.kind if isinstance(e,Failure) else 'INVALID_INPUT';reason=e.reason if isinstance(e,Failure) else str(e)
        result={'format':'schema-check/v1','verification':'UNKNOWN' if kind=='UNKNOWN' else 'FAIL','explanation':reason} if mode=='verify' else failure(kind,reason)
        # Error JSON always goes to stdout; never overwrite a requested input/output on error.
        sys.stdout.buffer.write((dumps(result)+'\n').encode())
        if not quiet:sys.stderr.write(result['explanation']+'\n')
    if mode=='verify':return {'PASS':0,'UNKNOWN':3,'NOT_APPLICABLE':3}.get(result.get('verification'),1)
    return {'SUPPORTED':0,'UNSUPPORTED':3,'UNKNOWN':3,'INVALID_INPUT':2}.get(result.get('support'),1)
