# Fixed-version observations and their provenance

These results illustrate schema-preservation inspection. They are case records, not a ranking or a count of distinct bugs. Each tool uses the same columns and the same 123 supported reference schemas.

|Tool|Version|Case records|Compile refusals|Invalid acceptance records|Existing issue/PR|Official repository record|Newly reported within saved invalid rows|
|---|---|---:|---:|---:|---:|---:|---:|
|llguidance|1.9.1|123|26|0|0|0|0|
|XGrammar|0.2.8|123|8|58|46|12|0|
|outlines-core|0.2.14|123|42|17|16|0|1|

Zero means no accepted-invalid probe was observed in this fixed set; it is not a proof of backend-language equivalence or general conformance. Compile refusals include correct refusals of empty languages and are not automatically errors. Warnings are preserved.

**Existing issue/PR** includes the empty-enum report in Outlines PR #269; it is explicitly a PR, not a fabricated issue number. **Official repository record** includes merged PRs #672, #134 and #670 (warning/fallback behavior); it does not assert that the same limitation appears in a user manual or that every invocation warns. Closed issue status alone does not mean a released version fixed the behavior.

The source annotation snapshot has 85 normalized tool/schema pairs from several saved audits; the table above uses the 123-case native matrix instead. Root annotations are removed only to join provenance. The actual schema, input, runner and observed bytes are unchanged. An issue-family match is not a claim that each exact input had already appeared in the issue.

## Newly reported examples

