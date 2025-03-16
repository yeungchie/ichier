from __future__ import annotations
from typing import List, Optional, Union

from . import obj

__all__ = [
    "ConnectByName",
    "ConnectByOrder",
    "ConnectType",
    "Route",
    "traceByNet",
    "traceByInstTermName",
    "traceByInstTermOrder",
]


class Connect:
    instance: obj.Instance
    route: Optional[Route]

    def __repr__(self) -> str:
        return self.repr()

    def repr(self, indent: int = 0) -> str:
        inst = self.instance
        inst_repr = f"Instance({inst.reference!r}, {inst.name!r})"
        if isinstance(self, ConnectByName):
            state = f"ConnectByName({inst_repr!s}, {self.name!r})"
        elif isinstance(self, ConnectByOrder):
            state = f"ConnectByOrder({inst_repr!s}, {self.order!r})"
        else:
            raise TypeError(f"Invalid Connect type - {type(self)!r}")
        if self.route is not None:
            state += f" -> {self.route.repr(indent + 1)}"
        return state

    def trace(self, depth: int = -1, peek: bool = False) -> Optional[Route]:
        self.route = None
        if depth == 0:
            return
        master = self.instance.reference.getMaster()
        if master is None:
            return
        if isinstance(self, ConnectByName):
            net = master.nets[self.name]
        elif isinstance(self, ConnectByOrder):
            net = master.nets[master.terminals[self.order].name]
        route = traceByNet(net, depth - 1)
        if peek:
            return route
        if route.connect_collection:
            self.route = route

    def peek(self, depth: int = -1) -> Optional[Route]:
        return self.trace(depth, peek=True)


class ConnectByName(Connect):
    def __init__(self, instance: obj.Instance, name: str) -> None:
        self.instance = instance
        self.name = name
        self.route = None


class ConnectByOrder(Connect):
    def __init__(self, instance: obj.Instance, order: int) -> None:
        self.instance = instance
        self.order = order
        self.route = None


ConnectType = Union[ConnectByName, ConnectByOrder]


class Route:
    def __init__(self, net: obj.Net, connect_collection: List[ConnectType]) -> None:
        self.net = net
        self.connect_collection = connect_collection

    def __repr__(self) -> str:
        return self.repr()

    def repr(self, indent: int = 1) -> str:
        state = f"Route({self.net!r}, ["
        if self.connect_collection:
            state += "\n"
            for connect in self.connect_collection:
                state += f"{' ' * indent}{connect.repr(indent)},\n"
        state += f"{' ' * (indent - 1)}])"
        return state


def traceByNet(net: obj.Net, depth: int = -1) -> Route:
    module = net.getModule()
    if module is None:
        return Route(net, [])
    segs = []
    for inst in module.instances:
        if isinstance(inst.connection, dict):
            for t, n in inst.connection.items():
                if n == net.name:
                    segs.append(traceByInstTermName(inst, t, depth))
        elif isinstance(inst.connection, list):
            for i, n in enumerate(inst.connection):
                if n == net.name:
                    segs.append(traceByInstTermOrder(inst, i, depth))
        else:
            raise TypeError(f"Invalid connection type {type(inst.connection)}")
    return Route(net, segs)


def traceByInstTermName(
    instance: obj.Instance,
    term_name: str,
    depth: int = -1,
) -> ConnectByName:
    if not isinstance(instance.connection, dict):
        raise ValueError(f"{instance!r} is not connect by name")
    if term_name not in instance.connection:
        raise ValueError(f"term {term_name!r} not found in {instance!r}.connection")
    connect = ConnectByName(instance, term_name)
    connect.trace(depth)
    return connect


def traceByInstTermOrder(
    instance: obj.Instance,
    term_order: int,
    depth: int = -1,
) -> ConnectByOrder:
    if not isinstance(instance.connection, list):
        raise ValueError(f"{instance!r} is not connect by order")
    try:
        instance.connection[term_order]
    except IndexError:
        raise ValueError(
            f"order {term_order!r} out of range in {instance!r}.connection"
        )
    connect = ConnectByOrder(instance, term_order)
    connect.trace(depth)
    return connect
