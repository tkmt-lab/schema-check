"""Exhaustive token/byte/Unicode inventory and native Rust decoder equivalence."""
import json,resource,signal,time,hashlib
from pathlib import Path
from tokenizers import Tokenizer
from vocabulary import load,trie
P=Path(__file__).resolve().parent
resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(60);start=time.process_time()
records=[]
for key in ['t5-small','albert-base-v2']:
    first,later,stop,s,j=load(key);hf=Tokenizer.from_file(str(P.parents[2]/s['path']))
    probe=next(i for i,b in first.items() if b and b==later[i]);lead=hf.decode([probe],skip_special_tokens=True)
    assert all(hf.decode([i],skip_special_tokens=True).encode()==b for i,b in first.items())
    assert all(hf.decode([probe,i],skip_special_tokens=True).encode()==lead.encode()+b for i,b in later.items())
    present_bytes=set().union(*(set(b) for b in later.values()),*(set(b) for b in first.values()))
    scalars={ord(c) for b in list(first.values())+list(later.values()) for c in b.decode()}
    ranges=[]
    for lo,hi in [(0,0xD7FF),(0xE000,0x10FFFF)]:
        cursor=lo
        for v in sorted(x for x in scalars if lo<=x<=hi):
            if cursor<v:ranges.append([cursor,v-1])
            cursor=v+1
        if cursor<=hi:ranges.append([cursor,hi])
    rec={**s,'model_type_verified':'Unigram (legacy JSON has no model.type)','ordinary_tokens':len(first),'vocabulary_size':hf.get_vocab_size(),'excluded_special_ids':[t['id'] for t in j['added_tokens'] if t['special']],
         'stop_id':stop,'stop_convention':'model EOS' if key=='t5-small' else 'SEP as API stop marker; ALBERT has no autoregressive EOS',
         'rust_decoder_all_singletons_and_all_probe_pairs_match':True,'probe_token_id':probe,
         'empty_first_ids':[i for i,b in first.items() if not b],'empty_later_ids':[i for i,b in later.items() if not b],
         'first_trie_states':len(trie(first)),'later_trie_states':len(trie(later)),
         'missing_single_byte_pieces_first':[b for b in range(256) if bytes([b]) not in set(first.values())],
         'missing_single_byte_pieces_later':[b for b in range(256) if bytes([b]) not in set(later.values())],
         'byte_values_absent_everywhere':[b for b in range(256) if b not in present_bytes],
         'unicode_scalars_present_count':len(scalars),'unicode_scalars_missing_count':sum(b-a+1 for a,b in ranges),'unicode_missing_ranges_inclusive':ranges,
         'printable_ascii_absent_everywhere':[chr(v) for v in range(32,127) if v not in scalars],
         'singleton_character_piece_count_first':len({b.decode() for b in first.values() if len(b.decode())==1}),
         'singleton_character_piece_count_later':len({b.decode() for b in later.values() if len(b.decode())==1}),
         'selected_character_presence':{c:ord(c) in scalars for c in ['{','}','\\','"','A','a','é','😀','💩']}}
    records.append(rec)
out={'records':records,'cpu_seconds':time.process_time()-start,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(P/'INVENTORY.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['key','ordinary_tokens','first_trie_states','later_trie_states','printable_ascii_absent_everywhere','empty_first_ids','byte_values_absent_everywhere','unicode_scalars_missing_count']} for r in records],ensure_ascii=False))