|Tool|Fixed version|Report|Witness in the original invalid-acceptance rows?|
|---|---|---|---|
|llguidance|1.9.1|None (0)|No new report|
|XGrammar|0.2.8|[#1029](https://github.com/mlc-ai/xgrammar/issues/1029)|No: supplemental witness for a schema already in this matrix|
|outlines-core|0.2.14|[#277](https://github.com/dottxt-ai/outlines-core/issues/277)|Yes|

The XGrammar #1029 schema is already in the 123-case matrix, but its violating value was not in the original probe set. The supplemental witness is not added to the original 58. Outlines #277 is the anyOf/required witness already among the 17. Both reports were filed by the project on 2026-11-02; linking them does not establish bug priority or maintainer confirmation. Their standalone reproducers are in comparison/reports/.

## Per-case provenance

The complete 369 tool/schema rows, including all zero-observation and refusal rows, are in [observation-map.csv](../comparison/observation-map.csv) and [observation-map.json](../comparison/observation-map.json). The observed invalid-acceptance rows below link their issue or official record.

|Tool|Version|Case|Class|Family|References|
|---|---|---|---|---|---|
|XGrammar|0.2.8|pattern-length|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|unicode-length|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|oneof-overlap|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|oneof-identical|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|oneof-not|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|not-global|OFFICIAL_REPOSITORY_RECORD|unsupported-not|[files](https://github.com/mlc-ai/xgrammar/pull/134/files), [858](https://github.com/mlc-ai/xgrammar/issues/858)|
|XGrammar|0.2.8|lift-pattern-0|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift-minLength-0|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift-minLength-1|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift-maxLength-0|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift-maxLength-1|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite-oneOf-1|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|suite-oneOf-2|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|suite-not-4|OFFICIAL_REPOSITORY_RECORD|unsupported-not|[files](https://github.com/mlc-ai/xgrammar/pull/134/files), [858](https://github.com/mlc-ai/xgrammar/issues/858)|
|XGrammar|0.2.8|suite-not-5|OFFICIAL_REPOSITORY_RECORD|unsupported-not|[files](https://github.com/mlc-ai/xgrammar/pull/134/files), [858](https://github.com/mlc-ai/xgrammar/issues/858)|
|XGrammar|0.2.8|infinite-star|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|unicode-unbounded|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|length-pattern-cap|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|length-repeat-empty|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|infinite-overlapping-oneof|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|infinite-not|OFFICIAL_REPOSITORY_RECORD|unsupported-not|[files](https://github.com/mlc-ai/xgrammar/pull/134/files), [858](https://github.com/mlc-ai/xgrammar/issues/858)|
|XGrammar|0.2.8|lift3-properties-0|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-properties-3|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-properties-5|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-required-0|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-required-3|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-required-4|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-additionalProperties-2|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-additionalProperties-3|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|lift3-additionalProperties-5|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|issue-xg858-original|EXISTING_ISSUE_OR_PR|combinator-sibling-loss|[858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|issue-xg895-original|EXISTING_ISSUE_OR_PR|pattern-plus-length|[895](https://github.com/mlc-ai/xgrammar/issues/895), [966](https://github.com/mlc-ai/xgrammar/issues/966), [896](https://github.com/mlc-ai/xgrammar/pull/896)|
|XGrammar|0.2.8|issue-vllm56556-finite-derived|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-exclusiveMaximum-0-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-exclusiveMaximum-0-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-exclusiveMinimum-0-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-exclusiveMinimum-0-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-maximum-0-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-maximum-0-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-maximum-1-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-maximum-1-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-minimum-0-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-minimum-0-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-minimum-1-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-minimum-1-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-0-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-0-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-1-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-1-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-2-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-2-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-4-typed-number|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|suite7-multipleOf-4-typed-integer|EXISTING_ISSUE_OR_PR|multi-branch-allOf|[937](https://github.com/mlc-ai/xgrammar/issues/937), [858](https://github.com/mlc-ai/xgrammar/issues/858), [859](https://github.com/mlc-ai/xgrammar/pull/859)|
|XGrammar|0.2.8|integer-multiple-rational|OFFICIAL_REPOSITORY_RECORD|fractional-integer-multipleOf|[670](https://github.com/mlc-ai/xgrammar/pull/670), [files](https://github.com/mlc-ai/xgrammar/pull/670/files)|
|XGrammar|0.2.8|number-oneof-divisibility|OFFICIAL_REPOSITORY_RECORD|oneOf-permissive-fallback|[672](https://github.com/mlc-ai/xgrammar/pull/672), [files](https://github.com/mlc-ai/xgrammar/pull/672/files)|
|XGrammar|0.2.8|array-unique-finite|EXISTING_ISSUE_OR_PR|uniqueItems|[932](https://github.com/mlc-ai/xgrammar/issues/932)|
|XGrammar|0.2.8|array-unique-impossible|EXISTING_ISSUE_OR_PR|uniqueItems|[932](https://github.com/mlc-ai/xgrammar/issues/932)|
|XGrammar|0.2.8|array-rational-items|EXISTING_ISSUE_OR_PR|uniqueItems|[932](https://github.com/mlc-ai/xgrammar/issues/932)|
|outlines-core|0.2.14|pattern-length|EXISTING_ISSUE_OR_PR|pattern-plus-length|[274](https://github.com/dottxt-ai/outlines-core/issues/274), [276](https://github.com/dottxt-ai/outlines-core/pull/276)|
|outlines-core|0.2.14|oneof-overlap|EXISTING_ISSUE_OR_PR|oneOf-exactly-one|[156](https://github.com/dottxt-ai/outlines-core/issues/156)|
|outlines-core|0.2.14|oneof-identical|EXISTING_ISSUE_OR_PR|oneOf-exactly-one|[156](https://github.com/dottxt-ai/outlines-core/issues/156)|
|outlines-core|0.2.14|length-repeat-empty|EXISTING_ISSUE_OR_PR|pattern-plus-length|[274](https://github.com/dottxt-ai/outlines-core/issues/274), [276](https://github.com/dottxt-ai/outlines-core/pull/276)|
|outlines-core|0.2.14|infinite-not|EXISTING_ISSUE_OR_PR|unsupported-not|[261](https://github.com/dottxt-ai/outlines-core/issues/261)|
|outlines-core|0.2.14|suite3-enum-14|EXISTING_ISSUE_OR_PR|empty-enum|[269](https://github.com/dottxt-ai/outlines-core/pull/269), [261](https://github.com/dottxt-ai/outlines-core/issues/261)|
|outlines-core|0.2.14|object-required-impossible|EXISTING_ISSUE_OR_PR|required-outside-properties|[152](https://github.com/dottxt-ai/outlines-core/issues/152)|
|outlines-core|0.2.14|issue-xg858-original|NEWLY_REPORTED|anyOf-required-with-sibling-properties|[277](https://github.com/dottxt-ai/outlines-core/issues/277), [156](https://github.com/dottxt-ai/outlines-core/issues/156), [152](https://github.com/dottxt-ai/outlines-core/issues/152), [858](https://github.com/mlc-ai/xgrammar/issues/858)|
|outlines-core|0.2.14|issue-xg895-original|EXISTING_ISSUE_OR_PR|pattern-plus-length|[274](https://github.com/dottxt-ai/outlines-core/issues/274), [276](https://github.com/dottxt-ai/outlines-core/pull/276)|
|outlines-core|0.2.14|suite7-multipleOf-4-typed-number|EXISTING_ISSUE_OR_PR|allOf-intersection|[259](https://github.com/dottxt-ai/outlines-core/issues/259)|
|outlines-core|0.2.14|number-finite-tenths|EXISTING_ISSUE_OR_PR|numeric-bounds|[147](https://github.com/dottxt-ai/outlines-core/issues/147), [260](https://github.com/dottxt-ai/outlines-core/pull/260), [files](https://github.com/dottxt-ai/outlines-core/pull/260/files)|
|outlines-core|0.2.14|number-exclusive-empty|EXISTING_ISSUE_OR_PR|numeric-bounds|[147](https://github.com/dottxt-ai/outlines-core/issues/147), [260](https://github.com/dottxt-ai/outlines-core/pull/260), [files](https://github.com/dottxt-ai/outlines-core/pull/260/files)|
|outlines-core|0.2.14|integer-fractional-window-empty|EXISTING_ISSUE_OR_PR|numeric-bounds|[147](https://github.com/dottxt-ai/outlines-core/issues/147), [260](https://github.com/dottxt-ai/outlines-core/pull/260), [files](https://github.com/dottxt-ai/outlines-core/pull/260/files)|
|outlines-core|0.2.14|integer-multiple-rational|EXISTING_ISSUE_OR_PR|multipleOf|[261](https://github.com/dottxt-ai/outlines-core/issues/261)|
|outlines-core|0.2.14|array-unique-finite|EXISTING_ISSUE_OR_PR|uniqueItems|[261](https://github.com/dottxt-ai/outlines-core/issues/261), [196](https://github.com/dottxt-ai/outlines-core/issues/196)|
|outlines-core|0.2.14|array-unique-impossible|EXISTING_ISSUE_OR_PR|uniqueItems|[261](https://github.com/dottxt-ai/outlines-core/issues/261), [196](https://github.com/dottxt-ai/outlines-core/issues/196)|
|outlines-core|0.2.14|array-rational-items|EXISTING_ISSUE_OR_PR|uniqueItems|[261](https://github.com/dottxt-ai/outlines-core/issues/261), [196](https://github.com/dottxt-ai/outlines-core/issues/196)|
