# schema-check: certificates for canonical JSON completion

**Version 0.1.0 · Release date 2026-11-20 · DOI: not specified**

https://github.com/tkmt-lab/schema-check · Tatsuhiko Takimoto

Inspect JSON Schema constraints for structured-output generation.
For supported schemas, this package computes emptiness and shortest completions in a canonical UTF-8 reference language, with separate checking entries for the evidence.
Developers can use the reference language and finite probes of fixed-version backends to inspect accepted values against the schema.

## Run a byte check

Requirements: Python 3.10 or later, POSIX `ps`, macOS or Linux. The default tools run offline using only Python's standard library.

From this directory, keep generated examples under the manifest-excluded `.cache/` directory. They can remain there when you run `verify.py` later:

```sh
mkdir -p .cache/examples
python3 -B schema-check examples/object.json --prefix '{"modifier":' -o .cache/examples/result.json
python3 -B schema-check verify .cache/examples/result.json --schema examples/object.json
```

Expected result: the three-byte suffix `""}`. Generation sets `verification: NOT_RUN`; successful separate verification returns `verification: PASS`. Without `-o`, JSON goes to stdout; a short explanation goes to stderr.

## More byte examples and output fields

```sh
python3 -B schema-check examples/tenths.json --prefix '0.' -o .cache/examples/decimal-result.json
python3 -B schema-check verify .cache/examples/decimal-result.json --schema examples/tenths.json
python3 -B schema-check examples/empty-number.json -o .cache/examples/empty-result.json
python3 -B schema-check examples/emoji.json --prefix-hex 22f09f -o .cache/examples/partial-utf8.json
```

The decimal example needs suffix `1`. The contradictory numeric schema has an empty language. The emoji prefix stops inside a UTF-8 character; a suffix may therefore have `utf8: null` while its authoritative `bytes` and `hex` fields are present. `--prefix-file` reads exact bytes and does not strip a newline.

|Output|Meaning|
|---|---|
|`support: SUPPORTED`|The artifact supplies language and shortest-completion evidence in the documented model.|
|`UNSUPPORTED`|The schema is outside the implemented fragment; the record contains status only.|
|`UNKNOWN`|A resource/size bound prevented a conclusion; the record contains status only.|
|`INVALID_INPUT`|Checked input syntax is invalid.|
|`language.empty`|A boolean for supported inputs; otherwise null.|
|`prefix.can_complete`|Whether these exact prefix bytes have a canonical continuation.|
|`prefix.shortest_completion`|A shortest suffix, including an empty suffix for an already complete value.|

Exit codes are 0 for supported answers/PASS, 1 for verification failure/internal error, 2 for invalid input, and 3 for unsupported/unknown/not-applicable results. `verify --schema` binds the exact schema document, including whitespace, as well as its normalized meaning.

## The reference language

The fixed corpus has **123 supported schemas out of 214**, **88 unsupported** and **3 unknown**.

The language is **canonical compact JSON**, with recursively sorted object keys, no whitespace, Python JSON string escapes, and raw UTF-8 for other Unicode scalars. Numbers use exact finite decimal notation without an exponent, redundant fractional zeros or negative zero. “No completion” is relative to that language.

Supported fragments include finite enum/const and closed finite objects; declared string guards and restricted full-string patterns; exact rational numeric bounds, exclusive bounds and `multipleOf`; finite-domain arrays with `items`, length bounds and `uniqueItems`; and Boolean combinations where the required guards can be established. String lengths count Unicode code points; distances count UTF-8 **bytes**. [Supported inputs](docs/SUPPORTED.md) states the restrictions.

## Fixed-vocabulary token evidence

The token component currently consumes **schema-check/v1**, while the main command produces **v2** with numeric/array extensions. The v1 implementation is retained explicitly:

```sh
python3 -B schema-check-v1 examples/object.json --prefix '{"modifier":' -o .cache/examples/byte-v1.json
python3 -B token-check .cache/examples/byte-v1.json -o .cache/examples/token-result.json
python3 -B token-check verify .cache/examples/token-result.json --schema examples/object.json
```

`token-check` uses the fixed GPT-2 ordinary-token pieces. Distances count ordinary tokens; `distance_including_eos` and the EOS witness add one explicit EOS. `--prefix-token-ids` preserves a supplied ordinary-token prefix. Passing a v2 artifact to this v1 token entry fails explicitly.

