from typing import Any, Dict

from .fig import Collection

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


class SpecifyParameters(ParameterCollection):
    pass


class OrderParameters(list):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        if args == (None,) and not kwargs:
            return
        self.extend(*args, **kwargs)

    def __repr__(self) -> str:
        return f"Params: {list(self)!r}"

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
            "items": list(self),
        }
