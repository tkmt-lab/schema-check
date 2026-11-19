# Evidence and trust boundary

The finite guard returns a superset of every accepted value, never an arbitrary
test sample. A typed bounded integer interval has finitely many candidates.
A bounded number interval with a decimal multiple has a finite rational grid.
Finite arrays enumerate products/permutations of a complete finite item guard.
Uniqueness uses semantic JSON equality. The final predicate filters candidates.

The numeric reference tracks lexical validity, sign, integer/fraction position,
comparison with each schema constant, and residues for decimal multiples.
Lengths saturate beyond all relevant comparison positions. A multiple has
finite decimal precision; after that many fractional positions, a canonical
value with a nonzero last digit cannot be divisible by it. Canonical numeric
strings have no redundant trailing zero, so fractional versus integer values
is decidable from the lexical state. The parser/model never round through
binary64 or the default Decimal arithmetic context.

The producer builds a word trie or explores numeric feature states and computes
reverse shortest distances. The separate checker blocks reads/imports of
generate.py and nfa_builder.py. It compares the submitted automaton with either
an independently constructed finite-word trie or the shared numeric model over
all 256 byte transitions in a reachable product. It checks all submitted states
are reached in that product, acceptance agrees, distance equations hold, null
regions are closed, completions replay, and equal-length ties use byte order.
The public verifier also checks schema/document hashes and every projected
language/prefix claim.

Finite guards, numeric feature semantics, encoding, and the previous string
meaning kernel are shared trust, not independently derived mathematical
semantics. The exact-Fraction jsonschema oracle checks 34,277 finite candidates,
fixtures and numeric samples on the 40 newly compared schemas; sampling is not
a proof for all rational values. Corpus fixtures, masks, and third-party
acceptance are observations, not independent proofs of the reference kernel.
The arguments are prose and executable checks, rather than machine-checked proofs.
