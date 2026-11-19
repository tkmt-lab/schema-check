# What the evidence establishes

For a supported schema, the artifact describes a total deterministic automaton over byte values 0–255. Missing edges go to its explicit dead sink. The target language is the canonical JSON language in the README, not every equivalent serialization.

The producer uses a finite-domain trie, a symbolic string NFA followed by determinization, or the preserved finite fallback. `schema-check verify` uses a different entry point in a fresh isolated interpreter. It never imports the producer modules and installs an audit hook that rejects reading `generate.py`, its bytecode, or `nfa_builder.py`. A detached-copy test removes all those files before verification.

For finite domains, the checker reconstructs the expected language from the shared finite meaning kernel and checks product equivalence over all 256 bytes. Product states are queued once and bounded. For symbolic strings, it validates character-state annotations, the local NFA structure, subset transitions, acceptance, and reachability. The producer-only NFA builder is separate from the shared reference file and absent from the verification import path. The finite fallback uses its own checker.

At every accepting state the distance is zero. At every other state, a finite distance must be the minimum finite child distance plus one; a null distance has no finite-distance child. A finite suffix has exactly the declared length, is the lexicographically smallest at that length, and replays to acceptance. Null-distance states therefore form a closed region without acceptance. The initial state gives emptiness and a shortest example. Replaying the supplied prefix reaches the state used by the completion or impossibility claim.

The public verifier also checks byte and integer types, state/entry limits, the captured schema digest, an optional external document binding, the prefix path, and all displayed semantic claims. It compares deterministic JSON representations so booleans cannot pass as integer claims. Unknown or unsupported outputs have no such mathematical certificate and cannot receive `PASS`.

Shared trusted code includes the declared Schema semantics, finite guards, canonical encoding, symbolic character semantics and Unicode encoding boxes, input normalization, and output projection. The verifier checks construction from those definitions; it does not independently establish that every definition implements all of JSON Schema. The next3 evidence and predicate tests support the declared fragment, not universal conformance.

The schema document digest binds exact input bytes only when compared with an independently supplied document. A self-contained artifact can establish a claim about its captured schema, but it is not a signature or an authenticity certificate.

No external decoder is imported by either public command.
