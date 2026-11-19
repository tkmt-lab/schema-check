# Verification record

This record collects dated replay results and packaging history. The current checking method and trust boundary are described in [VERIFICATION.md](VERIFICATION.md); machine-readable source records are in [PROVENANCE.json](../PROVENANCE.json).

## Recorded offline replays

On 2026-11-05 UTC, the standard-library certificate replay and public examples passed on a fresh Linux copy. The environment was Linux 6.18.57 x86-64 with glibc 2.41 and Python 3.12.14. The inspection independently compared all 820 manifest entries with their file sizes and SHA-256 digests, and recorded no changes to the existing files after execution. External backend packages were not rerun.

On 2026-11-06 UTC, a further inspection of input commit `ae7d921dbe8a182a491aef3d9bdb657f9ba14e4c` ran all 13 standard README commands on a copy; every command exited with status 0, including the complete replay. The 824 existing packet files matched before and after execution, excluding `.cache/`. These file counts describe the inspected snapshots, before the later editorial changes. The optional external comparisons were again outside the replay.

The research archive retains the source reports and command logs. These reports are identified here for traceability; they are not bundled in the package:

|Archived report|SHA-256|
|---|---|
|`cloud-check-2026-11-05/REPORT.md`|`2c669b57d0d6b58b642bfe6e4d0ba3150b65a4eb88295cb866458edb3c06699e`|
|`prerelease-recheck2-2026-11-06/REPORT.md`|`48479305b41c2058109b58c6bf8f448ea760b8aa49d637f737c1b60d6b9c344f`|

The saved external-backend observations were obtained in the pinned macOS environment described in [COMPARISON.md](COMPARISON.md). The Linux replays above check the offline package; they are not new measurements of those backends.

## Source adaptations recorded on 2026-11-06

The `source_files` entries in [PROVENANCE.json](../PROVENANCE.json) record two tokenizer-metadata adaptations: `TOKENIZER-SOURCE.json` for GPT-2 and `TOKENIZERS.json` for T5/ALBERT. Their tokenizer paths were relocated to the bundled `data/tokenizers/` directory. Source URLs, revisions, sizes and tokenizer hashes were unchanged.

The same provenance record identifies the mathematical Python source input as commit `5060bf412`. The files supplied for the namespace revision, including earlier adaptations, are identified by `namespace_input_commit`, `source_id` and `source_sha256`; the current distributed files are identified by `path`, `sha256` and `bytes`. Historical external-backend sources in `next5/NATIVE-SOURCES.json` retain their original `input_commit` and `sha256`, with a public logical name in `source`; bundled derivatives have separate `packaged_path` and `packaged_sha256` fields. Package wrappers and check orchestration are also listed in the manifest. Later diagnostic-path redactions and wording-only changes are recorded under `publication_sanitization` and `release_wording_update`.

## Public namespace

The 2026-11-06 packaging revision adopted `components/schema-check/` and the
`schema-check-*` format labels throughout the entry points, producers, checkers
and saved evidence. These were naming changes: schemas, numeric results, token
graphs and byte-certificate digests retained their original values. Source logical
names and stable content identifiers were recorded in PROVENANCE; the private archive
retained the original-path correspondence. Third-party snapshots, revisions and
license texts retained their original bytes.

## AI-use evidence recorded on 2026-11-06

The earlier implementation and checking task instructions requested `gpt-6.1-sol` with high reasoning effort; the package-preparation instructions requested `gpt-6.1-terra` with medium reasoning effort. Those instructions establish requested settings, not the models that actually ran. They are therefore not used as confirmed runtime attribution in the README. The 2026-11-06 documentation revisions used Codex, with GPT-6-astra assisting text review.

## Retained v1 implementation: record dated 2026-11-02

The v1 packaging record described an internal release candidate and recorded no public release or upstream issue submission for that stage. It assigned publication and licensing decisions to internal coordination. Those statements described that stage, rather than the distribution or its later issue reports.

The v1 work was performed by one agent and did not replace the separate verification review. Relative to the original v1 source snapshot (identified by the archived, non-bundled `VENDORED.json`), it made four local changes:

1. It split the producer-only NFA builder from shared string semantics/encoding and adjusted the import.
2. It added aggregate completion-entry budgets to all three producers; exhaustion returned unknown rather than empty.
3. It deduplicated queued finite-verifier product states and bounded their count.
4. It added bounded public parsing, schema-shape checks, exact numeric normalization, process isolation, the result protocol, and separate query/output verification.

No supported result in the frozen 134-case corpus was lost, and all 83 original certificates replayed against the packaged checkers. That work replayed local engine/certificates and checked installed comparison package metadata; it did not rerun all three external backends. The comparison reproduced schema-level conditions from XGrammar #858 and #895; no new upstream issue was submitted during that stage. The later #1029 and #277 reports are described in the package README.

## Editorial history recorded on 2026-11-06

Release metadata, diagnostic-path redaction and the README PDF were revised on 2026-11-05. Reader introductions, bibliographic summaries and AI-use disclosure were revised on 2026-11-06. Dated verification and source-adaptation records were separated from the README; its PDF used resource citations in place of general acknowledgements. The public namespace revision preserved mathematical payloads and upstream snapshots.

On 2026-11-06, the retained v1 README was changed to describe its current role and link to the distribution licenses. Its trust document retained the shared-kernel boundary, while the input-snapshot change list and task attribution were moved to this record. The historical issue-submission statement was restricted to its original stage. The changelog was reduced to release contents. Mathematical code, schemas, certificates, numerical claims and saved backend observations were unchanged by these editorial changes.

The 2026-11-02 v2 correctness record stated that no independent agent or formal theorem prover had been used for that work. The original packet verification description likewise recorded no separate-agent review within that packaging task. On 2026-11-06, these task-specific statements were moved here; the current trust documents retained the shared semantic kernels and the distinction between executable checks, independent review and formal proof.

On 2026-11-02, the version-snapshot/baseline procedure was exercised with the fixed versions recorded in `comparison/reference-versions.json`.

The 2026-11-02 token corruption-check module recorded that no independent agent had been involved. On 2026-11-06, that attribution was moved here from its module docstring; all executable statements were preserved.

On 2026-11-06, inspection of the bundled v1 README workflows found that the
examples and test runner left four JSON outputs outside the manifest. The example
paths were changed to `.cache/examples/`, and the test report and temporary test
files were moved under `.cache/`. The manifest check retained its strict payload
comparison. Test assertions, schemas, certificates and saved observations were
unchanged.

The packaging work recorded on 2026-11-02 created no repository, pushed no
release, assigned no DOI and sent no external messages; release scheduling was
left to a separate publication step. On 2026-11-06, the internal task label and
scheduling fields were removed from the machine-readable provenance. Source
commits and original source digests were retained.
