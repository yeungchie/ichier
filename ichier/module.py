from typing import Any, Dict, Iterable, Iterator, Literal, Union

from icutk.log import logger

import ichier.obj as icobj
from .fig import Fig, FigCollection

__all__ = [
    "Module",
    "ModuleCollection",
]


class Module(Fig):
    def __init__(
        self,
        name: str,
        terminals: Iterable["icobj.Terminal"] = (),
        nets: Iterable["icobj.Net"] = (),
        instances: Iterable["icobj.Instance"] = (),
        parameters: dict = {},
    ) -> None:
        self.name = name
        self.__terminals = icobj.TerminalCollection(self, terminals)
        self.__nets = icobj.NetCollection(self, nets)
        self.__instances = icobj.InstanceCollection(self, instances)
        self.__parameters = icobj.ParameterCollection(parameters)

    @property
    def terminals(self) -> "icobj.TerminalCollection":
        return self.__terminals

    @property
    def instances(self) -> "icobj.InstanceCollection":
        return self.__instances

    @property
    def nets(self) -> "icobj.NetCollection":
        return self.__nets

    @property
    def parameters(self) -> "icobj.ParameterCollection":
        return self.__parameters

    def summary(
        self,
        info_type: Literal["compact", "detail"] = "compact",
    ) -> Dict[str, Any]:
        if info_type == "compact":
            return {
                "name": self.name,
                "instances": len(self.instances),
                "terminals": len(self.terminals),
                "nets": len(self.nets),
                "parameters": len(self.parameters),
            }
        elif info_type == "detail":
            return {
                "name": self.name,
                "instances": self.instances.summary(),
                "terminals": self.terminals.summary(),
                "nets": self.nets.summary(),
                "parameters": self.parameters.summary(),
            }
        else:
            raise ValueError("type must be 'compact' or 'detail'")

    def rebuild(self) -> None:
        """Rebuild the module.

        Rebuild all instances connection, then recreating all nets for this module.
        """
        self.instances.rebuild()
        self.nets.rebuild()

    def makeModule(self, modules: Iterable["icobj.Instance"]) -> "Module": ...


class ModuleCollection(FigCollection):
    def _valueChecker(self, value: Module) -> None:
        if not isinstance(value, Module):
            raise TypeError("value must be a Module")

    def __iter__(self) -> Iterator[Module]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Module:
        return super().__getitem__(key)

    def summary(
        self, info_type: Literal["compact", "detail"] = "compact"
    ) -> Dict[str, Any]:
        return {
            "total": len(self),
            "list": [module.summary(info_type) for module in self.figs],
        }

    def rebuild(self) -> None:
        for fig in self:
            logger.info(f"Rebuilding module {fig.name!r} ...")
            fig.rebuild()
