# Fixed vocabularies and token reachability

The retained token code consumes v1 byte DFA evidence. It first checks that byte evidence. GPT-2 uses a fixed map from each ordinary token ID to its raw byte piece, before lossy UTF-8 replacement. The certificate checks a byte-state quotient, all ordinary-token transitions, shortest ordinary-token distances and witnesses. GPT-2 has all 256 one-byte pieces, hence every byte-completable state can also be completed with ordinary tokens in this fixed model. The observed zero gap in 83 schemas is consistent with that structural fact; it does not say byte and token shortest distances agree.

T5-small and ALBERT use a two-phase ordinary-token Metaspace map. In the first phase the leading-space behavior is removed; in continuation the replacement becomes a space. Empty-output first tokens are real tokens, rather than silently deleted. Special and unknown IDs are excluded as recorded in the code and tokenizer metadata. ALBERT is an MLM vocabulary control. No weights or inference calls are made.

|Vocabulary|Pinned revision|tokenizer.json SHA256|
|---|---|---|
|openai-community/gpt2|607a30d783dfa663caf39e06633721c8d4cfcd7e|8414cab924d8b9b33013f0d221c5862f365ee9be39c5c2bfae8a5a9e970478a6|
|google-t5/t5-small|df1b051c49625cf57a3d0d8d3863ed4d13564fe4|d2acde0d8d71dd30a711834b07781b9c89feaac33fd332f60507699282740066|
|albert/albert-base-v2|8e2f239c5f8a2c0f253781ca60135db913e5c80c|6e2aa3d5ca4c6841bc36a5028179cb4d63c129931fa18fce38fdb38cec4d2ac3|

Exact URLs and byte sizes are in `components/schema-check/next5/TOKENIZER-SOURCE.json` and `components/schema-check/next6/TOKENIZERS.json`. The unchanged JSONs are bundled in `data/tokenizers/` so default checking requires no network.

Every ordinary token is directly replayed from every checked quotient/phase state by the token verifier; it does not use the producer's trie traversal. Byte/quotient consistency, graph closure, Bellman equations, tie-breaking and witnesses are checked. Shared trust still includes the byte-language semantic kernels and the fixed vocabulary conversion; the Metaspace query segmentation helper is shared too. This is separate code checking, not an independent review or a second independent decoder semantics implementation.

The fixed data have 12 empty byte languages and 71 nonempty ones. GPT-2 has zero byte-live/token-dead schema cases. T5 and ALBERT have 24 and 28 byte-nonempty but root-token-infeasible cases. In both, no recorded case has a dead reachable state from a token-feasible root. Root infeasibility, prefixes that cannot be tokenized, and new dead ends after a feasible root must not be combined into a single failure count. The per-vocabulary summaries retain these distinctions and the recorded-prefix denominators.

No guarantee is made for arbitrary vocabularies, decoder contexts, external token filtering, lossy UTF-8 replacement paths, token probabilities, serving integrations or termination of arbitrary sampling. EOS is separate from ordinary tokens. The public GPT-2 CLI reports both ordinary-token distance and explicit-EOS distance. The T5/ALBERT corpus checker is a research interface, not a general tokenizer adapter.
