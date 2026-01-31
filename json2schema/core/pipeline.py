#!/usr/bin/env python3
from typing import Any, Dict, List
from .comparators.template import Resource, Comparator, ProcessingContext

def merge(a: Dict, b: Dict) -> Dict:
    r = dict(a)
    r.update(b)
    return r


class Converter:
    def __init__(self):
        self._schemas: List[Resource] = []
        self._jsons: List[Resource] = []
        self._comparators: List[Comparator] = []
        self._id = 0

    def add_schema(self, s: dict):
        self._schemas.append(Resource(self._id, "schema", s))
        self._id += 1

    def add_json(self, j: Any):
        self._jsons.append(Resource(self._id, "json", j))
        self._id += 1

    def register(self, c: Comparator):
        self._comparators.append(c)

    def _collect_prop_names(self, schemas: List[Resource], jsons: List[Resource]) -> List[str]:
        """
        Собираем имена свойств из схем (properties) и из json-объектов (ключи словарей).
        Возвращаем отсортированный детерминированный список.
        """
        names = set()
        # from schemas
        for s in schemas:
            if isinstance(s.content, dict) and "properties" in s.content and isinstance(s.content["properties"], dict):
                names.update(s.content["properties"].keys())
        # from jsons
        for j in jsons:
            if isinstance(j.content, dict):
                names.update(j.content.keys())
        return sorted(names)

    def _gather_property_candidates(self, schemas: List[Resource], jsons: List[Resource], prop: str):
        """
        Возвращаем два списка Resource:
        - s_out: для каждой схемы, которая содержит property -> вложенный schema с тем же id
        - j_out: для каждого json, где есть ключ prop -> значение с тем же id
        """
        s_out = []
        j_out = []
        for s in schemas:
            c = s.content
            if isinstance(c, dict) and "properties" in c and isinstance(c["properties"], dict) and prop in c["properties"]:
                s_out.append(Resource(s.id, "schema", c["properties"][prop]))
        for j in jsons:
            if isinstance(j.content, dict) and prop in j.content:
                j_out.append(Resource(j.id, "json", j.content[prop]))
        return s_out, j_out

    def _run_level(self, ctx: ProcessingContext, env: str, prev_result: Dict) -> Dict:
        node = dict(prev_result)

        # применяем компараторы в порядке регистрации; компараторы читают и пишут в node (prev_result)
        for comp in self._comparators:
            if not comp.can_process(ctx, env, node):
                continue
            g, alts = comp.process(ctx, env, node)
            if g:
                node.update(g)
            if alts:
                branches = []
                for alt in alts:
                    sealed_ctx = ProcessingContext(ctx.schemas, ctx.jsons, sealed=True)
                    # внутри ветви anyOf передаём текущее накопленное result (node) — оно служит базой
                    child = self._run_level(sealed_ctx, env + "/anyOf", node)
                    branches.append({**child, **alt})
                return {"anyOf": branches}

        # рекурсивно обходим properties — теперь имена берём и из схем, и из jsons
        prop_names = self._collect_prop_names(ctx.schemas, ctx.jsons)
        if prop_names:
            node.setdefault("properties", {})
            for name in prop_names:
                s_cands, j_cands = self._gather_property_candidates(ctx.schemas, ctx.jsons, name)
                sub_ctx = ProcessingContext(s_cands, j_cands, sealed=False)
                # при спуске prev_result для дочернего уровня начинаем с пустого словаря
                node["properties"][name] = self._run_level(sub_ctx, env + f"/properties/{name}", {})

        # items/arrays/etc можно аналогично расширить при необходимости

        return node

    def run(self):
        root_ctx = ProcessingContext(self._schemas, self._jsons, sealed=False)
        return self._run_level(root_ctx, "/", {})
