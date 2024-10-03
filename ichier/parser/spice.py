from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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


def fromFile(file: str) -> ichier.Design:
    with open(file, "r", encoding="utf-8") as f:
        design = fromIterable(f)
    design.name = file
    return design


def fromString(string: str) -> ichier.Design:
    return fromIterable(string.splitlines())


def fromIterable(data: Iterable) -> ichier.Design:
    data = LineIterator(data)
    design = ichier.Design()
    for line in data:
        # subckt
        if line.upper().startswith(".SUBCKT"):
            subckt = [line]
            for line in data:
                subckt.append(line)
                if line.upper().startswith(".ENDS"):
                    break
            design.modules.append(subcktParser(subckt))

    return design


def subcktParser(strings: Sequence[str]) -> ichier.Module:
    module_name: Optional[str] = None
    terminals: Dict[str, ichier.Terminal] = {}
    nets: Dict[str, ichier.Net] = {}
    instances: Dict[str, ichier.Instance] = {}
    parameters: Dict[str, str] = {}

    data = LineIterator(strings, chomp=True)

    line = data.next
    if not line.upper().startswith(".SUBCKT"):
        # 第一行开头不是 .SUBCKT 说明不是有效的 subckt 定义
        raise SpiceSubcktError(f"Invalid data at line {data.line}:\n>>> {data.last1}")

    # .SUBCKT <module_name> <term1> <term2> ...
    tokens = line.split()
    module_name = tokens[1]
    for term in tokens[2:]:
        terminals[term] = ichier.Terminal(name=term)

    # 看看 term 定义是否完整
    for line in data:
        if line.startswith("+"):
            # 下一行 + 开头说明 term 还没定义结束
            for term in line.split()[1:]:
                terminals[term] = ichier.Terminal(name=term)
        else:
            data.revert()
            break

    for line in data:
        if line.strip() == "":
            continue  # 跳过空行
        elif line.startswith("*"):
            if line.upper().startswith("*.PININFO"):
                data.revert()
                for term, dir in __subcktPinInfoParser(data).items():
                    if term in terminals:
                        terminals[term].direction = dir
                    else:
                        raise SpicePinInfoError(
                            f"Invalid pininfo of pin '{term}' at subkct {module_name} ."
                        )
            else:
                continue  # 跳过其他注释
        elif line.startswith("."):
            if line.upper().startswith(".ENDS"):
                break
            elif line.upper().startswith(".PARAM"):
                data.revert()
                for name, value in __subcktParamParser(data).items():
                    parameters[name] = value
            else:
                continue
        else:
            data.revert()
            inst, net_names = __subcktInstanceParser(data)
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


def __subcktPinInfoParser(data: LineIterator) -> Dict[str, str]:
    """
    `*.PININFO A:I B:I Y:O VDD:B VSS:B`
    """
    text = data.next
    pininfo = {}
    for token in text.split()[1:]:
        term, dir = token.split(":")
        pininfo[term] = {
            "I": "in",
            "O": "out",
            "B": "inout",
        }[dir.upper()]
    return pininfo


def __subcktParamParser(data: LineIterator) -> Dict[str, str]:
    """
    `.PARAMS A=1 B=2 C=3`
    """
    text = data.next
    params = {}
    for token in text.split()[1:]:
        name, value = token.split("=")
        params[name] = value
    return params


def __subcktInstanceParser(
    data: LineIterator,
) -> Tuple[ichier.Instance, List[str]]:
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
    tokens = data.next.split()
    for line in data:
        if line.startswith("+"):
            tokens += line.split()[1:]
        else:
            data.revert()
            break

    inst_name = tokens[0]
    params = {}
    if "/" in tokens:
        if tokens[1] == "/":
            # X4 / INV $PINS A=IN VDD=VDD VSS=VSS Z=OUT
            ref_name = tokens[2]
            if not tokens[3].upper().startswith("$PINS"):
                raise SpiceInstanceError(
                    f"Invalid instance definition at line {data.line}:\n>>> {' '.join(tokens)}"
                )
            connect_info = {}
            for token in tokens[4:]:
                if "=" in token:
                    term, net = token.split("=")
                    connect_info[term] = net
        else:
            # X3 IN VDD VSS OUT / INV
            ref_name = tokens[-1]
            connect_info = tokens[1:-2]
    else:
        # X1 Y A VSS VSS nmos m=1
        # X2 A VSS $[res] w=1 l=2
        # X2 A VSS w=1 $[res] l=2
        nets_and_ref = []
        for token in tokens[1:]:
            if "=" in token:
                name, value = token.split("=")
                params[name] = value
            else:
                nets_and_ref.append(token)

        ref_name = nets_and_ref[-1]
        if ref_name.startswith("$"):
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
