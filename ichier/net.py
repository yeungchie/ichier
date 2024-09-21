from typing import Any, Dict

import ichier
from .fig import Fig, FigCollection

__all__ = [
    "Net",
    "NetCollection",
]


class Net(Fig):
    def __init__(self, name: str) -> None:
        self.name = name

    def getConnectedInstances(self) -> tuple:
        if self.collection is None:
            return ()
        if not isinstance(self.collection.parent, ichier.Module):
            return ()
        insts = []
        for inst in self.collection.parent.instances:
            inst: ichier.Instance
            if isinstance(inst.connection, tuple):
                nets = inst.connection
            elif isinstance(inst.connection, dict):
                nets = inst.connection.values()
            if self.name in nets:
                insts.append(inst)
        return tuple(insts)


class NetCollection(FigCollection):
    def _valueChecker(self, fig: Net) -> None:
        if not isinstance(fig, Net):
            raise TypeError("fig must be an Net object")

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
        }
