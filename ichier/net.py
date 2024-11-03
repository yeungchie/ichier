from typing import Any, Dict, Iterator, Optional, Tuple, Union

from icutk.log import getLogger

import ichier.obj as icobj
from .fig import Fig, FigCollection

__all__ = [
    "Net",
    "NetCollection",
]


class Net(Fig):
    def getAssocInstances(self) -> Tuple["icobj.Instance", ...]:
        """Get the instances associated with the net in the module."""
        module = self.getModule()
        if module is None:
            raise ValueError("Instance not in module")
        insts = set()
        for inst in module.instances:
            inst: icobj.Instance
            if isinstance(inst.connection, tuple):
                nets = inst.connection
            elif isinstance(inst.connection, dict):
                nets = inst.connection.values()
            if self.name in nets:
                insts.add(inst)
        return tuple(insts)


class NetCollection(FigCollection):
    def _valueChecker(self, fig: Net) -> None:
        if not isinstance(fig, Net):
            raise TypeError("fig must be an Net object")

    def __iter__(self) -> Iterator[Net]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Net:
        return super().__getitem__(key)

    def get(self, *args: Any, **kwargs: Any) -> Optional[Net]:
        return super().get(*args, **kwargs)

    def summary(self) -> Dict[str, Any]:
        return {
            "total": len(self),
        }

    def rebuild(self) -> None:
        """Recreating all nets in the module."""
        module = self.parent
        if not isinstance(module, icobj.Module):
            raise ValueError("parent module must be specified")

        logger = getLogger(__name__)
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
