from __future__ import annotations
from typing import Dict, Optional, Tuple

from icutk.string import LineIterator

from ichier.node import Design, Module, Terminal, Net, Instance
from .p_inst import InstParser

__all__ = []


class SpiceFormatError(Exception):
    pass


class SpiceSubcktError(SpiceFormatError):
    pass


class SpicePinInfoError(SpiceFormatError):
    pass


class SpiceInstanceError(SpiceFormatError):
    pass


class SpiceIncludeError(SpiceFormatError):
    pass


def parse(
    lineiter: LineIterator,
    priority: Tuple[int, ...] = (),
) -> Design:
    inst_parser = InstParser()
    design = Design(priority=priority)
    for line in lineiter:
        lineno = lineiter.line
        if line.upper().startswith(".SUBCKT"):
            lineiter.revert()
            module = parseSubckt(lineiter, inst_parser=inst_parser)
            if design.modules.get(module.name) is not None:
                continue  # 忽略重复的 subckt 定义
            module.lineno = lineno
            design.modules.append(module)
        elif line.upper().startswith(".INCLUDE"):
            continue
    return design


def parseSubckt(
    lineiter: LineIterator,
    inst_parser: Optional[InstParser] = None,
) -> Module:
    module_name: Optional[str] = None
    terminals: Dict[str, Terminal] = {}
    nets: Dict[str, Net] = {}
    instances: Dict[str, Instance] = {}
    parameters: Dict[str, str] = {}

    line = lineiter.next
    if not line.upper().startswith(".SUBCKT"):
        # 第一行开头不是 .SUBCKT 说明不是有效的 subckt 定义
        raise SpiceSubcktError(
            f"Invalid data at line {lineiter.line}:\n>>> {lineiter.last1}"
        )

    # .SUBCKT <module_name> <term1> <term2> ... <key1=value1> <key2=value2> ...
    tokens = line.split()
    module_name = tokens[1]
    for term in tokens[2:]:
        if "=" in term:
            k, v = term.split("=")
            parameters[k] = v
        else:
            terminals[term] = Terminal(name=term)

    # 看看 term 定义是否完整
    for line in lineiter:
        if line.startswith("+"):
            # 下一行 + 开头说明 term 还没定义结束
            for term in line.split()[1:]:
                terminals[term] = Terminal(name=term)
        else:
            lineiter.revert()
            break

    for line in lineiter:
        if line.strip() == "":
            continue  # 跳过空行
        elif line.startswith("$"):
            continue  # 跳过 $ 注释
        elif line.startswith("*"):
            if line.upper().startswith("*.PININFO"):
                lineiter.revert()
                for term, dir in parseSubcktPinInfo(lineiter).items():
                    if term in terminals:
                        terminals[term].direction = dir
                    else:
                        raise SpicePinInfoError(
                            f"Invalid pininfo of pin '{term}' at subkct {module_name} ."
                        )
            else:
                continue  # 跳过其他 * 注释
        elif line.startswith("."):
            if line.upper().startswith(".ENDS"):
                break
            elif line.upper().startswith(".PARAM"):
                lineiter.revert()
                for name, value in parseSubcktParams(lineiter).items():
                    parameters[name] = value
            else:
                continue
        else:
            lineiter.revert()
            inst, net_names = parseSubcktInstance(lineiter, parser=inst_parser)
            instances[inst.name] = inst
            for name in net_names:
                if name not in nets:
                    nets[name] = Net(name=name)

    return Module(
        name=module_name,
        terminals=terminals.values(),
        nets=nets.values(),
        instances=instances.values(),
        parameters=parameters,
    )


def parseSubcktPinInfo(lineiter: LineIterator) -> Dict[str, str]:
    """
    `*.PININFO A:I B:I Y:O VDD:B VSS:B`
    """
    text = lineiter.next
    pininfo = {}
    for token in text.split()[1:]:
        term, dir = token.split(":")
        pininfo[term] = {
            "I": "input",
            "O": "output",
            "B": "inout",
        }[dir.upper()]
    return pininfo


def parseSubcktParams(lineiter: LineIterator) -> Dict[str, str]:
    """
    `.PARAMS A=1 B=2 C=3`
    """
    text = lineiter.next
    params = {}
    for token in text.split()[1:]:
        name, value = token.split("=")
        params[name] = value
    return params


def parseSubcktInstance(
    lineiter: LineIterator,
    parser: Optional[InstParser] = None,
) -> Tuple[Instance, list]:
    if parser is None:
        parser = InstParser()
    raw_lines = [code := lineiter.next]
    for line in lineiter:
        if line.startswith("+"):
            raw_lines.append(line)
            code += " " + line[1:]
        else:
            lineiter.revert()
            break
    raw = "\n".join(raw_lines)
    try:
        inst = parser.parse(code)
        inst.raw = raw
    except SyntaxError as e:
        inst = Instance(
            reference=None,
            name=code.split()[0],
            raw=raw,
            error=e,
        )
        # raise SpiceInstanceError(
        #     f"{e}\nInvalid instance definition at line {lineiter.line}:\n>>> {code}"
        # )
    if isinstance(inst.connection, dict):
        net_names = list(inst.connection.values())
    else:
        net_names = list(inst.connection)
    return inst, net_names
