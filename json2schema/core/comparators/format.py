import re
from typing import Optional, Any, Dict
from .template import Comparator, ProcessingContext, ComparatorResult

class FormatDetector:
    """Глобальный детектор форматов. Расширяем — просто добавляем в _registry."""

    _registry = {
        "string": {
            re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"): "email",
            re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
                re.I,
            ): "uuid",
            re.compile(r"^\d{4}-\d{2}-\d{2}$"): "date",
            re.compile(
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
            ): "date-time",
            re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.I): "uri",
            re.compile(
                r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}" r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
            ): "ipv4",
        }
    }

    @classmethod
    def detect(cls, value: Any, type_hint: str = "string") -> Optional[str]:
        patterns = cls._registry.get(type_hint, {})
        for pattern, name in patterns.items():
            if pattern.fullmatch(str(value)):
                return name
        return None

class FormatComparator(Comparator):
    name = "format"

    def can_process(self, ctx: ProcessingContext, env: str, prev_result: Dict) -> bool:
        # Форматы допустимы ТОЛЬКО если тип уже зафиксирован как string
        return prev_result.get("type") == "string"

    def process(
        self,
        ctx: ProcessingContext,
        env: str,
        prev_result: Dict
    ) -> ComparatorResult:

        format_map: Dict[str, set[int]] = {}

        # 1. Форматы, явно объявленные в схемах
        for s in ctx.schemas:
            if isinstance(s.content, dict) and "format" in s.content:
                f = s.content["format"]
                format_map.setdefault(f, set()).add(s.id)

        # 2. Форматы, детектированные из JSON-значений
        for j in ctx.jsons:
            detected = FormatDetector.detect(j.content, type_hint="string")
            if detected:
                format_map.setdefault(detected, set()).add(j.id)

        if not format_map:
            return None, None

        variants = [
            {
                "format": fmt,
                "j2sElementTrigger": sorted(ids),
            }
            for fmt, ids in format_map.items()
        ]

        # sealed → формат должен быть один
        if ctx.sealed:
            return variants[0], None

        if len(variants) == 1:
            return variants[0], None

        # Конфликт форматов → anyOf
        return None, variants

