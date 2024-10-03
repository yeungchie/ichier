from typing import Any, Iterable, Dict, Tuple, Union

import ichier
from .fig import Fig, FigCollection

__all__ = [
    "Instance",
    "InstanceCollection",
]


class Instance(Fig):
    def __init__(
        self,
        name: str,
        reference: str,
        connection: Union[Iterable[str], Dict[str, str]] = (),
        parameters: dict = {},
    ) -> None:
        self.name = name
        self.reference = reference
        self.connection = connection
        self.__parameters = ichier.ParameterCollection(parameters)

    @property
    def reference(self) -> str:
        return self.__module_name

    @reference.setter
    def reference(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("module_name must be a string")
        self.__module_name = value

    @property
    def connection(
        self,
    ) -> Union[Tuple[str, ...], Dict[str, str]]:
        return self.__connection

    @connection.setter
    def connection(
        self,
        value: Union[Iterable[str], Dict[str, str]],
    ) -> None:
        if isinstance(value, dict):
            for net, term in value.items():
                if not isinstance(net, str) or not isinstance(term, str):
                    raise TypeError(
                        f"connection must be a dict of str:str pairs - {repr(net)}:{repr(term)}"
                    )
            self.__connection = value
        elif isinstance(value, Iterable):
            value = tuple(value)
            for net in value:
                if not isinstance(net, str):
                    raise TypeError(
                        f"connection must be a iterable of strings - {repr(net)}"
                    )
            self.__connection = value
        else:
            raise TypeError("connection must be a iterable or a dict")

    @property
    def parameters(self) -> "ichier.ParameterCollection":
        return self.__parameters

    def __getitem__(self, key: str) -> Any:
        return self.parameters[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.parameters[key] = value

    def __delitem__(self, key: str) -> None:
        del self.parameters[key]


class InstanceCollection(FigCollection):
    def _valueChecker(self, fig: Instance) -> None:
        if not isinstance(fig, Instance):
            raise TypeError("fig must be an Instance object")

    def summary(self) -> Dict[str, Any]:
        cate = {}
        for fig in self.figs:
            fig: Instance
            cate.setdefault(fig.reference, 0)
            cate[fig.reference] += 1
        return {
            "total": len(self),
            "categories": cate,
        }
