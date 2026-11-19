"""Compact saved schema-check witness; no model or tokenizer download."""
import importlib.metadata
import json

from jsonschema import Draft202012Validator
import xgrammar as xg

SCHEMA = {
    "type": "object",
    "properties": {"a": {"type": "boolean"}},
    "required": ["missing"],
    "additionalProperties": False,
}
TEXT = '{"a":false}'
print("xgrammar", importlib.metadata.version("xgrammar"))
print("schema_valid", Draft202012Validator(SCHEMA).is_valid(json.loads(TEXT)))
info = xg.TokenizerInfo(
    [bytes([i]) for i in range(256)] + [b"<eos>"],
    vocab_type=xg.VocabType.RAW,
    stop_token_ids=[256],
)
compiler = xg.GrammarCompiler(info, max_threads=1, cache_enabled=False)
compiled = compiler.compile_json_schema(json.dumps(SCHEMA, sort_keys=True), strict_mode=False)
matcher = xg.GrammarMatcher(compiled)
accepted = all(matcher.accept_token(token) for token in TEXT.encode("utf-8"))
accepted = accepted and matcher.accept_token(256) and matcher.is_terminated()
print("accepted_with_EOS", bool(accepted))
