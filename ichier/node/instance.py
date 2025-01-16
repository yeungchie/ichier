from __future__ import annotations
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple, Union
from textwrap import wrap

from icutk.log import getLogger

from . import obj
from .fig import Fig, FigCollection
from ..utils import flattenSequence, expandTermNetPairs

__all__ = [
    "Instance",
    "InstanceCollection",
]


class Instance(Fig):
    def __init__(
        self,
        reference: str,
        name: Optional[str] = None,
        connection: Union[
            None,
            Dict[str, Union[None, str, Sequence[str]]],
            Sequence[Union[None, str, Sequence[str]]],
        ] = None,
        parameters: Optional[Dict[str, Any]] = None,
        orderparams: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(name)
        self.reference = reference

        if connection is None:
            connection = {}
        self.connection = connection
        self.__parameters = obj.ParameterCollection(parameters)
        self.__orderparams = obj.OrderParameters(orderparams)
        self.collection: obj.InstanceCollection

    @property
    def reference(self) -> obj.Reference:
        return self.__reference

    @reference.setter
    def reference(self, value: str) -> None:
        if isinstance(value, obj.DesignateReference):
            ref_cls = obj.DesignateReference
        else:
            ref_cls = obj.Reference
        self.__reference = ref_cls(value, instance=self)

    @property
    def connection(
        self,
    ) -> Union[Dict[str, Union[str, Tuple[str, ...]]], Tuple[str, ...]]:
        return self.__connection

    @connection.setter
    def connection(
        self,
        value: Union[
            Dict[str, Union[None, str, Sequence[str]]],
            Sequence[Union[None, str, Sequence[str]]],
        ],
    ) -> None:
        if isinstance(value, dict):
            connect = {}
            for term, net_info in value.items():
                if not isinstance(term, str):
                    raise TypeError("connect by name, term must be a string")
                if net_info is None:
                    continue  # 忽略悬空连接
                elif isinstance(net_info, str):
                    connect[term] = net_info
                elif isinstance(net_info, Sequence):
                    connect[term] = flattenSequence(tuple(net_info))
                else:
                    raise TypeError(
                        "connect by name, net description must be a string or a sequence"
                    )
        elif isinstance(value, Sequence):
            connect = flattenSequence(tuple(value))
            if not all(x is None or isinstance(x, str) for x in connect):
                raise TypeError("connect by order, must be a sequence of strings")
        else:
            raise TypeError("connection must be a dict or a sequence")
        self.__connection = connect

    def getAssocNets(self) -> Tuple[obj.Net, ...]:
        """Get the nets associated with the instance in the module."""
        module = self.getModule()
        if module is None:
            raise ValueError("Instance not in module")
        nets = set()
        if isinstance(self.connection, dict):
            connects = self.connection.values()
        else:
            connects = self.connection
        for net_desc in connects:
            if isinstance(net_desc, str):
                if net := module.nets.get(net_desc):
                    nets.add(net)
            else:
                raise ValueError(
                    f"{net_desc!r} is not a scalar string, maybe you need to rebuild the connection."
                )
        return tuple(nets)

    @property
    def parameters(self) -> obj.ParameterCollection:
        return self.__parameters

    def __getitem__(self, key: str) -> Any:
        return self.parameters[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.parameters[key] = value

    def __delitem__(self, key: str) -> None:
        del self.parameters[key]

    def rebuild(
        self,
        *,
        reference: Optional[obj.Module] = None,
        mute: bool = False,
        verilog_style: bool = False,
    ) -> None:
        """Rebuild connection"""
        logger = getLogger(__name__, mute=mute)
        if reference is None and self.collection is not None:
            if isinstance(module := self.collection.parent, obj.Module):
                if isinstance(modules := module.collection, obj.ModuleCollection):
                    reference = modules.get(self.reference)
        else:
            module = None

        if not isinstance(reference, obj.Module):
            reference = None

        mod_name = "(NONE)" if module is None else module.name
        ref_name = self.reference.name
        if reference is None:
            ref_name += "(MISS)"
        logger.info(
            f"Rebuilding module {mod_name!r} instance '{ref_name}:{self.name}' ..."
        )

        if isinstance(self.connection, dict):
            connect = {}
            for term, net_desc in self.connection.items():
                if isinstance(net_desc, str):  # 一对一连接
                    if reference:
                        if reference.terminals.get(term) is not None:
                            connect[term] = net_desc
                        else:
                            # 找不到对应 terminal
                            if (
                                verilog_style
                                and term.isidentifier()
                                and net_desc.isidentifier()
                            ):
                                # 参考 Verilog 语法风格，且连接描述的可能是总线连接
                                if terms := reference.terminals.find(rf"{term}\[\d+\]"):
                                    if nets := reference.nets.find(
                                        rf"{net_desc}\[\d+\]"
                                    ):
                                        # 模块内已有 net 参考
                                        connect.update(expandTermNetPairs(terms, nets))
                                    else:
                                        # 模块内无 net 参考，尝试自动生成 net 名称
                                        connect.update(
                                            expandTermNetPairs(terms, net_desc)
                                        )
                                else:
                                    raise ValueError(
                                        f"term '{term!s}[\\d+]' not found in module {reference.name!r}"
                                    )
                            else:
                                # 不是参考 Verilog 语法风格，或者连接描述无法拓展为总线连接
                                raise ValueError(
                                    f"term {term!r} not found in module {reference.name!r}"
                                )
                    else:
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

    def dumpToSpice(self, *, width_limit: int = 88) -> str:
        tokens = [self.name]
        if isinstance(self.reference, obj.DesignateReference):
            if isinstance(self.connection, dict):
                for net in self.connection.values():
                    if not isinstance(net, str):
                        raise TypeError("net must be a string")
                    tokens.append(net)
            else:
                tokens += self.connection
            tokens.append(f"$[{self.reference.name}]")
        else:
            if isinstance(self.connection, dict):
                tokens += ["/", self.reference.name, "$PINS"]
                for term, net in self.connection.items():
                    if not isinstance(net, str):
                        raise TypeError("net must be a string")
                    tokens.append(f"{term!s}={net!s}")
            else:
                for net in self.connection:
                    tokens.append(str(net))
                tokens += ["/", self.reference.name]
        return "\n".join(
            wrap(
                " ".join(tokens),
                width=width_limit,
                subsequent_indent="+ ",
            )
        )


class InstanceCollection(FigCollection):
    def _valueChecker(self, fig: Instance) -> None:
        if not isinstance(fig, Instance):
            raise TypeError("fig must be an Instance object")

    def __iter__(self) -> Iterator[Instance]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Instance:
        return super().__getitem__(key)

    def get(self, *args: Any, **kwargs: Any) -> Optional[Instance]:
        return super().get(*args, **kwargs)

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

    def rebuild(
        self,
        *,
        mute: bool = False,
        verilog_style: bool = False,
    ) -> None:
        for fig in self:
            fig.rebuild(mute=mute, verilog_style=verilog_style)
