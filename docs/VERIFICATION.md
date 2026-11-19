# What verification establishes

`verify.py` checks every saved v2 certificate and each of the 83 token certificates for each pinned vocabulary. The token workers also recheck all 83 underlying v1 byte certificates, so their repeated checks are not three independent semantic implementations. Non-supported v2 records are checked as status-only records and never promoted to mathematical certificates.

The byte verification entry validates the schema/document binding, canonical language construction/equivalence, all-byte transition closure, shortest distances, suffix replay and displayed claims. The token entry validates the byte input, quotient, all ordinary-token transitions, distances and query witnesses. Verification runs in separate processes with producer-file access blocked. A detached-copy control physically removes generate.py and nfa_builder.py files before calling the v2 verification entry. This demonstrates separation of code entry points, not independence of every shared routine.

The shared trust boundary includes canonical JSON encoding, finite-domain/guard semantics, the numeric feature transitions, byte reference semantics, vocabulary conversion, and the declared query helpers. The frozen CORRECTNESS.md/TRUST.md files preserve the detailed earlier arguments. The arguments are prose and executable checks, rather than proof-assistant formalizations. A local PASS is not external independent review, general JSON Schema conformance or novelty certification.

The default replay additionally checks four public examples, a GPT-2 public round trip, refusal of a v2 artifact by the v1 token component, rejection of modified evidence and the producer-removed copy. It runs one computational worker at a time. Polling checks the RSS of the orchestrator and descendants, with a 1.5GiB precaution stop below 2GiB; Linux also limits each worker's address space. macOS does not have a claimed hard address-space cap in this workflow. Stops fail verification, retain their reason, and are never turned into empty-language proofs. Assertions must remain enabled.

A successful run hashes saved external comparison observations; it does not rerun external backends. Those observations require the optional pinned environment and the separate reproduction recipe. The manifest detects byte changes, not a malicious replacement of both payload and manifest; it is not a signature. Producer-removed checking and hashes do not eliminate trust in Python, the implementation kernels or the operating system.

## Reference-language checking and external-tool inspection

Whole-language equivalence is checked for the schema-derived reference automaton in the supported canonical fragment. External llguidance/XGrammar/Outlines behavior is inspected with recorded finite probes; no observed invalid acceptance is not a whole-backend equivalence certificate. This distinction applies to every tool, including the zero-observation llguidance row.

The default replay also recomputes the 369-row observation classification from the frozen records and its source annotation snapshot. It checks that issue links and category totals match those records; it does not establish that maintainers accepted a report or that a released fix exists.
