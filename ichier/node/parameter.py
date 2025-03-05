from typing import Any, Dict

from .fig import Collection, OrderList

__all__ = [
    "ParameterCollection",
    "SpecifyParameters",
    "OrderParameters",
]


class ParameterCollection(Collection):
    def __repr__(self) -> str:
        strings = ["Params:"]
        for key, value in self.items():
            strings.append(f"  {key} = {repr(value)}")
        return "\n".join(strings)

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
            "property": dict(self),
        }

    def dumpToSpice(self) -> str:
        return " ".join(f"{k!s}={v!s}" for k, v in self.items())


class SpecifyParameters(ParameterCollection):
    pass


class OrderParameters(OrderList):
    def __repr__(self) -> str:
        return self.repr("Params")

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
            "items": list(self),
        }

    def dumpToSpice(self) -> str:
        return " ".join(map(str, self))
