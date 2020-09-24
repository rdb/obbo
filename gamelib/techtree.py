from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TechNode:
    model:str
    category:str
    cost:int
    power:int  # Negative number means consumer, positive delivery
    depends_on:Tuple[str] = field(default_factory=tuple)
    capacity:int = 0
    unlocked:bool = False


class TechTree:
    def __init__(self, treecfg:List[TechNode]):
        self._tree:List[TechNode] = treecfg
        self._tree_dict = {i.model: i for i in treecfg}

    def get_current(self, fltr:Optional[str] = None) -> Dict[str, List[str]]:
        tree = {}
        for i in self._tree:
            if fltr and i.category != fltr:
                continue
            unlocked = True
            for j in i.depends_on:
                if not self._tree_dict[j].unlocked:
                    unlocked = False
                    break
            if not unlocked:
                continue

            if i.category not in tree:
                tree[i.category] = []
            tree[i.category].append(i.model)
        return tree

    def get_build_cost(self, model:str) -> int:
        return self._get_node(model).cost

    def get_category(self, model:str):
        return self._get_node(model).category

    def get_capacity(self, model:str):
        return self._get_node(model).capacity

    def get_power(self, model:str):
        return self._get_node(model).power

    def unlock(self, model:str) -> None:
        self._tree_dict[model].unlocked = True

    def reset(self) -> None:
        for i in self._tree:
            i.unlocked = False

    def _get_node(self, model:str) -> TechNode:
        if model not in self._tree_dict:
            raise ValueError(f'Unknown model "{model}"')
        return self._tree_dict[model]
