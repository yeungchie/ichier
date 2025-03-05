from __future__ import annotations
from pathlib import Path
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)
from collections import defaultdict
from textwrap import wrap

from icutk.log import getLogger

from . import obj
from .fig import Fig, FigCollection

__all__ = [
    "Module",
    "ModuleCollection",
]


class Module(Fig):
    def __init__(
        self,
        name: Optional[str] = None,
        terminals: Iterable[obj.Terminal] = (),
        nets: Iterable[obj.Net] = (),
        instances: Iterable[obj.Instance] = (),
        parameters: Optional[Dict[str, Any]] = None,
        specparams: Optional[Dict[str, Any]] = None,
        prefix: str = "",
    ) -> None:
        super().__init__(name)
        self.__terminals = obj.TerminalCollection(self, terminals)
        self.__nets = obj.NetCollection(self, nets)
        self.__instances = obj.InstanceCollection(self, instances)
        self.__parameters = obj.ParameterCollection(parameters)
        self.__specparams = obj.SpecifyParameters(specparams)
        self.__prefix = prefix
        self.__lienno = None
        self.__path = None

    @property
    def terminals(self) -> obj.TerminalCollection:
        return self.__terminals

    @property
    def instances(self) -> obj.InstanceCollection:
        return self.__instances

    @property
    def nets(self) -> obj.NetCollection:
        return self.__nets

    @property
    def parameters(self) -> obj.ParameterCollection:
        return self.__parameters

    @property
    def specparams(self) -> obj.SpecifyParameters:
        return self.__specparams

    @property
    def prefix(self) -> str:
        return self.__prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("prefix must be a string")
        self.__prefix = value

    @property
    def lineno(self) -> Optional[int]:
        return self.__lienno

    @lineno.setter
    def lineno(self, value: Optional[int]) -> None:
        self.__lienno = value

    @property
    def path(self) -> Optional[Path]:
        return self.__path

    @path.setter
    def path(self, value: Optional[Union[str, Path]]) -> None:
        if value is not None:
            value = Path(value)
        self.__path = value

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
                "specparams": self.specparams.summary(),
            }
        else:
            raise ValueError("type must be 'compact' or 'detail'")

    def rebuild(
        self,
        *,
        mute: bool = False,
        verilog_style: bool = False,
    ) -> None:
        """Rebuild the module.

        Rebuild all instances connection, then recreating all nets for this module.
        """
        self.instances.rebuild(mute=mute, verilog_style=verilog_style)
        self.nets.rebuild(mute=mute)

    def pack(
        self,
        name: str,
        instances: Iterable[Union[str, obj.Instance]],
        to_design: Optional[obj.Design] = None,
    ) -> Module:
        """Create a new module with the given instances.

        Parameters :
        ---
        name : The name of the new module.
        instances : The instances to be included in the new module. Or the `str` result should be the instance name.
        to_design : The design to which the new module will be added. If None, the module will be added to the current design unless then module not belong to any design.

        Returns :
        ---
        The new module.
        """
        if to_design is not None:
            if not isinstance(to_design, obj.Design):
                raise TypeError("to_design must be a Design")
            design = to_design
        else:
            design = self.getDesign()
        if design is not None and name in design.modules:
            raise ValueError(
                f"Module {name!r} already exists in design {design.name!r}"
            )

        insts: Set[obj.Instance] = set()
        nets: Set[obj.Net] = set()
        net_dirs: DefaultDict[str, set] = defaultdict(set)

        for i in instances:
            inst = self.instances.get(str(i))
            if inst is None:
                raise ValueError(f"Instance '{i!s}' not found in module {self.name!r}")
            insts.add(inst.copy())
            nets.update(inst.getAssocNets())  # 所有与这些实例有关联的 net

            connection = inst.connection
            if isinstance(connection, dict):
                if master := inst.reference.getMaster():
                    # 连接关系为 dict 且能找到 master 可以用来参考逻辑方向
                    for t, n in connection.items():
                        if n is not None:
                            if isinstance(n, str):
                                net_dirs[n].add(master.terminals[t].direction)
                            else:
                                raise ValueError(
                                    f"{n!r} is not a scalar string, maybe you need to rebuild the connection."
                                )

        term_names: Set[str] = set()
        for net in nets:
            if self.terminals.get(net.name) is not None:
                term_names.add(net.name)  # 连接到当前模块的 terminal，需要引出 terminal
            else:
                assoc_insts = set(net.getAssocInstances())
                assoc_insts.difference_update(insts)
                if len(assoc_insts) > 0:
                    term_names.add(net.name)  # 与其他实例有连接关系，需要引出 terminal

        terms = []
        for tname in term_names:
            dirs = net_dirs[tname]
            if len(dirs) == 0:
                dir = "inout"  # 未知方向，默认 inout
            elif "output" in dirs:
                dir = "output"  # output 优先级最高
            elif "inout" in dirs:
                dir = "inout"  # inout 其次
            else:
                dir = "input"  # input 最低
            terms.append(obj.Terminal(name=tname, direction=dir))

        module = Module(
            name=name,
            terminals=terms,
            instances=insts,
        )

        if design is not None:
            design.modules[name] = module

        module.rebuild()
        return module

    def dumpToSpice(self, *, width_limit: int = 88) -> str:
        # head
        head = "\n".join(
            wrap(
                " ".join([".SUBCKT", self.name, *[t.name for t in self.terminals]]),
                width=width_limit,
                subsequent_indent="+ ",
            )
        )

        # pininfo items
        pin_pairs = []
        for t in self.terminals:
            pair = [t.name]
            if t.direction == "input":
                pair.append("I")
            elif t.direction == "output":
                pair.append("O")
            elif t.direction == "inout":
                pair.append("B")
            pin_pairs.append(":".join(pair))

        pininfo = "\n".join(
            wrap(
                " ".join(pin_pairs),
                width=width_limit,
                initial_indent="*.PININFO ",
                subsequent_indent="*.PININFO ",
            )
        )

        # instance items
        insts = "\n".join(
            i.dumpToSpice(width_limit=width_limit) for i in self.instances
        )

        return "\n".join(x for x in [head, pininfo, insts, ".ENDS"] if x != "")


class ModuleCollection(FigCollection):
    def _valueChecker(self, value: Module) -> None:
        if not isinstance(value, Module):
            raise TypeError("value must be a Module")

    def __iter__(self) -> Iterator[Module]:
        return iter(self.figs)

    def __getitem__(self, key: Union[int, str]) -> Module:
        return super().__getitem__(key)

    def get(self, *args: Any, **kwargs: Any) -> Optional[Module]:
        return super().get(*args, **kwargs)

    def summary(
        self, info_type: Literal["compact", "detail"] = "compact"
    ) -> Dict[str, Any]:
        return {
            "total": len(self),
            "list": [module.summary(info_type) for module in self],
        }

    def rebuild(
        self,
        *,
        mute: bool = False,
        verilog_style: bool = False,
    ) -> None:
        logger = getLogger(__name__, mute=mute)
        for fig in self:
            logger.info(f"Rebuilding module {fig.name!r} ...")
            fig.rebuild(mute=mute, verilog_style=verilog_style)

    def getTopLevels(self) -> Tuple[obj.Module, ...]:
        count = defaultdict(int)
        for module in self:
            for inst in module.instances:
                count[inst.reference.name] += 1
        return tuple(module for module in self if count[module.name] == 0)
