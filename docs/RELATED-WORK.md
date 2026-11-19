# Related work

Saibo Geng, Hudson Cooper, Michał Moskal, Samuel Jenkins, Julian Berman, Nathan Ranchin, Robert West, Eric Horvitz and Harsha Nori. *JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models*. [arXiv:2501.10868v3](https://arxiv.org/abs/2501.10868v3), 2025.

The paper evaluates empirical coverage and output compliance on a large real-world schema collection. Section 5 and Appendix C distinguish empirical, true and implementation-based theoretical coverage; we do not characterize it as ignoring language-level correctness. The [workshop version](https://openreview.net/forum?id=FKOaJqKoio), titled *JSONSchemaBench: Evaluating Constrained Decoding with LLMs on Efficiency, Coverage and Quality*, is associated with the ICML 2025 ES-FoMo III workshop, rather than being identified here as an ICML main-conference paper.

This packet's exact equivalence check is between its generated canonical reference automaton and the declared supported semantics. Its external-backend comparisons use finite probes. It therefore supplies a restricted reference-language inspection component; it does not certify the full language of arbitrary external backends. No overall superiority or priority is claimed.
