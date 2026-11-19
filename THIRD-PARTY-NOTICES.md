# Third-party material

Project licensing does not replace these terms.

|Material|Source and scope|Retained terms|
|---|---|---|
|JSON Schema Test Suite inputs and their copies embedded in case/certificate corpora|Revision `3f05891cac5d51ffa068d7076d1372130e00c829`; source URLs in the frozen source manifests|MIT notices in `components/schema-check/next4/{tests,comparison}/SUITE-LICENSE` and `components/schema-check/next7/sources/SUITE-LICENSE`|
|GPT-2 tokenizer and model card|`openai-community/gpt2`, revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`|Pinned model card says MIT; upstream OpenAI text is titled Modified MIT License. Both are retained in `third_party/cards/gpt2-README.md` and `third_party/GPT2-UPSTREAM-LICENSE.txt`.|
|T5-small tokenizer and model card|`google-t5/t5-small`, revision `df1b051c49625cf57a3d0d8d3863ed4d13564fe4`|Apache-2.0 metadata; card and upstream license retained in `third_party/`|
|ALBERT-base-v2 tokenizer and model card|`albert/albert-base-v2`, revision `8e2f239c5f8a2c0f253781ca60135db913e5c80c`|Apache-2.0 metadata; card and upstream license retained in `third_party/`|

Tokenizer snapshots are unchanged; only the project-side path fields locating them were changed. No model weights are bundled. The model repositories contain no separate LICENSE file at these pinned revisions; metadata and model cards are retained, alongside license texts retrieved from the corresponding upstream projects. Retrieval URLs and hashes are in PROVENANCE.json. These records preserve provenance; they are not a legal certification of every upstream asset's licensing history.

Issue-derived schemas remain attributed to their source issues in the frozen input/source records. Existing implementation defects are described as fixed-version observations. The package makes no claim to owning upstream descriptions, no claim of bug priority, and no claim of upstream priority. The project reports XGrammar #1029 and Outlines #277 are linked in docs/OBSERVATIONS.md.

llguidance, XGrammar, outlines-core, torch, tokenizers, transformers, jsonschema and Python are external runtime/reference dependencies for optional experiments. Their implementations, wheels, services and papers are not redistributed by this packet. Their own licenses apply.
