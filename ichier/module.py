from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    Literal,
    Optional,
    Set,
    Union,
)
from collections import defaultdict

from icutk.log import getLogger

import ichier.obj as icobj
from .fig import Fig, FigCollection

__all__ = [
    "Module",
    "ModuleCollection",
    "Reference",
]


class Module(Fig):
    def __init__(
        self,
        name: str,
        terminals: Iterable["icobj.Terminal"] = (),
        nets: Iterable["icobj.Net"] = (),
        instances: Iterable["icobj.Instance"] = (),
        parameters: Optional[Dict[str, Any]] = None,
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

    def makeModule(
        self,
        name: str,
        instances: Iterable[Union[str, "icobj.Instance"]],
        to_design: Optional["icobj.Design"] = None,
    ) -> "Module":
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
            if not isinstance(to_design, icobj.Design):
                raise TypeError("to_design must be a Design")
            design = to_design
        else:
            design = self.getDesign()
        if design is not None and name in design.modules:
            raise ValueError(
                f"Module {name!r} already exists in design {design.name!r}"
            )

        insts: Set[icobj.Instance] = set()
        nets: Set[icobj.Net] = set()
        net_dirs: DefaultDict[str, set] = defaultdict(set)

        for i in instances:
            inst = self.instances.get(str(i))
            if inst is None:
                raise ValueError(f"Instance '{i!s}' not found in module {self.name!r}")
            insts.add(inst)
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
            terms.append(icobj.Terminal(name=tname, direction=dir))

        module = Module(
            name=name,
            terminals=terms,
            instances=insts,
        )

        if design is not None:
            design.modules[name] = module

        module.rebuild()
        return module


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
            "list": [module.summary(info_type) for module in self.figs],
        }

    def rebuild(self) -> None:
        logger = getLogger(__name__)
        for fig in self:
            logger.info(f"Rebuilding module {fig.name!r} ...")
            fig.rebuild()


class Reference(str):
    def __new__(cls, name: str, instance: "icobj.Instance"):
        return super().__new__(cls, name)

    def __init__(self, name: str, instance: "icobj.Instance") -> None:
        if not isinstance(instance, icobj.Instance):
            raise TypeError("instance must be an Instance")
        self.__name = str(self)
        self.__instance = instance

    def __repr__(self) -> str:
        return f"Reference({super().__repr__()})"

    def __str__(self) -> str:
        return super().__str__()

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    def name(self) -> str:
        return self.__name

    @property
    def instance(self) -> "icobj.Instance":
        return self.__instance

    def getMaster(self) -> Optional[Module]:
        design = self.instance.getDesign()
        if design is None:
            return
        return design.modules.get(self.name)
