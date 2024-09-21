from typing import Any, Dict
from typing_extensions import Literal, Optional

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
        direction: Literal["in", "out", "inout"] = "inout",
        net_name: Optional[str] = None,
    ) -> None:
        self.name = name
        self.direction = direction
        self.net_name = net_name

    def __repr__(self) -> str:
        return f"Terminal(name={self.name}, {self.direction})"

    @property
    def direction(self) -> Literal["in", "out", "inout"]:
        return self.__direction

    @direction.setter
    def direction(self, value) -> None:
        if value not in ["in", "out", "inout"]:
            raise ValueError("direction must be 'in', 'out', or 'inout'")
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

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
            "order": list(self.order),
            "direction": {name: x.direction for name, x in self.items()},
            "connection": {name: x.net_name for name, x in self.items()},
        }
