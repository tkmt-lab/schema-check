# Reproduce the fixed-version comparisons

The default CLI and certificate replay have no third-party Python dependency. This optional experiment requires an environment separate from the packet. No model weights, account, inference server or GPU is needed. Use a disposable output directory and preserve the frozen observations.

## Fixed versions, inputs and runners

|Package|Version|Recorded source commit, where available|
|---|---|---|
|llguidance|1.9.1|f0971424ec072d3e4d4196bcc7f31a2f60527df9|
|XGrammar|0.2.8|97787376faee5ed8466cfad57c99855e4ce2f6aa|
|outlines-core|0.2.14|8466141a4d882572876d39563c9e6be372d918d3|
|torch|2.15.0|Reference wheel/environment metadata retained|
|tokenizers|0.23.3|Reference environment metadata retained|
|transformers|5.22.1|Reference environment metadata retained|
|jsonschema|4.26.0|Reference oracle environment metadata retained|

The source commits record research provenance; they do not prove wheel-to-source build equivalence. Reference platform: macOS ARM64, Python 3.14.7. Wheel availability/transitive versions can differ elsewhere. A version mismatch stops the supplied preflight. An explicit version snapshot creates a separate update run; it never silently changes the published reference pins.

The complete frozen inputs and runner code are bundled, with hashes in MANIFEST.json:

* **byte-v1:** 134 schemas/fixtures in `components/schema-check/next4/comparison/CASES.json`; runner `experiment.py` and `analyze.py` there. Original native/byte records are in `components/schema-check/next3/RESULTS.json`. The 83 supported schemas include development and issue-derived examples, not an unseen benchmark.
* **byte-v2:** 214 inputs in `components/schema-check/next7/CASES.json`; runner `run.py` and `analyze.py` there. Saved `all/`, `native/`, `SUMMARY.json`, `TABLE.csv` and `FAILURES.json` retain status and raw observations. This runner **reuses the frozen 83 native baseline records** and reruns the 40 newly eligible comparisons; it is not an all-123 fresh backend run by default. Supplying a same-version byte-v1 `--baseline` replaces those 83 inherited observations with that replay and records its environment/hash.
* **GPT-2 token probes:** `components/schema-check/next5/native_smoke.py` and its fixed tokenizer metadata/corpus. Its light probes do not replace the full token certificate replay.
* **Metaspace probes:** `components/schema-check/next6/native_metadata.py`, `native_probe.py`, fixed tokenizer metadata and byte corpus. Original indices 0,34,73,74 plus the explicitly marked simple-object controls are preserved. Outlines is supplied explicit first/continuation raw pieces; this is not a complete native SentencePiece integration.

The JSON Schema Test Suite revision is `3f05891cac5d51ffa068d7076d1372130e00c829`. Raw files, source manifests and MIT notices are retained under the frozen source directories. Typed/finite lifts are labeled separately from original Suite schemas. All tools receive the same logical schema; Boolean siblings and constraints are not removed to obtain a comparison.

## Platform scope

External-backend comparison commands are optional on both systems and are not required by `verify.py`. The reference workflow below uses **macOS ARM64 / Python 3.14.7**. On Linux, skip these commands for the default certificate replay; a separately attempted Linux comparison is outside that reference environment.

The existing Linux worker guard in `tools/limits.py` imposes a **2 GiB virtual-address-space limit (RLIMIT_AS)**. Some Linux Torch wheels, including CUDA-bearing dependencies, and OpenBLAS may fail to load or initialize under it, with MemoryError, ImportError or allocation errors. The RSS precaution is a different limit. These instructions do not relax either guard or prescribe a different Linux wheel installation.

An import/allocation failure is an environment failure, not a schema compilation refusal or a backend-conformance observation. In the current byte-v2 wrapper, such failures can appear in `compile_error` rows even when the wrapper ends with return code 0 or COMPLETE.json says PASS. Inspect the per-case logs before interpreting a Linux attempt, and keep that attempt separate from the frozen macOS table. The saved observations and counts are unchanged by this platform note.

## Prepare and run (optional reference-platform downloads)

```sh
python3 -m venv .comparison-env
.comparison-env/bin/python -m pip install -r comparison/requirements.txt \
  -c components/schema-check/next4/comparison/constraints-reference.txt
.comparison-env/bin/python -B comparison/check_environment.py
python3 -B comparison/reproduce.py byte-v1 --python "$PWD/.comparison-env/bin/python" --output .cache/reproduce-byte-v1
python3 -B comparison/reproduce.py byte-v2 --python "$PWD/.comparison-env/bin/python" --output .cache/reproduce-byte-v2
python3 -B comparison/reproduce.py gpt2 --python "$PWD/.comparison-env/bin/python" --output .cache/reproduce-gpt2
python3 -B comparison/reproduce.py metaspace --python "$PWD/.comparison-env/bin/python" --output .cache/reproduce-metaspace
python3 -B comparison/reproduce.py reports --python "$PWD/.comparison-env/bin/python" --output .cache/reproduce-reported-examples
```

