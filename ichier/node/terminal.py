from __future__ import annotations
from typing import Any, Dict, Iterator, Optional, Literal, Tuple, Union

from .fig import Fig, FigCollection
from .net import bitInfoSplit
from .trace import traceByNet, Route

__all__ = [
    "Terminal",
    "TerminalCollection",
]


class Terminal(Fig):
    def __init__(
        self,
        name: Optional[str] = None,
        direction: Literal["input", "output", "inout"] = "inout",
    ) -> None:
        super().__init__(name)
        self.direction = direction

    def __repr__(self) -> str:
        return f"Terminal({self.name!r}, {self.direction!r})"

    @property
    def direction(self) -> str:
        return self.__direction

    @direction.setter
    def direction(self, value) -> None:
        if value not in ["input", "output", "inout"]:
            raise ValueError("direction must be 'input', 'output', or 'inout'")
        self.__direction = value

    def split(self) -> Tuple[str, Optional[int]]:
        return bitInfoSplit(self.name)

    def trace(self, depth: int = -1) -> Route:
        module = self.getModule()
        if module is None:
            raise ValueError("unbound terminal cannot trace")
        return traceByNet(module.nets[self.name], depth=depth)


class TerminalCollection(FigCollection):
    def _valueChecker(self, fig: Terminal) -> None:
        if not isinstance(fig, Terminal):
            raise TypeError("fig must be an Terminal object")

    def __iter__(self) -> Iterator[Terminal]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Terminal:
        return super().__getitem__(key)

    def get(self, *args: Any, **kwargs: Any) -> Optional[Terminal]:
        return super().get(*args, **kwargs)

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
            "order": list(self.order),
            "direction": {name: x.direction for name, x in self.items()},
        }
