from __future__ import annotations
from typing import List, Union

from . import obj

__all__ = [
    "ConnectByName",
    "ConnectByOrder",
    "Connect",
    "Route",
    "traceByNet",
    "traceByInstTermName",
    "traceByInstTermOrder",
]


class ConnectByName:
    def __init__(self, instance: obj.Instance, name: str) -> None:
        self.instance = instance
        self.name = name
        self.route = None

    def __repr__(self) -> str:
        return self.pprint()

    def pprint(self, indent: int = 0) -> str:
        state = f"ConnectByName(Instance({self.instance.reference!r}, {self.instance.name!r}), {self.name!r})"
        if self.route is not None:
            state += f" -> {self.route.pprint(indent + 1)}"
        return state

    def trace(self, depth: int = -1) -> None:
        self.route = None
        if depth == 0:
            return
        master = self.instance.reference.getMaster()
        if master is None:
            return
        route = traceByNet(master.nets[self.name], depth - 1)
        if route.connect_collection:
            self.route = route


class ConnectByOrder:
    def __init__(self, instance: obj.Instance, order: int) -> None:
        self.instance = instance
        self.order = order
        self.route = None

    def __repr__(self) -> str:
        return self.pprint()

    def pprint(self, indent: int = 0) -> str:
        state = f"ConnectByOrder(Instance({self.instance.reference!r}, {self.instance.name!r}), {self.order})"
        if self.route is not None:
            state += f" -> {self.route.pprint(indent + 1)}"
        return state

    def trace(self, depth: int = -1) -> None:
        self.route = None
        if depth == 0:
            return
        master = self.instance.reference.getMaster()
        if master is None:
            return
        route = traceByNet(master.nets[master.terminals[self.order].name], depth - 1)
        if route.connect_collection:
            self.route = route


Connect = Union[ConnectByName, ConnectByOrder]


class Route:
    def __init__(self, net: obj.Net, connect_collection: List[Connect]) -> None:
        self.net = net
        self.connect_collection = connect_collection

    def __repr__(self) -> str:
        return self.pprint()

    def pprint(self, indent: int = 1) -> str:
        state = f"Route({self.net!r}, ["
        if self.connect_collection:
            state += "\n"
            for connect in self.connect_collection:
                state += f"{' ' * indent}{connect.pprint(indent)},\n"
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
        elif isinstance(inst.connection, tuple):
            for i, n in enumerate(inst.connection):
                if n == net.name:
                    segs.append(traceByInstTermOrder(inst, i, depth))
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
    if not isinstance(instance.connection, tuple):
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
