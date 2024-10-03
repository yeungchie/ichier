from typing import Any, Dict, Iterable
from typing_extensions import Literal

import ichier
from ichier.fig import Fig, FigCollection

__all__ = [
    "Module",
    "ModuleCollection",
]


class Module(Fig):
    def __init__(
        self,
        name: str,
        terminals: Iterable["ichier.Terminal"] = (),
        nets: Iterable["ichier.Net"] = (),
        instances: Iterable["ichier.Instance"] = (),
        parameters: dict = {},
    ) -> None:
        self.name = name
        self.__terminals = ichier.TerminalCollection(self, terminals)
        self.__nets = ichier.NetCollection(self, nets)
        self.__instances = ichier.InstanceCollection(self, instances)
        self.__parameters = ichier.ParameterCollection(parameters)

    @property
    def terminals(self) -> "ichier.TerminalCollection":
        return self.__terminals

    @property
    def instances(self) -> "ichier.InstanceCollection":
        return self.__instances

    @property
    def nets(self) -> "ichier.NetCollection":
        return self.__nets

    @property
    def parameters(self) -> "ichier.ParameterCollection":
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


class ModuleCollection(FigCollection):
    def _valueChecker(self, value: Module) -> None:
        if not isinstance(value, Module):
            raise TypeError("value must be a Module")

    def summary(
        self, info_type: Literal["compact", "detail"] = "compact"
    ) -> Dict[str, Any]:
        return {
            "total": len(self),
            "list": [module.summary(info_type) for module in self.figs],
        }
