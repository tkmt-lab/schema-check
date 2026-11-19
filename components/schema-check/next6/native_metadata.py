import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import json,time,resource,signal,importlib.metadata as metadata
from pathlib import Path
from vocabulary import load,digest
resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(59);start=time.process_time()
from llguidance import LLTokenizer
from transformers import PreTrainedTokenizerFast
import torch,xgrammar as xgr
torch.set_num_threads(1);torch.set_num_interop_threads(1)
P=Path(__file__).resolve().parent;rows=[]
for key in ['t5-small','albert-base-v2']:
    first,later,stop,s,j=load(key);path=P.parents[2]/s['path'];ll_error=None
    try:ll=LLTokenizer(str(path),eos_token=stop,slices=[])
    except ValueError as e:ll=None;ll_error=str(e)
    hf=PreTrainedTokenizerFast(tokenizer_file=str(path),unk_token='<unk>',pad_token='<pad>')
    ti=xgr.TokenizerInfo.from_huggingface(hf,stop_token_ids=[stop]);decoded=ti.decoded_vocab
    encoded=[w for w,score in j['model']['vocab']]
    for t in j['added_tokens']:
        if t['id']>=len(encoded):encoded.extend(['']*(t['id']+1-len(encoded)))
        encoded[t['id']]=t['content']
    manual=xgr.TokenizerInfo(encoded,vocab_type=xgr.VocabType.BYTE_FALLBACK,stop_token_ids=[stop],add_prefix_space=True);manual_decoded=manual.decoded_vocab
    rows.append({'key':key,'llguidance_load_error':ll_error,'llguidance_vocab_size':None if ll is None else ll.vocab_size,'llguidance_first_differences':None if ll is None else [i for i,b in first.items() if ll.decode_bytes([i])!=b],
        'llguidance_later_differences':None if ll is None else [i for i,b in later.items() if ll.decode_bytes([i])!=b],
        'llguidance_extra_special_ids':None if ll is None else [i for i in first if ll.is_special_token(i)],
        'xgrammar_vocab_type':str(ti.vocab_type),'xgrammar_add_prefix_space':ti.add_prefix_space,
        'xgrammar_first_differences':[i for i,b in first.items() if decoded[i]!=b],
        'xgrammar_later_differences':[i for i,b in later.items() if decoded[i]!=b],
        'hf_backend_decoder':json.loads(hf.backend_tokenizer.to_str())['decoder'],
        'xgrammar_explicit_metaspace_later_differences':[i for i,b in later.items() if manual_decoded[i]!=b]})
out={'versions':{k:metadata.version(k) for k in ['llguidance','xgrammar','outlines-core','tokenizers','torch','transformers']},'rows':rows,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(P/'NATIVE-METADATA.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([{k:len(v) if isinstance(v,list) else v for k,v in r.items()} for r in rows]))
