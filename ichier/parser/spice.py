from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

from icutk.string import LineIterator
import ichier

__all__ = []


class SpiceFormatError(Exception):
    pass


class SpiceSubcktError(SpiceFormatError):
    pass


class SpicePinInfoError(SpiceFormatError):
    pass


class SpiceInstanceError(SpiceFormatError):
    pass


def fromFile(
    file: Union[str, Path],
    cb_next: Optional[Callable] = None,
) -> ichier.Design:
    path = Path(file)
    with open(path, "rt", encoding="utf-8") as f:
        design = fromIterable(f.readlines(), cb_next=cb_next)
    design.name = path.name
    design.path = path
    return design


def fromString(string: str, cb_next: Optional[Callable] = None) -> ichier.Design:
    return fromIterable(string.splitlines(), cb_next=cb_next)


def fromIterable(data: Iterable, cb_next: Optional[Callable] = None) -> ichier.Design:
    return __parse(
        LineIterator(
            data=data,
            chomp=True,
            cb_next=cb_next,
        )
    )


def __parse(lineiter: LineIterator) -> ichier.Design:
    design = ichier.Design()
    for line in lineiter:
        if line.upper().startswith(".SUBCKT"):
            lineiter.revert()
            module = __subcktParse(lineiter)
            if design.modules.get(module.name) is not None:
                continue  # 忽略重复的 subckt 定义
            design.modules.append(module)
    return design


def __subcktParse(lineiter: LineIterator) -> ichier.Module:
    module_name: Optional[str] = None
    terminals: Dict[str, ichier.Terminal] = {}
    nets: Dict[str, ichier.Net] = {}
    instances: Dict[str, ichier.Instance] = {}
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
        terminals[term] = ichier.Terminal(name=term)

    # 看看 term 定义是否完整
    for line in lineiter:
        if line.startswith("+"):
            # 下一行 + 开头说明 term 还没定义结束
            for term in line.split()[1:]:
                terminals[term] = ichier.Terminal(name=term)
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
                for term, dir in __subcktPinInfoParse(lineiter).items():
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
                for name, value in __subcktParamParse(lineiter).items():
                    parameters[name] = value
            else:
                continue
        else:
            lineiter.revert()
            inst, net_names = __subcktInstanceParse(lineiter)
            instances[inst.name] = inst
            for name in net_names:
                if name not in nets:
                    nets[name] = ichier.Net(name=name)

    return ichier.Module(
        name=module_name,
        terminals=terminals.values(),
        nets=nets.values(),
        instances=instances.values(),
        parameters=parameters,
    )


def __subcktPinInfoParse(lineiter: LineIterator) -> Dict[str, str]:
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


def __subcktParamParse(lineiter: LineIterator) -> Dict[str, str]:
    """
    `.PARAMS A=1 B=2 C=3`
    """
    text = lineiter.next
    params = {}
    for token in text.split()[1:]:
        name, value = token.split("=")
        params[name] = value
    return params


def __subcktInstanceParse(lineiter: LineIterator) -> Tuple[ichier.Instance, List[str]]:
    """
    1. active device / connect by order:

    `X1 Y A VSS VSS nmos m=1`

    2. passive device / connect by order:

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
            ref_name = ref_name[2:-1]

        connect_info = nets_and_ref[:-1]

    inst = ichier.Instance(
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