T5-small and ALBERT-base-v2 retain first-token versus continuation Metaspace phases. They are available as frozen corpus tools. Replay one saved case by index 0–82:

```sh
python3 -B tools/check_corpus.py t5-small 73
python3 -B tools/check_corpus.py albert-base-v2 73
```

The input byte language must itself be canonical valid UTF-8. T5/ALBERT exclude special and unknown tokens as recorded in their pinned conversion. ALBERT is a vocabulary control. [Token model](docs/TOKEN-MODEL.md) records the boundaries and the pinned input hashes.

## Verify the complete frozen packet

```sh
python3 -B verify.py
```

The default replay is offline. It checks the manifest, 123 supported v2 byte certificates among 214 records, keeps 88 UNSUPPORTED and 3 UNKNOWN records separate, checks all 83 legacy byte certificates while replaying **249 token certificates** (83 per vocabulary), runs four public examples and the GPT-2 CLI round trip, rejects altered evidence and v2/v1 misuse, and verifies a physically detached v2 copy after its producer files have been removed. Results go to `.cache/verification.json`. The frozen files remain unchanged. Allow several minutes; the program uses one computational worker at a time, 30/60-second phase limits and an aggregate one-hour CPU stop.

Each worker is monitored with a **1.5 GiB aggregate-RSS precaution stop below the 2 GiB ceiling**. Linux also applies a per-process 2 GiB address-space limit. A limit stop fails the packet replay. Run without `python -O`; assertion-enabled workers are required. [Verification boundaries](docs/VERIFICATION.md) describe the shared semantic kernels. Dated replay results and source adaptations are collected in the [verification record](docs/VERIFICATION-RECORD.md).

