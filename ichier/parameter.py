from typing import Any, Dict

from .fig import Collection

__all__ = [
    "ParameterCollection",
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
            "property": {name: value for name, value in self.items()},
        }
