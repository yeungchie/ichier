from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from icutk.string import LineIterator

from ichier.node import Design, Module, DesignateReference, Terminal, Net, Instance
from ichier.utils.escape import makeSafeString

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
    design = Design(priority=priority)
    for line in lineiter:
        lineno = lineiter.line
        if line.upper().startswith(".SUBCKT"):
            lineiter.revert()
            module = parseSubckt(lineiter)
            if design.modules.get(module.name) is not None:
                continue  # 忽略重复的 subckt 定义
            module.lineno = lineno
            design.modules.append(module)
        elif line.upper().startswith(".INCLUDE"):
            continue
    return design


def parseSubckt(lineiter: LineIterator) -> Module:
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

    # .SUBCKT <module_name> <term1> <term2> ...
    tokens = line.split()
    module_name = tokens[1]
    for term in tokens[2:]:
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
            inst, net_names = parseSubcktInstance(lineiter)
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


def parseSubcktInstance(lineiter: LineIterator) -> Tuple[Instance, List[str]]:
    """
    1. user device / connect by order:

    `X1 Y A VSS VSS nmos m=1`

    2. built-in device / connect by order:

    `X2 A VSS $[res] w=1 l=2`

    `X2 A VSS w=1 $[res] l=2`

    3. subcircuit / connect by order:

    `X3 IN VDD VSS OUT / INV`

    4. subcircuit / connect by name:

    `X4 / INV $PINS A=IN VDD=VDD VSS=VSS Z=OUT`
    """
    tokens = lineiter.next.split()
    for line in lineiter:
        if line.startswith("+"):
            tokens += line.split()[1:]
        else:
            lineiter.revert()
            break

    inst_name = tokens[0]
    params = {}
    if "/" in tokens:
        if tokens[1] == "/":
            # X4 / INV $PINS A=IN VDD=VDD VSS=VSS Z=OUT
            ref_name = tokens[2]
            connect_info = {}
            for token in tokens[4:]:
                if "=" in token:
                    term, net = token.split("=")
                    connect_info[term] = net
        elif tokens[-2] == "/":
            # X3 IN VDD VSS OUT / INV
            ref_name = tokens[-1]
            connect_info = tokens[1:-2]
        else:
            raise SpiceInstanceError(
                f"Invalid instance definition at line {lineiter.line}:\n>>> {' '.join(tokens)}"
            )
    elif set(("$pins", "$PINS")) & set(tokens):
        # X4 INV $PINS A=IN VDD=VDD VSS=VSS Z=OUT
        ref_name = tokens[1]
        connect_info = {}
        for token in tokens[2:]:
            if "=" in token:
                term, net = token.split("=")
                connect_info[term] = net
    else:
        # X1 Y A VSS VSS nmos m=1
        # X2 A VSS 1.2 $[res] w=1 l=2
        # X2 A VSS w=1 1.2 $[res] l=2
        nets_and_ref = []
        param_order = 1
        for token in tokens[1:]:
            if "=" in token:
                name, value = token.split("=")
                params[name] = value
            elif token[0].isdigit():
                params[f"param_order_{param_order}"] = token
                param_order += 1
            else:
                nets_and_ref.append(token)

        ref_name = nets_and_ref[-1]
        if ref_name.startswith("$[") and ref_name.endswith("]"):
            ref_name = DesignateReference(ref_name[2:-1])

        connect_info = nets_and_ref[:-1]

    if isinstance(connect_info, dict):
        connect_info = {t: makeSafeString(n) for t, n in connect_info.items()}
    elif isinstance(connect_info, list):
        connect_info = [makeSafeString(n) for n in connect_info]

    inst = Instance(
        name=inst_name,
        reference=ref_name,
        connection=connect_info,
        parameters=params,
    )

    if isinstance(connect_info, dict):
        net_names = list(connect_info.values())
    else:
        net_names = connect_info

    return (inst, net_names)