The optional external-backend comparisons use a separate pinned macOS environment; [reproduction instructions](docs/COMPARISON.md) specify versions, input snapshots, runners and interpretation. Default verification hashes the saved observations. See [platform scope](docs/COMPARISON.md#platform-scope) for the environment requirements.

In the frozen records, GPT-2 has zero byte-live/token-dead cases in 83 schemas because every byte has an ordinary one-byte piece. T5-small and ALBERT have 24 and 28 byte-nonempty schemas respectively that are token-infeasible from the root. Neither corpus contains a dead state reachable from a token-feasible root.

## Inspect the fixed-version observations

The following records illustrate what the inspection workflow exposes. The same columns and the same 123 reference-supported schemas are used for all tools. Refusals include correct rejection of unsatisfiable schemas.

|Tool|Version|Schema records|Compile refusals|Accepted-invalid case records|Existing issue/PR|Official repository record|Newly reported within saved invalid rows|
|---|---|---:|---:|---:|---:|---:|---:|
|llguidance|1.9.1|123|26|0|0|0|0|
|XGrammar|0.2.8|123|8|58|46|12|0|
|outlines-core|0.2.14|123|42|17|16|0|1|

Each affected case has an [issue/record classification](docs/OBSERVATIONS.md); the full 369 tool/schema rows include refusals and zero-observation rows. Official repository records include merged PRs and warning/test records.

Two examples were newly reported by the project: [XGrammar #1029](https://github.com/mlc-ai/xgrammar/issues/1029), accepting `{"a":false}` under a closed object with an undeclared required key, and [Outlines #277](https://github.com/dottxt-ai/outlines-core/issues/277), accepting `{}` under an anyOf branch requiring modifier. The XGrammar schema is already in the 123-case matrix, but its violating value was absent from the original probes; the supplemental witness is not added to 58. The Outlines witness is already among 17.

When a newer released version resolves an observation, the record is updated after replaying the same inputs and runner, while the older snapshot remains archived. The [update recipe](docs/COMPARISON.md#update-a-version-without-mixing-baselines) uses a separate version snapshot and a same-version byte-v1 baseline before the 40 v2 additions; the old 83 observations remain in their original snapshot.

## Related work

[JSONSchemaBench](https://arxiv.org/abs/2501.10868) (Geng et al., 2025; also an ICML 2025 ES-FoMo III workshop version) studies empirical coverage and output compliance over large real-world schema collections; this package checks exact language equivalence for supported canonical reference automata, while its external-backend comparisons remain finite probes. The paper also distinguishes true, empirical and theoretical coverage; [reference details](docs/RELATED-WORK.md) preserve that distinction.

## Scope

The language-equivalence check covers the complete supported **reference automaton language**. Alternate serializations of the same JSON value can fall outside the canonical language. Open recursive JSON, references, unrestricted arrays, general regular expressions and unknown keywords remain outside the implementation; regularity alone does not imply support. UNSUPPORTED and UNKNOWN records contain no mathematical certificate, and resource stops are never emptiness proofs. Input checks are not a complete JSON Schema metaschema validator.

Token evidence exhausts the ordinary IDs of the **three pinned vocabularies**. It does not extend to every tokenizer or decoder, and a byte completion alone does not prove token-level completion. The input byte language must be canonical valid UTF-8; extra paths from a final lossy decoder replacing malformed UTF-8 are outside the shortestness guarantee. Token sequences need not be the BPE encoder's preferred segmentation. T5/ALBERT are frozen corpus tools, not a general decoder adapter; ALBERT's role as a vocabulary control is not an autoregressive-model recommendation. Arbitrary sampling termination, serving-backend integration and probability guarantees are outside the claims.

External-backend comparisons are finite probes of fixed versions/settings. Zero observed invalid acceptances, including the llguidance row, do not certify a backend's whole language. The saved data are development/reproduction inputs, not an unseen benchmark; case counts describe observations, not distinct bugs or overall tool quality. Official repository records are not necessarily a user-manual support table. Issue reports and acknowledgements do not imply the cited authors' review, endorsement or agreement; filing a report also does not establish priority. No performance-superiority or novelty claim is made.

The standard replay checks saved observations by hash and does not rerun or independently certify external backends. Linux runs of the optional comparisons are not reference-environment reproductions, and Torch/OpenBLAS imports may fail under the address-space limit. On macOS, RSS polling is not an absolute hard address-space guarantee. Producer/checker entry separation retains shared semantic kernels; it does not establish independent semantics. External independent review and formal proof remain unclaimed. Digests and the manifest check bytes, not sender identity, authorship, mathematical truth or a digital signature.

This package provides checked impossibility results and concrete shortest completions within its fragment; it does not replace a general JSON Schema validator or a production decoder. [claims.json](claims.json) maps the claims to evidence and limitations.

## AI use and responsibility

Google Gemini suggested asking whether a partial JSON document can be completed under the constraints of a schema.
OpenAI Codex helped implement the checker, run the byte and token calculations, and verify the resulting certificates.
AI agents reviewed related work and upstream issue reports, drafted reports, and edited the documentation. GPT-6-astra helped review the text.
For selected backend observations, a separate AI agent wrote its own test code and checked the results against a JSON Schema validator. Human peer reviewers did not take part in these computational checks.
Anthropic Claude Code helped submit two issue reports with the author’s approval.
The records do not identify the model versions used for the other tasks.
Tatsuhiko Takimoto is the author and takes responsibility for the code, data, and written conclusions.

## Attribution and contact

[PROVENANCE.json](PROVENANCE.json) records the frozen sources and adaptations.

Project-owned code is **Apache-2.0**; original documentation and generated evidence are **CC-BY-4.0**. Third-party Suite fixtures, tokenizer files and upstream notices retain their own terms; see [LICENSE](LICENSE) and [third-party notices](THIRD-PARTY-NOTICES.md). The GPT-2 model card says MIT while its upstream text is titled “Modified MIT License”; both are retained, not replaced with a project license. [CITATION.cff](CITATION.cff) and `.zenodo.json` record the release metadata. Research contact: [research@tatsuhikotakimoto.com](mailto:research@tatsuhikotakimoto.com).

## Acknowledgements

* The llguidance developers provide the matcher, byte-token APIs and warning records used by the fixed-input replay.
* The XGrammar developers provide the JSON Schema compiler, matcher and token-mask interfaces used by the same inspection workflow.
* The Outlines developers provide the Schema-to-regex and Index APIs used to replay the same inputs.
* Geng and the JSONSchemaBench coauthors make coverage and compliance explicit in their evaluation framework; those distinctions inform how this packet states its scope.
* The JSON Schema Test Suite and tokenizer maintainers provide the fixtures and pinned public vocabularies used here.

We thank these authors and maintainers for making those inputs, interfaces and definitions available.