The wrapper checks package metadata, copies the packet, then runs the original scripts in that disposable copy. It refuses an existing output directory. New outputs and warnings are retained in the copy/RUN.json and the original per-phase output locations; the frozen packet is not overwritten. Native code is an optional dependency and is not bundled. Running only the preflight checks metadata, not native behavior.

Byte runs use 256 single-byte pieces plus EOS, not a real model tokenizer. llguidance uses `lenient=false`, `coerce_one_of=false`; XGrammar uses `strict_mode=false`, one compiler thread and no cache; Outlines uses the Schema→regex→Index API. Settings/warnings are part of the observations. The original byte runners impose 30-second combined phases, retained-state limits, a 1.5GiB RSS precaution and a two-hour aggregate CPU budget. The packet wrapper additionally monitors combined RSS below 2GiB. Use one experiment at a time. The wrapper's wall allowance includes runner overhead and is not permission to discard an internal stop.

## Inspect the saved observations

|Tool|Fixed version|Supported reference records|Accepted-invalid case records|Existing issue/PR|Official repository record|Newly reported within saved invalid rows|
|---|---|---:|---:|---:|---:|---:|
|llguidance|1.9.1|123|0|0|0|0|
|XGrammar|0.2.8|123|58|46|12|0|
|outlines-core|0.2.14|123|17|16|0|1|

The same columns apply to each tool. [Per-case provenance](OBSERVATIONS.md) includes compile refusals and all 369 tool/schema rows. Counts illustrate recorded inputs, not distinct bugs or an overall ranking. In the earlier 83-case matrix the corresponding accepted-invalid observations were 0,33,9; the additional 40 cases contributed 0,25,8. Warnings, malformed-JSON acceptance, empty-language acceptance and representation restrictions remain separate. Only selected mask paths were traced; forced byte acceptance is not universally claimed to be an admitted sampling path.

Previously reported mechanisms, official repository warning/fallback records and the project's newly filed reports are labeled separately. Official records include merged PRs, not necessarily a user manual. An existing mechanism match is not a claim that the identical input appears in an issue. A closed issue does not imply a fix in the pinned release.

The newly filed examples are [XGrammar #1029](https://github.com/mlc-ai/xgrammar/issues/1029) and [Outlines #277](https://github.com/dottxt-ai/outlines-core/issues/277). The XGrammar schema is already in the 123-case matrix, but the violating value was not in its original probe set; the supplemental witness does not change the archived 58. The Outlines witness is already one of the 17 archived observations. Reproducers are bundled in comparison/reports/. These links record project reports, not maintainer confirmation or novelty.

The token records distinguish root infeasibility from new dead ends after a token-feasible root. Decoder metadata support, explicit raw-piece adapters, compile refusal, resource stops and complete-value mismatches are separate outcomes. No observed invalid acceptance is not a whole-backend language-equivalence proof.

## Update a version without mixing baselines

These are observations of fixed versions. When a newer released version resolves an observation, update the dated record after replaying the same inputs and runner; retain the older snapshot. Do not replace the frozen reference files or call a new environment the original comparison.

1. Copy comparison/reference-versions.json into `.cache/candidate-versions.json` and explicitly edit the selected package version(s). All seven distribution names must remain present. Prepare a separate environment, for example `.cache/comparison-new/`, with precisely that snapshot; no new environment is installed by the reproduction command.
2. Run the same byte-v1 wrapper with `--versions-file`. It records installed versions and input hashes in ENVIRONMENT.json.
3. Run byte-v2 with the same version snapshot **and the byte-v1 output directory as --baseline**. The wrapper refuses a missing baseline, a failed/incomplete baseline or mismatched versions. Its 83 inherited native records then come from the new same-version replay, followed by the 40 v2 additions. Actual baseline hashes/versions replace the original runner's hard-coded provenance label; the latter is retained only as a historical label.
4. Run the two standalone report examples with the same explicit version snapshot. Preserve stdout/stderr, compile refusal and resource/API errors. Annotate each dated observation as still observed, resolved in the tested version, refused, incompatible or unknown; archive the previous result. An API error is not a mathematical success.

```sh
.cache/comparison-new/bin/python -B comparison/check_environment.py --versions-file .cache/candidate-versions.json
python3 -B comparison/reproduce.py byte-v1 \
  --python "$PWD/.cache/comparison-new/bin/python" \
  --versions-file .cache/candidate-versions.json --output .cache/update-byte-v1
python3 -B comparison/reproduce.py byte-v2 \
  --python "$PWD/.cache/comparison-new/bin/python" \
  --versions-file .cache/candidate-versions.json --baseline .cache/update-byte-v1 \
  --output .cache/update-byte-v2
python3 -B comparison/reproduce.py reports \
  --python "$PWD/.cache/comparison-new/bin/python" \
  --versions-file .cache/candidate-versions.json --output .cache/update-reports
```

The update mode supports byte comparisons and standalone report examples. The fixed native GPT-2/Metaspace adapter probes contain their own pinned assertions and are not silently treated as new-version tests. The saved observations cover only the published pins; newer versions require separate runs.

The frozen observation-classification checker validates only the archived reference table, whose totals are intentionally fixed. New-version analyses and dated update notes live in their new output directory. Do not merge old and new records to produce a larger bug count.
