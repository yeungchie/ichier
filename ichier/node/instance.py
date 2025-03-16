from __future__ import annotations
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple, Union, overload
from textwrap import wrap
from copy import deepcopy

from icutk.log import getLogger

from . import obj
from .fig import Fig, FigCollection, Collection, OrderList
from .trace import (
    traceByInstTermName,
    traceByInstTermOrder,
    ConnectByName,
    ConnectByOrder,
    ConnectType,
)
from ..utils import flattenSequence, expandTermNetPairs

__all__ = [
    "Instance",
    "InstanceCollection",
    "ConnectionPair",
    "ConnectionList",
    "InstanceHierPath",
]


class Instance(Fig):
    def __init__(
        self,
        reference: Optional[str],
        name: Optional[str] = None,
        connection: Optional[Union[Dict[str, Any], Sequence[Any]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        orderparams: Optional[Sequence[str]] = None,
        prefix: Optional[str] = "X",
        raw: Optional[str] = None,
        error: Any = None,
    ) -> None:
        super().__init__(name)
        self.reference = reference

        if connection is None:
            connection = {}
        self.connection = connection
        self.__parameters = obj.ParameterCollection(parameters)
        self.__orderparams = obj.OrderParameters(orderparams)
        self.__prefix = prefix
        self.__raw = raw
        self.error = error
        self.collection: obj.InstanceCollection

    @property
    def reference(self) -> Union[obj.Reference, obj.DesignateReference, obj.Unknown]:
        return self.__reference

    @reference.setter
    def reference(self, value: Optional[str]) -> None:
        if value is None:
            self.__reference = obj.Unknown(instance=self)
        elif isinstance(value, obj.DesignateReference):
            self.__reference = obj.DesignateReference(value, instance=self)
        else:
            self.__reference = obj.Reference(value, instance=self)

    @property
    def connection(self) -> Union[ConnectionPair, ConnectionList]:
        return self.__connection

    @connection.setter
    def connection(
        self,
        value: Optional[Union[Dict[str, Any], Sequence[Any]]],
    ) -> None:
        if value is None:
            self.__connection = ConnectionPair()
            return
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
            self.__connection = ConnectionPair(connect)
        elif isinstance(value, Sequence):
            connect = flattenSequence(tuple(value))
            if not all(x is None or isinstance(x, str) for x in connect):
                raise TypeError("connect by order, must be a sequence of strings")
            self.__connection = ConnectionList(connect)
        else:
            raise TypeError("connection must be a dict or a sequence")

    def getAssocNets(self) -> Tuple[obj.Net, ...]:
        """Get the nets associated with the instance in the module."""
        module = self.getModule()
        if module is None:
            raise ValueError("Instance not in module")
        nets = set()
        if isinstance(self.connection, ConnectionPair):
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

    @property
    def orderparams(self) -> obj.OrderParameters:
        return self.__orderparams

    @property
    def prefix(self) -> Optional[str]:
        if self.__prefix is not None:
            return self.__prefix
        if m := self.reference.getMaster():
            return m.prefix

    @prefix.setter
    def prefix(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("prefix must be a string")
        self.__prefix = value

    @property
    def raw(self) -> Optional[str]:
        return self.__raw

    @raw.setter
    def raw(self, value: Optional[str]) -> None:
        self.__raw = value

    def __call__(self, key: Union[str, int]) -> Any:
        try:
            if isinstance(key, str):
                return self.parameters[key]
            elif isinstance(key, int):
                return self.orderparams[key]
            else:
                raise TypeError(f"key must be a str or an int - {key!r}")
        except KeyError:
            if m := self.reference.getMaster():
                return m.parameters[key]
        except IndexError as e:
            raise e

    @overload
    def trace(self, according: str, depth: int = -1) -> ConnectByName: ...
    @overload
    def trace(self, according: int, depth: int = -1) -> ConnectByOrder: ...
    def trace(self, according: Union[str, int], depth: int = -1) -> ConnectType:
        if isinstance(self.connection, ConnectionPair):
            if not isinstance(according, str):
                raise ValueError(
                    f"this instance connection is a dict, the according should be a string - {according!r}"
                )
            return traceByInstTermName(self, according, depth=depth)
        elif isinstance(self.connection, ConnectionList):
            if not isinstance(according, int):
                raise ValueError(
                    f"this instance connection is a tuple, the according should be an integer - {according!r}"
                )
            return traceByInstTermOrder(self, according, depth=depth)
        else:
            raise TypeError(
                f"this instance connection type is not supported - {type(self.connection)!r}"
            )

    def copy(self, name: Optional[str] = None) -> Instance:
        if isinstance(self.reference, obj.Unknown):
            ref = None
        else:
            ref = self.reference
        if name is None:
            name = self.name
        return Instance(
            reference=ref,
            name=name,
            connection=deepcopy(self.connection),
            parameters=deepcopy(self.parameters),
            orderparams=deepcopy(self.orderparams),
            raw=self.raw,
            error=deepcopy(self.error),
        )

    def __copy__(self) -> Instance:
        return self.copy()

    def __deepcopy__(self, *args, **kwargs) -> Instance:
        return self.copy()

    def rebuild(
        self,
        *,
        master: Optional[obj.Module] = None,
        mute: bool = False,
        verilog_style: bool = False,
    ) -> None:
        """Rebuild connection"""
        logger = getLogger(__name__, mute=mute)
        if isinstance(self.reference, obj.Unknown):
            logger.warning(f"Unknown instance '{self.name}' reference, ignore rebuild.")
            return  # 跳过 Unknown reference，可能是解析失败的实例

        module = self.getModule()
        mod_name = "(NONE)" if module is None else module.name

        if master is None:
            master = self.reference.getMaster()

        ref_name = self.reference.name
        if master is None:
            ref_name += "(MISS)"

        logger.info(
            f"Rebuilding module {mod_name!r} instance '{ref_name}:{self.name}' ..."
        )

        if isinstance(self.connection, ConnectionPair):
            connect = {}
            for term, net_desc in self.connection.items():
                if isinstance(net_desc, str):  # 一对一连接
                    if master:
                        # 有 master 参考
                        if master.terminals.get(term) is not None:
                            connect[term] = net_desc
                        else:
                            # 找不到对应 terminal
                            if (
                                verilog_style
                                and term.isidentifier()
                                and net_desc.isidentifier()
                            ):
                                # 参考 Verilog 语法风格，且连接描述的可能是总线连接
                                if terms := master.terminals.find(rf"{term}\[\d+\]"):
                                    if nets := master.nets.find(rf"{net_desc}\[\d+\]"):
                                        # 模块内已有 net 参考
                                        connect.update(expandTermNetPairs(terms, nets))
                                    else:
                                        # 模块内无 net 参考，尝试自动生成 net 名称
                                        connect.update(
                                            expandTermNetPairs(terms, net_desc)
                                        )
                                else:
                                    raise ValueError(
                                        f"term '{term!s}[\\d+]' not found in module {master.name!r}"
                                    )
                            else:
                                # 不是参考 Verilog 语法风格，或者连接描述无法拓展为总线连接
                                raise ValueError(
                                    f"term {term!r} not found in module {master.name!r}"
                                )
                    else:
                        # 没有 master 参考
                        if (
                            verilog_style
                            and term.isidentifier()
                            and net_desc.isidentifier()
                        ):
                            if module is None:
                                # 不属于任意 module
                                connect[term] = net_desc
                            elif nets := module.nets.find(rf"{net_desc}\[\d+\]"):
                                # 在 module 中这个 net 属于一组总线
                                connect.update(expandTermNetPairs(term, nets))
                            else:
                                # net 不是总线描述
                                connect[term] = net_desc
                        else:
                            connect[term] = net_desc
                elif isinstance(net_desc, (list, tuple)):  # 一对多连接
                    if not verilog_style:
                        raise ValueError(
                            "single-multiple connection only supported in Verilog style"
                        )
                    if master:
                        result = master.terminals.find(rf"{term}\[\d+\]")
                        if not result:
                            raise ValueError(
                                f"term bus type {term!r} not found in module {master.name!r}"
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
        elif isinstance(self.connection, ConnectionList):
            if master:
                if len(self.connection) != len(master.terminals):
                    raise ValueError(
                        "different number of terms and nets, cannot connect by order."
                    )
                connect = {}
                for term, net_desc in zip(master.terminals, self.connection):
                    connect[term.name] = net_desc
                self.connection = connect
            else:
                # 没有可以参考的 master
                if module is None or not verilog_style:
                    # 不属于任何模块，或者不是 Verilog 风格的连接描述，顺序连接无法重建
                    logger.warning(
                        f"Module {mod_name!r} instance '{ref_name}:{self.name}' has no reference master, ignore rebuild by order."
                    )
                else:
                    connect = []
                    for net_desc in self.connection:
                        if nets := module.nets.find(rf"{net_desc}\[\d+\]"):
                            # 匹配到总线描述，拓展该链接
                            connect.extend(map(str, nets))
                        else:
                            connect.append(net_desc)
                    self.connection = connect
        else:
            raise TypeError(
                f"connection must be dict or tuple - {type(self.connection)}"
            )

    def dumpToSpice(self, *, width_limit: int = 88) -> str:
        if isinstance(self.reference, obj.Unknown):
            if self.raw is None:
                raise ValueError("raw must be set when reference is unknown")
            else:
                return self.raw
        if self.prefix is not None:
            prefix = self.prefix
        elif m := self.getModule():
            prefix = m.prefix
        else:
            prefix = "X"
        tokens = [prefix + self.name]
        if isinstance(self.reference, obj.DesignateReference):
            if isinstance(self.connection, ConnectionPair):
                tokens += self.connection.values()
            else:  # ConnectionList
                tokens += self.connection
            tokens.append(f"$[{self.reference.name}]")
            if self.orderparams:
                tokens.append(self.orderparams.dumpToSpice())
            if self.parameters:
                tokens.append(self.parameters.dumpToSpice())
        else:  # Reference
            if isinstance(self.connection, ConnectionPair):
                if self.parameters or self.orderparams:
                    tokens += self.connection.values()
                    tokens.append(self.reference.name)
                    if self.orderparams:
                        tokens.append(self.orderparams.dumpToSpice())
                    if self.parameters:
                        tokens.append(self.parameters.dumpToSpice())
                else:
                    tokens += ["/", self.reference.name, "$PINS"]
                    for term, net in self.connection.items():
                        if not isinstance(net, str):
                            raise TypeError("net must be a string")
                        tokens.append(f"{term!s}={net!s}")
            else:  # ConnectionList
                tokens += self.connection
                tokens += ["/", self.reference.name]
                if self.orderparams:
                    tokens.append(self.orderparams.dumpToSpice())
                if self.parameters:
                    tokens.append(self.parameters.dumpToSpice())
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
        unknown = 0
        cate = {}
        for fig in self:
            if isinstance(fig.reference, obj.Unknown):
                unknown += 1
            else:
                cate.setdefault(fig.reference, 0)
                cate[fig.reference] += 1
        return {
            "total": len(self),
            "categories": cate,
            "unknown": unknown,
        }

    def rebuild(
        self,
        *,
        mute: bool = False,
        verilog_style: bool = False,
    ) -> None:
        for fig in self:
            fig.rebuild(mute=mute, verilog_style=verilog_style)


class ConnectionPair(Collection):
    pass


class ConnectionList(OrderList):
    pass


class InstanceHierPath(list):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self:
            raise ValueError("member must not be empty")
        for i in self:
            if not isinstance(i, Instance):
                raise TypeError(f"hierarchy member should be an Instance - {i!r}")

    @property
    def parent(self) -> Optional[InstanceHierPath]:
        insts = self[:-1]
        if not insts:
            return None
        return InstanceHierPath(insts)
