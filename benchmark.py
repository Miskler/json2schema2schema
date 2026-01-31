import time
from statistics import mean

# ===== json2schema (твоя библиотека) =====
from json2schema.core.pipeline import Converter
from json2schema.core.comparators import (
    TypeComparator,
    FormatComparator,
    RequiredComparator,
    FlagMaker,
    EmptyComparator,
    DeleteElement,
)

# ===== genson =====
from genson import SchemaBuilder


# ===== входные данные =====
SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "object",
            "properties": {
                "name": {"type": "integer"}
            }
        }
    }
}

JSONS = [
    [{"name": "fdfddfm"}],
    ["fdfddfm"],
    {"name": "fdfddfm"},
    [{"name": "https://dddd.ru"}],
    [{"empty": {}}],
    {"name": "https://dddd.ru"},
    {
        "name": "alice@example.com",
        "email": "alice@example.com",
        "identifier": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
        "created": "2024-01-31"
    }
]

RUNS = 2000


# ===== json2schema прогон =====
def run_json2schema():
    conv = Converter()
    conv.add_schema(SCHEMA)

    for j in JSONS:
        conv.add_json(j)

    conv.register(TypeComparator())
    conv.register(FormatComparator())
    conv.register(RequiredComparator())
    #conv.register(FlagMaker())
    conv.register(EmptyComparator())
    conv.register(DeleteElement())

    return conv.run()


# ===== genson прогон =====
def run_genson():
    builder = SchemaBuilder()
    builder.add_schema(SCHEMA)

    for j in JSONS:
        builder.add_object(j)

    return builder.to_schema()


# ===== бенчмарк =====
def benchmark(fn, runs):
    timings = []

    for _ in range(runs):
        start = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - start)

    return timings


if __name__ == "__main__":
    print(f"Прогонов: {RUNS}\n")

    t1 = benchmark(run_json2schema, RUNS)
    t2 = benchmark(run_genson, RUNS)

    avg_json2schema = mean(t1)
    avg_genson = mean(t2)

    print("=== РЕЗУЛЬТАТЫ ===")
    print(f"json2schema : {avg_json2schema:.6f} сек (avg)")
    print(f"genson      : {avg_genson:.6f} сек (avg)")

    if avg_genson > 0:
        print(f"\njson2schema / genson = {avg_json2schema / avg_genson:.2f}x")
    
    print("\n")
    from jsonschema_diff import JsonSchemaDiff, ConfigMaker
    from jsonschema_diff.color import HighlighterPipeline
    from jsonschema_diff.color.stages import (
        MonoLinesHighlighter, PathHighlighter, ReplaceGenericHighlighter,
    )
    prop = JsonSchemaDiff(
        config=ConfigMaker.make(),
        colorize_pipeline=HighlighterPipeline([
            MonoLinesHighlighter(),
            ReplaceGenericHighlighter(),
            PathHighlighter(),
        ])
    )

    prop.compare( # Function accepts both file path and schema dict itself // can be combined
        old_schema=run_json2schema(),
        new_schema=run_genson()
    )

    # Теперь можно вывести
    prop.print(with_legend=False)
