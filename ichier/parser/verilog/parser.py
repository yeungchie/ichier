from typing import Callable, List, Literal, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from ply.yacc import yacc

from .lexer import VerilogLexer
from ichier import Design, Module, Instance, Terminal, Net

__all__ = [
    "VerilogParser",
]


class Include:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = path

    @property
    def path(self) -> Path:
        return self.__path

    @path.setter
    def path(self, value: Union[str, Path]) -> None:
        self.__path = Path(value)

    def __repr__(self) -> str:
        return f"Include({self.path})"

    def read(self) -> str:
        return self.path.read_text()

    def parse(self) -> "Design": ...


@dataclass
class ModuleNetItem:
    type: Literal["input", "output", "inout", "wire"]
    name_list: List[str]


class ModuleSpecifyItem(dict):
    pass


class ModulePortDict(dict):
    def filling(self, other: dict) -> None:
        for name, dir in other.items():
            if name in self:
                if self[name] != dir:
                    raise ValueError(f"Conflict direction of port {name}")
            else:
                self[name] = dir


@dataclass
class ModuleInstItem:
    name: str
    reference: str
    connect_by: Literal["name", "order"]
    connection: Optional[Union[dict, list]]


class VerilogParser:
    def p_design(self, p):  # 设计
        """
        design  :  design_item_list
        """
        design = Design()
        for item in p[1]:
            if isinstance(item, Module):
                if design.modules.get(item.name) is not None:
                    continue  # 忽略重复的 module 定义
                design.modules.append(item)
        p[0] = design

    def p_design_item_list(self, p):  # 设计项列表
        """
        design_item_list  :  design_item_list  design_item
                          |  design_item
        """
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_design_item(self, p):  # 设计项
        """
        design_item  :  module
                     |  include
        """
        p[0] = p[1]

    def p_include(self, p):  # 包含外部网表文件
        """
        include  :  INCLUDE
        """
        p[0] = Include(path=p[1])

    def p_module(self, p):  # 模块定义
        """
        module  :  module_head  module_item_list  ENDMODULE
                |  module_head  ENDMODULE
        """
        module_name = p[1]["module_name"]
        port_order = {name: [] for name in p[1]["port_order"]}
        port_dir = ModulePortDict()
        nets = {}
        insts = {}
        params = {"specify": {}}

        if len(p) == 4:
            for item in p[2]:
                if isinstance(item, ModuleNetItem):
                    for name in item.name_list:
                        if nets.get(name) is None:
                            nets[name] = Net(name=name)
                        if item.type in ["input", "output", "inout"]:
                            port_name = name.partition("[")[0]
                            if port_name not in port_order:
                                raise ValueError(f"Undefined port {name!r}")
                            port_order[port_name].append(name)
                            port_dir.filling({name: item.type})
                elif isinstance(item, ModuleInstItem):
                    insts[item.name] = Instance(
                        name=item.name,
                        reference=item.reference,
                        connection=item.connection,
                    )
                elif isinstance(item, ModuleSpecifyItem):
                    params["specify"].update(item)
        terms = []
        for port, members in port_order.items():
            for member in members or [port]:
                terms.append(Terminal(name=member, direction=port_dir[member]))
        p[0] = Module(
            name=module_name,
            terminals=terms,
            nets=nets.values(),
            instances=insts.values(),
            parameters=params,
        )

    def p_module_item_list(self, p):  # 模块项列表
        """
        module_item_list  :  module_item_list  module_item
                          |  module_item
        """
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_module_item(self, p):  # 模块项
        """
        module_item  :  module_net
                     |  module_specify
                     |  module_inst
        """
        p[0] = p[1]

    def p_module_net(self, p):  # 模块端口方向和网络声明
        """
        module_net  :  net_type  id_list  ';'
                    |  net_type  range  ID  ';'
        """
        if len(p) == 4:
            net_names = p[2]
        else:
            net_names = ["%s[%d]" % (p[3], i) for i in p[2]]
        p[0] = ModuleNetItem(
            type=p[1],
            name_list=net_names,
        )

    def p_net_type(self, p):  # 端口方向和网络关键字
        """
        net_type  :  INPUT
                  |  OUTPUT
                  |  INOUT
                  |  WIRE
        """
        p[0] = p[1]

    def p_module_inst(self, p):  # 模块例化
        """
        module_inst  :  id  id  '('  ')'  ';'
                     |  id  id  '('  connection  ')'  ';'
        """
        ref_name = p[1]
        inst_name = p[2]
        connection = None
        if len(p) == 7:
            connection = p[4]
        p[0] = ModuleInstItem(
            name=inst_name,
            reference=ref_name,
            connect_by="name",
            connection=connection,
        )

    def p_connection(self, p):  # 端口连接
        """
        connection  :  connect_by_name_dict
                    |  connect_by_order_list
        """
        p[0] = p[1]

    def p_connect_by_name_dict(self, p):  # 多个实例端口命名连接
        """
        connect_by_name_dict  :  connect_by_name_dict  ','  connect_by_name
                              |  connect_by_name
        """
        p[0] = p[1]
        if len(p) == 4:
            p[0].update(p[3])

    def p_connect_by_name(self, p):  # 实例端口命名连接
        """
        connect_by_name  :  '.'  id  '('  ')'
                         |  '.'  id  '('  net_description  ')'
        """
        if len(p) == 5:
            p[0] = {p[2]: None}
        else:
            p[0] = {p[2]: p[4]}

    def p_connect_by_order_list(self, p):  # 多个实例端口顺序连接
        """
        connect_by_order_list  :  connect_by_order_list  ','  connect_by_order
                               |  connect_by_order
        """
        if len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = [p[1]]

    def p_connect_by_order(self, p):  # 实例端口顺序连接
        """
        connect_by_order  :  net_description
        """
        p[0] = p[1]

    def p_net_description(self, p):  # 网络描述
        """
        net_description  :  net
                         |  group_net
        """
        if isinstance(p[1], list) and len(p[1]) == 1:
            p[0] = p[1][0]
        else:
            p[0] = p[1]

    def p_group_net(self, p):  # 一个总线端口连接到多个网络
        """
        group_net  :  '{'  net_list  '}'
        """
        p[0] = p[2]

    def p_net_list(self, p):  # 多个网络定义
        """
        net_list  :  net_list  ','  net
                  |  net
        """
        p[0] = p[1]
        if len(p) == 4:
            p[0] += p[3]

    def p_net(self, p):  # 三种网络定义 net, net[0], net[1:0]
        """
        net  :  id
             |  bit_net
             |  bus_net
        """
        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]]

    def p_bit_net(self, p):  # 单比特形式的网络
        """
        bit_net  :  ID  '['  INT  ']'
        """
        p[0] = "%s[%d]" % (p[1], p[3])

    def p_bus_net(self, p):  # 总线形式的网络
        """
        bus_net  :  ID  range
        """
        p[0] = ["%s[%d]" % (p[1], i) for i in p[2]]

    def p_range(self, p):  # 定义总线范围
        """
        range  :  '['  INT  ':'  INT  ']'
        """
        start, end = p[2], p[4]
        if start <= end:
            step = 1
        else:
            step = -1
        p[0] = range(start, end + step, step)

    def p_module_head(self, p):  # 模块声明头部
        """
        module_head  :  MODULE  id  '('  id_list  ')'  ';'
                     |  MODULE  id  ';'
        """
        data = {
            "module_name": p[2],
            "port_order": [],
        }
        if len(p) == 7:
            data["port_order"] = p[4]
        p[0] = data

    def p_id_list(self, p):
        """
        id_list  :  id_list  ','  id
                 |  id
        """
        if len(p) == 4:
            p[0] = p[1] + [p[3]]
        else:
            p[0] = [p[1]]

    def p_id(self, p):  # 标识符
        """
        id  :  ID
            |  ESC_ID
        """
        p[0] = p[1]

    def p_module_specify(self, p):
        """
        module_specify  :  SPECIFY  specparam_list  ENDSPECIFY
        """
        p[0] = ModuleSpecifyItem(p[2])

    def p_specparam_list(self, p):
        """
        specparam_list  :  specparam_list  specparam
                        |  specparam
        """
        p[0] = p[1]
        if len(p) == 3:
            p[0].update(p[2])

    def p_specparam(self, p):
        """
        specparam  :  SPECPARAM  id  '='  scalar  ';'
        """
        p[0] = {p[2]: p[4]}

    def p_scalar(self, p):  # 标量
        """
        scalar  :  num
                |  STRING
        """
        p[0] = p[1]

    def p_num(self, p):  # 数字
        """
        num  :  INT
             |  FLOAT
        """
        p[0] = p[1]

    def p_error(self, t):
        if t is None:
            raise SyntaxError("Syntax error at EOF")
        else:
            raise SyntaxError(f"Syntax error at line {t.lineno} - {t.value!r}")

    def __init__(
        self,
        *,
        cb_input: Optional[Callable] = None,
        cb_token: Optional[Callable] = None,
    ):
        self.lexer = VerilogLexer(
            cb_input=cb_input,
            cb_token=cb_token,
        )
        self.tokens = self.lexer.tokens
        self.parser = yacc(module=self, debug=False, write_tables=False)

    def parse(self, text) -> Design:
        return self.parser.parse(text, lexer=self.lexer)
