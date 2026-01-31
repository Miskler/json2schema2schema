from json2schema.core.pipeline import Converter
from json2schema.core.comparators import TypeComparator, FormatComparator
import json

conv = Converter()
conv.add_schema({"type": "object", "properties": {"name": {"type": "integer"}}})
conv.add_schema({"type": "object", "properties": {"name": {"type": "string"}}})
conv.add_json({"name": "Bob"})
conv.add_json({
    "name": "Bob",
    "email": "alice@example.com",
    "identifier": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    "created": "2024-01-31"
})
conv.register(TypeComparator())
conv.register(FormatComparator())
print(json.dumps(conv.run(), indent=2, ensure_ascii=False))
