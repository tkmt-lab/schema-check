"""Compact saved schema-check witness; no model or tokenizer download."""
import importlib.metadata
import json

from jsonschema import Draft202012Validator
from outlines_core import Index, Vocabulary, json_schema

SCHEMA = {
    "type": "object",
    "properties": {"modifier": {"enum": ["", "dark"]}},
    "anyOf": [{"required": ["modifier"]}],
    "additionalProperties": False,
}
TEXT = "{}"
print("outlines-core", importlib.metadata.version("outlines-core"))
print("schema_valid", Draft202012Validator(SCHEMA).is_valid(json.loads(TEXT)))
regex = json_schema.build_regex_from_schema(json.dumps(SCHEMA, sort_keys=True))
vocabulary = Vocabulary(256, {bytes([i]): [i] for i in range(256)})
index = Index(regex, vocabulary)
state = index.get_initial_state()
accepted = True
for token in TEXT.encode("utf-8"):
    if token not in index.get_allowed_tokens(state):
        accepted = False
        break
    state = index.get_next_state(state, token)
accepted = accepted and index.is_final_state(state) and 256 in index.get_allowed_tokens(state)
print("accepted_with_EOS", bool(accepted))
print("regex", regex)
