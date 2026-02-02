import argparse
import json
import sys
import time

from rich.console import Console

from . import Converter, PseudoArrayHandler
from .comparators import (
    DeleteElement,
    EmptyComparator,
    FormatComparator,
    RequiredComparator,
)

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate JSON Schema from JSON input using json2schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  json2schema input.json -o schema.json
  json2schema input1.json input2.json --title "My Data"
  cat input.json | python -m your_package.script -
  json2schema --title "Example" < input.json
  json2schema dir/file1.json dir/file2.json -o schema.json
        """,
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Пути к входным JSON-файлам. Используйте '-' для чтения из stdin. "
        "Если аргументы не указаны — читает из stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Путь к выходному файлу JSON Schema. Если не указан — вывод в stdout.",
    )
    parser.add_argument(
        "--base-of",
        choices=["anyOf", "oneOf", "allOf"],
        default="anyOf",
        help="Комбинатор для различающихся типов (по умолчанию: anyOf).",
    )
    parser.add_argument(
        "--no-pseudo-array", action="store_true", help="Отключить обработку pseudo-массивов."
    )

    args = parser.parse_args()

    # Сбор входных данных
    datas = []
    if not args.inputs:
        # Автоматическое чтение из stdin
        try:
            data = json.load(sys.stdin)
            datas.append(data)
        except json.JSONDecodeError as e:
            console.print(f"[red]Ошибка чтения JSON из stdin: {e}[/red]")
            sys.exit(1)
    else:
        for input_path in args.inputs:
            if input_path == "-":
                try:
                    data = json.load(sys.stdin)
                    datas.append(data)
                except json.JSONDecodeError as e:
                    console.print(f"[red]Ошибка чтения JSON из stdin: {e}[/red]")
                    sys.exit(1)
            else:
                try:
                    with open(input_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    datas.append(data)
                except FileNotFoundError:
                    console.print(f"[red]Файл не найден: {input_path}[/red]")
                    sys.exit(1)
                except json.JSONDecodeError as e:
                    console.print(f"[red]Некорректный JSON в файле {input_path}: {e}[/red]")
                    sys.exit(1)

    if not datas:
        console.print("[red]Не предоставлено ни одного валидного JSON.[/red]")
        sys.exit(1)

    # Конвертер
    pseudo_handler = None if args.no_pseudo_array else PseudoArrayHandler()
    conv = Converter(pseudo_handler=pseudo_handler, base_of=args.base_of)

    for data in datas:
        conv.add_json(data)

    # Компараторы
    conv.register(FormatComparator())
    conv.register(RequiredComparator())
    conv.register(EmptyComparator())
    conv.register(DeleteElement())
    if not args.no_pseudo_array:
        conv.register(DeleteElement("isPseudoArray"))

    # Генерация схемы
    start_time = time.time()
    try:
        result = conv.run()
    except Exception as e:
        console.print(f"[red]Ошибка при генерации схемы: {e}[/red]")
        sys.exit(1)
    elapsed = round(time.time() - start_time, 4)

    # Вывод результата
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Схема успешно записана в {args.output}[/green]")
        except Exception as e:
            console.print(f"[red]Ошибка записи файла {args.output}: {e}[/red]")
            sys.exit(1)
    else:
        console.print(result)

    # Информация о выполнении
    instances_word = "экземпляр" if len(datas) == 1 else "экземпляров"
    console.print(f"Сгенерировано из {len(datas)} {instances_word} JSON.")
    console.print(f"Затраченное время: {elapsed} сек.")


if __name__ == "__main__":
    main()
