from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToDelete:
    content: int | float | str | list | dict = ""
    comparator_trigger: "Comparator" = None

@dataclass
class Resource:
    id: int
    type: str
    content: Any

@dataclass
class ProcessingContext:
    schemas: List[Resource]
    jsons: List[Resource]
    sealed: bool = False

ComparatorResult = Tuple[Optional[Dict[str, ToDelete | Any]], Optional[List[Dict]]]

class Comparator:
    name = "base"
    def can_process(self, ctx: ProcessingContext, env: str, prev_result: Dict) -> bool:
        return False
    def process(self, ctx: ProcessingContext, env: str, prev_result: Dict) -> ComparatorResult:
        return None, None
