from typing import Dict, List, Optional, Tuple

from .template import Comparator, ProcessingContext, ToDelete


class DeleteElement(Comparator):
    """Визуально показывает где именно могут сработать компораторы"""

    name = "delete-element"
    attribute = ""

    def __init__(self, attribute: str = "j2sElementTrigger"):
        super().__init__()
        self.attribute = attribute

    def can_process(self, ctx: ProcessingContext, env: str, node: Dict) -> bool:
        # Обрабатываем объекты и массивы
        return self.attribute in node

    def process(
        self, ctx: ProcessingContext, env: str, node: Dict
    ) -> Tuple[Optional[Dict], Optional[List[Dict]]]:
        return {self.attribute: ToDelete(node.get(self.attribute, -1), self.name)}, None
