from typing import Any, Dict, Iterator, Optional, Sequence, Tuple, Union

from icutk.log import logger

import ichier
from .fig import Fig, FigCollection
from .utils import flattenSequence, expandTermNetPairs

__all__ = [
    "Instance",
    "InstanceCollection",
]


class Instance(Fig):
    def __init__(
        self,
        name: str,
        reference: str,
        connection: Union[
            None,
            Dict[str, Union[str, Sequence[str]]],
            Sequence[Union[str, Sequence[str]]],
        ] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.reference = reference

        if connection is None:
            connection = {}
        self.connection = connection

        if parameters is None:
            parameters = {}
        self.__parameters = ichier.ParameterCollection(parameters)

        self.collection: "ichier.InstanceCollection"

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
    ) -> Union[Dict[str, Union[str, Tuple[str, ...]]], Tuple[str, ...]]:
        return self.__connection

    @connection.setter
    def connection(
        self,
        value: Union[
            Dict[str, Union[str, Sequence[str]]],
            Sequence[Union[str, Sequence[str]]],
        ],
    ) -> None:
        if isinstance(value, dict):
            connect = {}
            for term, net_info in value.items():
                if not isinstance(term, str):
                    raise TypeError("connect by name, term must be a string")
                if isinstance(net_info, str):
                    connect[term] = net_info
                elif isinstance(net_info, Sequence):
                    connect[term] = flattenSequence(tuple(net_info))
                else:
                    raise TypeError(
                        "connect by name, net description must be a string or a sequence"
                    )
        elif isinstance(value, Sequence):
            connect = flattenSequence(tuple(value))
            if not all(isinstance(x, str) for x in connect):
                raise TypeError("connect by order, must be a sequence of strings")
        else:
            raise TypeError("connection must be a dict or a sequence")
        self.__connection = connect

    @property
    def parameters(self) -> "ichier.ParameterCollection":
        return self.__parameters

    def __getitem__(self, key: str) -> Any:
        return self.parameters[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.parameters[key] = value

    def __delitem__(self, key: str) -> None:
        del self.parameters[key]

    def rebuild(self, reference: Optional["ichier.Module"] = None) -> None:
        """Rebuild connection"""
        if reference is None and self.collection is not None:
            if isinstance(module := self.collection.parent, ichier.Module):
                if isinstance(modules := module.collection, ichier.ModuleCollection):
                    reference = modules.get(self.reference)
        else:
            module = None

        if not isinstance(reference, ichier.Module):
            reference = None

        mod_name = module.name if module is not None else "none"
        ref_name = reference.name if reference is not None else "none"
        logger.info(
            f"Rebuilding module {mod_name!r} instance '{ref_name}:{self.name}' ..."
        )

        if isinstance(self.connection, dict):
            connect = {}
            for term, net_desc in self.connection.items():
                if isinstance(net_desc, str):  # 一对一连接
                    if (
                        reference and reference.terminals.get(term) is None
                    ):  # 检查 terminal 是否存在
                        raise ValueError(
                            f"term {term!r} not found in module {reference.name!r}"
                        )
                    connect[term] = net_desc
                elif isinstance(net_desc, tuple):  # 一对多连接
                    if reference:
                        result = reference.terminals.find(rf"{term}(\[\d+\]|<\d+>)")
                        if not result:
                            raise ValueError(
                                f"term bus type {term!r} not found in module {reference.name!r}"
                            )
                        if len(result) != len(net_desc):
                            raise ValueError(
                                f"different number of terms and nets, cannot connect {term!r} to {net_desc!r}"
                            )
                        for t, n in zip(result, net_desc):
                            connect[t.name] = n
                    else:
                        connect.update(expandTermNetPairs(term, net_desc))
            self.connection = connect
        elif isinstance(self.connection, (list, tuple)):
            if reference:
                if len(self.connection) != len(reference.terminals):
                    raise ValueError(
                        "different number of terms and nets, cannot connect by order."
                    )
                connect = {}
                for term, net_desc in zip(reference.terminals, self.connection):
                    connect[term.name] = net_desc
                self.connection = connect
            else:
                # 没有可以参考的Module，顺序连接忽略重建
                logger.warning(
                    f"Module {mod_name!r} instance '{ref_name}:{self.name}' has no reference module, ignore rebuild by order."
                )
        else:
            raise TypeError("connection must be dict, list or tuple.")


class InstanceCollection(FigCollection):
    def _valueChecker(self, fig: Instance) -> None:
        if not isinstance(fig, Instance):
            raise TypeError("fig must be an Instance object")

    def __iter__(self) -> Iterator[Instance]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Instance:
        return super().__getitem__(key)

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

    def rebuild(self) -> None:
        for fig in self:
            fig.rebuild()
