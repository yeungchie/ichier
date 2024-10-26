from typing import Any, Iterable, Dict, Iterator, Optional, Tuple, Union
import re


import ichier
from .fig import Fig, FigCollection
from .utils import logger, flattenMemName, expandTermNetPairs

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

    def rebuild(self, reference: Optional["ichier.Module"] = None) -> None:
        """Rebuild connection"""
        if reference is None and self.collection is not None:
            if isinstance(module := self.collection.parent, ichier.Module):
                if isinstance(modules := module.collection, ichier.ModuleCollection):
                    reference = modules.get(self.reference)
        else:
            module = None

        if isinstance(reference, ichier.Module):
            ref_terms = [t.name for t in reference.terminals]
        else:
            reference = None

        mod_name = module.name if module is not None else "none"
        ref_name = reference.name if reference is not None else "none"
        logger.info(
            f"Rebuilding module {mod_name!r} instance '{ref_name}:{self.name}' ..."
        )

        if isinstance(self.connection, dict):
            connection = {}
            for termname, netname in self.connection.items():
                term_order = flattenMemName(termname)
                net_order = flattenMemName(netname)
                term_count = len(term_order)
                net_count = len(net_order)
                if (term_count == 1) and (net_count != 1):
                    # terminal 只有一个, 但 net 不唯一
                    term = term_order[0]
                    if re.fullmatch(r"[\[\]<>]", term):
                        # term 字面上是总线的某 bit 例如 A<1>
                        # net 不唯一, 不能连接到这个端口上
                        raise ValueError(f"cannot connect {termname!r} to {netname!r}")
                    else:
                        # 可能是总线形式, verilog 中例化会被简写
                        # CELL I0 (.IN(A[1:0]));
                        if reference:
                            # 存在可以参考的 Module
                            # 匹配 term<\d+> / term[\d:]+
                            connection = expandTermNetPairs(
                                [
                                    t.name
                                    for t in reference.terminals
                                    if re.fullmatch(rf"{term}(<\d+>|\[\d+\])", t.name)
                                ],
                                net_order,
                            )
                        else:
                            # 没有可以参考的 Module, 自动生成一组总线
                            connection = expandTermNetPairs(termname, net_order)
                elif term_count != net_count:
                    # terminal 和 net 都是多个, 但数量不同, 无法连接
                    raise ValueError(
                        f"different number of terms and nets, cannot connect {termname!r} to {netname!r}"
                    )
                else:
                    # terminal 和 net 数量相同
                    for term, net in zip(term_order, net_order):
                        if reference and term not in ref_terms:
                            raise ValueError(
                                f"term {term!r} not found in module {reference.name!r}"
                            )
                        connection[term] = net
        elif isinstance(self.connection, Iterable):
            net_order = []
            for netname in self.connection:
                net_order += flattenMemName(netname)
            if reference is None:
                connection = net_order  # 没有可以参考的 Module, 只能按顺序连接
            else:
                connection = {}  # 存在可以参考的 Module, 按命名连接
                for term, net in zip(ref_terms, net_order):
                    connection[term] = net
        else:
            raise TypeError("connection must be a iterable or a dict")
        self.connection = connection


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
