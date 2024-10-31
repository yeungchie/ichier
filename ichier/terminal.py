from typing import Any, Dict, Iterator, Optional, Literal, Union

from .fig import Fig, FigCollection
from .errors import TerminalError

__all__ = [
    "Terminal",
    "TerminalCollection",
]


class Terminal(Fig):
    def __init__(
        self,
        name: str,
        *,
        direction: Literal["input", "output", "inout"] = "inout",
        net_name: Optional[str] = None,
    ) -> None:
        self.name = name
        self.direction = direction
        self.net_name = net_name

    def __repr__(self) -> str:
        return f"Terminal({self.name!r}, {self.direction!r})"

    @property
    def direction(self) -> Literal["input", "output", "inout"]:
        return self.__direction

    @direction.setter
    def direction(self, value) -> None:
        if value not in ["input", "output", "inout"]:
            raise ValueError("direction must be 'input', 'output', or 'inout'")
        self.__direction = value

    @property
    def net_name(self) -> Optional[str]:
        return self.__net or self.name

    @net_name.setter
    def net_name(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("net must be a Net object or None")
        self.__net = value

    def check(self) -> None:
        if self.net_name is not None and self.name != self.net_name:
            raise TerminalError(
                f"Terminal name {self.name} does not match net name {self.net_name}"
            )


class TerminalCollection(FigCollection):
    def _valueChecker(self, fig: Terminal) -> None:
        if not isinstance(fig, Terminal):
            raise TypeError("fig must be an Terminal object")

    def __iter__(self) -> Iterator[Terminal]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Terminal:
        return super().__getitem__(key)

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
            "order": list(self.order),
            "direction": {name: x.direction for name, x in self.items()},
            "connection": {name: x.net_name for name, x in self.items()},
        }
