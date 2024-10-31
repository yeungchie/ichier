from typing import Any, Dict, Iterator, Union

from icutk.log import logger

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

    def __iter__(self) -> Iterator[Net]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Net:
        return super().__getitem__(key)

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
        }

    def rebuild(self) -> None:
        """Recreating all nets in the module."""
        module = self.parent
        if not isinstance(module, ichier.Module):
            raise ValueError("parent module must be specified")
        logger.info(f"Rebuilding module {module.name!r} nets ...")

        all_nets = set()

        # terminals
        for term in module.terminals:
            all_nets.add(term.name)

        # instances
        for inst in module.instances:
            connection = inst.connection
            if isinstance(connection, dict):
                for net in connection.values():
                    all_nets.add(net)
            elif isinstance(connection, tuple):
                for net in connection:
                    all_nets.add(net)

        # create new
        self.clear()
        self.extend(Net(name) for name in all_nets)
