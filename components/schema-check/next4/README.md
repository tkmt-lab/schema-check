# schema-check

Check emptiness and shortest byte completions for a documented fragment of JSON Schema. The command produces JSON evidence and a short explanation. A separate command verifies the evidence without reading the producer files.

This directory contains the self-contained v1 byte implementation used by the fixed-vocabulary token tools. The main package command uses v2, which adds the numeric and array fragments described in [Supported inputs](../../../docs/SUPPORTED.md).

## Run

Requires Python 3.10 or later on macOS or Linux. Tested with Python 3.14.7. There are no third-party Python dependencies, model downloads, accounts, or background services. From this directory:

```sh
mkdir -p .cache/examples
./schema-check examples/issue-858.json -o .cache/examples/result.json
./schema-check verify .cache/examples/result.json --schema examples/issue-858.json
```

The generation command writes the full JSON artifact to `.cache/examples/result.json` and prints a short explanation to stderr. Without `-o`, JSON goes to stdout. `--quiet` suppresses the stderr explanation. `python3 schema-check ...` and `python3 -m schema_check ...` are alternatives.

For this example, the shortest example is `{"modifier":""}`. The artifact contains the normalized schema, its digests, the automaton certificate, and the exact byte claims. Producing evidence sets `verification` to `NOT_RUN`; the verification command returns a separate `verification: PASS` report.

Pass an exact prefix, including the opening JSON quote or brace:

```sh
./schema-check examples/issue-858.json --prefix '{"modifier":' -o .cache/examples/prefix-result.json
./schema-check verify .cache/examples/prefix-result.json --schema examples/issue-858.json

./schema-check examples/issue-895.json --prefix '{"k":"abcd' -o .cache/examples/impossible.json
./schema-check verify .cache/examples/impossible.json --schema examples/issue-895.json
```

The first prefix has the three-byte completion `""}`. The second cannot be completed in the supported canonical language. It reaches a state with null distance; the certificate lets the verifier check that this nonaccepting region is closed under every byte transition.

Use `--prefix-file prefix.bin` for raw bytes. No newline is stripped. Use `--prefix-hex 22f09f` for bytes that end inside a UTF-8 character. These options and `--prefix` are mutually exclusive. `--prefix ''` explicitly asks about the empty prefix. Without a prefix option, the `prefix` result is null.

## Read the JSON

|Field|Meaning|
|---|---|
|`support`|`SUPPORTED`, `UNSUPPORTED`, `UNKNOWN`, `INVALID_INPUT`, or `ERROR`|
|`language.empty`|A boolean only for supported inputs; otherwise null|
|`language.shortest_example`|A shortest canonical JSON encoding, or null for an empty/undecided language|
|`prefix.can_complete`|Whether the exact supplied bytes have a canonical continuation|
|`prefix.shortest_completion`|A shortest suffix, including a zero-byte suffix if the prefix is complete|
|`prefix.trace` / `prefix.evidence`|The replayed state path and its distance or closed-region claim|
|`certificate`|The full automaton and its language, distance, and completion evidence|

Words have `bytes`, `hex`, `utf8`, and `length_bytes` fields. **Bytes are authoritative.** A suffix beginning with a UTF-8 continuation byte has `utf8: null`; this does not mean the suffix is missing. Equal-length shortest results use byte lexicographic order.

An empty language, an impossible prefix, and an already complete prefix are successful answers, not command failures. A resource stop is `UNKNOWN`, never an emptiness proof. Unsupported/unknown artifacts do not contain mathematical certificates; verifying them returns `NOT_APPLICABLE`, not `PASS`.

|Exit code|Meaning|
|---|---|
|0|Supported answer, or successful verification|
|1|Verification failed, or an internal error|
|2|Invalid check input or command arguments|
|3|Unsupported/unknown check, or unknown/not-applicable verification|

`verify --schema file.json` binds the artifact to that exact UTF-8 document as well as the normalized schema. A whitespace-only edit changes the document hash. Without `--schema`, verification is about the schema captured in the artifact; it does not authenticate who supplied it. The artifact format is versioned as `schema-check/v1`.

