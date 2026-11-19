# Reproduce the optional backend comparison

The public `schema-check` command and its verifier use only the Python standard library. This comparison is a separate experiment. It requires external packages and does not make them runtime dependencies of the CLI. No model, tokenizer, GPU, vLLM server, or SGLang server is used.

The reference snapshot was recorded on 2026-11-02 with macOS arm64 and Python 3.14.7. Its complete package metadata is `comparison/ENVIRONMENT.json`. These versions and source commits were fixed before the original comparison:

|Package / input|Version / commit|
|---|---|
|[llguidance](https://github.com/guidance-ai/llguidance/tree/f0971424ec072d3e4d4196bcc7f31a2f60527df9)|1.9.1 / f0971424ec072d3e4d4196bcc7f31a2f60527df9|
|[outlines-core](https://github.com/dottxt-ai/outlines-core/tree/8466141a4d882572876d39563c9e6be372d918d3)|0.2.14 / 8466141a4d882572876d39563c9e6be372d918d3|
|[XGrammar](https://github.com/mlc-ai/xgrammar/tree/97787376faee5ed8466cfad57c99855e4ce2f6aa)|0.2.8 / 97787376faee5ed8466cfad57c99855e4ce2f6aa|
|torch|2.15.0|
|[JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/3f05891cac5d51ffa068d7076d1372130e00c829)|3f05891cac5d51ffa068d7076d1372130e00c829|

`comparison/CASES.json` freezes all 134 original schemas and fixtures, including development cases and issue-derived inputs. Selected raw Suite groups and finite lifts are labeled separately. `comparison/SOURCES.json` records the fixed references; `LLGUIDANCE-SOURCE.json`, `OUTLINES-WHEEL.json`, and `XGRAMMAR-WHEEL.json` preserve the previous wheel/source provenance. Metadata version checks do not establish a reproducible source build, and a wheel for another platform need not have the same hash.

## Prepare an optional environment

Run this in a disposable copy with enough space for torch and its dependencies. This step downloads packages; the ordinary CLI does not need it.

```sh
python3 -m venv .comparison-env
.comparison-env/bin/python -m pip install -r comparison/requirements.txt -c comparison/constraints-reference.txt
.comparison-env/bin/python -B comparison/check_environment.py
```

`requirements.txt` pins the four directly used packages. The constraints file records the reference environment's transitive versions. On a different platform/runtime, first check wheel availability and keep any changed environment as a separate experiment. Do not silently substitute a different package version and call it the same comparison.

## Run the frozen experiment

```sh
.comparison-env/bin/python -B comparison/experiment.py
.comparison-env/bin/python -B comparison/analyze.py
```

The experiment writes `comparison/RESULTS.json`, `SUMMARY.json`, and `FAILURES.json`. It checkpoints one case at a time; use a disposable copy or preserve old output before repeating. It uses the bundled engine directly so the original schemas, including their numeric spellings in the fixture data, remain the comparison input. It does not route the data through a decoder's approximation settings.

All three backends receive the same schema and 256 single-byte tokens plus EOS. Object keys are recursively sorted for serialization; no logical constraint is removed. llguidance uses `lenient=false` and `coerce_one_of=false`. Outlines uses its official Schema→regex→Index API. XGrammar uses `strict_mode=false`, one compiler thread, and no compiler cache, so unspecified additional properties/items are not independently forbidden. Native warnings are retained in each worker's stderr. These are byte-vocabulary results, not model-token or serving-stack tests.

The runner permits one compute worker at a time, CPU30/wall29 seconds per case, 100,000 engine states, RSS precaution stopping at 1.5 GiB, and a two-hour cumulative CPU budget. On macOS the RSS polling is a precaution rather than a hard address-space guarantee. A worker failure or incomplete run must not be counted as success or as an empty schema. The analyzer rejects incomplete/error-bearing results before counting.

## Compare the results correctly

The original next3 snapshot had 83 supported schemas out of 134. Among those 83, it observed invalid accepted encodings in 0 llguidance records, 9 Outlines records, and 33 XGrammar records (31 distinct schemas after removing annotations). Empty languages with an accepted encoding occurred in 0/4/7 records. Empty allowed-token masks at admitted nonterminal prefixes occurred in 0/0/0 records. Compile errors are reported separately and include correct unsatisfiability diagnostics; they are not all bugs. Rejection of a canonical valid fixture is also separate because some backends constrain representation or property order.

These counts describe the 2026-11-02 reference snapshot. Native warnings mean that a constraint loss is not necessarily silent. The cases were selected development/reproduction inputs, not an unseen benchmark or a coverage claim for the full Test Suite.

`examples/issue-858.json` and `issue-895.json` have the same schema conditions as [XGrammar #858](https://github.com/mlc-ai/xgrammar/issues/858) and [#895](https://github.com/mlc-ai/xgrammar/issues/895). They can be answered with the dependency-free CLI. Reproducing those schema-level constraints does not reproduce the original model token, vLLM routing, SGLang wrapper, or arbitrary-sampler termination problem.

The copied Suite fixtures retain their MIT notice in `comparison/SUITE-LICENSE`. External package code/wheels are not included in this directory.