## Supported language

The checker accepts a restricted Draft 2020-12 fragment when it can establish either a finite candidate domain or a necessary string guard:

- Finite `enum`/`const`, including nested objects/arrays, integer values, booleans, null, and Unicode scalar strings. Deep equality distinguishes booleans from numbers.
- Finite closed objects with `type: object`, `properties`, `required`, and explicit `additionalProperties: false`; each property needs a finite value domain. A finite guard can also constrain object keywords in a conjunction.
- Strings, including unbounded length, with `minLength`/`maxLength` and the full-string pattern fragment: anchored literals, positive character classes/ranges with one `*`, `+`, `?`, `{m}`, `{m,n}`, or `{m,}` quantifier, and single ASCII-letter `*`, `+`, or `?` forms.
- `allOf`, `anyOf`, exact `oneOf`, and `not` where the necessary guards can be established. `not` does not silently restrict the universe to strings or to mentioned values.

Open objects, unbounded object children, general arrays, `$ref`, `patternProperties`, general regular expressions, and fractional schema numbers are outside this v1 implementation. Some guarded numeric/type/size conditions are evaluated over finite candidates; they are not general numeric or object solvers. A valid schema outside the implementation returns `UNSUPPORTED`. Known keyword shape errors and duplicate JSON keys return `INVALID_INPUT`. This is not a complete JSON Schema metaschema validator.

The accepted encodings are **canonical compact JSON**: recursively sorted object keys, integer-valued numbers in integer notation, Python JSON escapes for quote/backslash/control characters, raw UTF-8 for other Unicode scalars, and no whitespace. Equivalent key orders, extra whitespace, alternate number forms, and alternate string escapes are not all accepted. “Cannot complete” is relative to this canonical language; it does not rule out a different JSON serialization. Schema integer inputs are read exactly, including `1e23`; fractional inputs are rejected rather than rounded.

## Units and limits

Distances are UTF-8 **byte** counts, not model token counts or Unicode character counts. String length constraints count Unicode code points. The tool does not prove reachability in a particular model vocabulary, correctness for all JSON Schema, or termination of arbitrary sampling. It does not repair or replace a serving backend.

Defaults are 100,000 automaton states, two million stored completion-byte entries, 1 MiB schema/prefix input, and 32 MiB artifact input/output. Each isolated worker has a 30-second CPU/wall budget; `--timeout` may lower the wall budget. POSIX `ps`, when available, supports a 1.5 GiB RSS precaution stop. Linux also applies a 2 GiB address-space limit. The RSS guard is polled; macOS has no claimed hard address-space cap. Scheduling and monitoring add small wall-time latency. Resource stops produce `UNKNOWN`.

## Verification and tests

The verifier checks the language construction and all-byte closure, shortest distances, actual suffix replay, and the claims displayed in the artifact. It blocks reads of producer files. The shared meaning/encoding kernels remain trusted; this is not a second independent Schema semantics implementation or a formal proof. See [TRUST.md](TRUST.md).

```sh
python3 -B tests/run.py
```

The test report is written to `.cache/TESTS.json`; temporary test files also stay under `.cache/`. These output locations keep the package manifest valid after running the examples and tests.

The frozen corpus has 134 schemas, 83 supported results, and 278 fixture-value checks. The tests verify every new supported artifact, replay 83 original certificates, reject nine evidence mutations, and verify a detached copy after all producer files have been removed. They also exercise partial UTF-8, raw newlines, empty languages, impossible prefixes, invalid input, resource stops, and an optimized parent interpreter. No external backend is needed for these tests.

External comparison is optional and documented separately in [COMPARISON.md](COMPARISON.md). Its package versions do not affect the CLI dependency set. Test Suite fixtures retain their MIT notice in `tests/SUITE-LICENSE` and `comparison/SUITE-LICENSE`. Project-owned code is Apache-2.0; original documentation and generated evidence are CC-BY-4.0. See the package [LICENSE](../../../LICENSE) and [third-party notices](../../../THIRD-PARTY-NOTICES.md).
