from typing import List, Iterable, Dict, Optional, Tuple, Union
import re

from icutk.lex import BaseLexer, tokensToDict, LexToken, TOKEN
from icutk.string import evalToBasicType

import ichier

__all__ = []


class VerilogLexer(BaseLexer):
    tokens = BaseLexer.tokens + [
        "COMMENT_LINE",  # //
        "COMMENT_BLOCK",  # /* */
        "CONSTRAINT",  # (* *)
        "PREPROCESS",  # `xxx
        "MODULE_HEAD",  # module ... ;
        "MODULE_END",  # endmodule
        "SPECIFY_START",  # specify
        "SPECIFY_END",  # endspecify
        "PARAMETER",  # parameter ... ;
        "INPUT",  # input ... ;
        "OUTPUT",  # output ... ;
        "INOUT",  # inout ... ;
        "WIRE",  # wire ... ;
        "SPECPARAM",  # specparam ... ;
        "INSTANCE",  # inst_name module_name ( ... );
        "STRING",  # "..."
    ]

    t_COMMENT_LINE = r"//.*"
    t_CONSTRAINT = r"\(\*([^*]|\*[^)])*\*\)"
    t_PREPROCESS = r"`.+"
    t_MODULE_END = r"endmodule"
    t_SPECIFY_START = r"specify"
    t_SPECIFY_END = r"endspecify"

    def t_COMMENT_BLOCK(self, t: LexToken):
        r"/\*([^*]|\*[^/])*\*/"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_MODULE_HEAD(self, t: LexToken):
        r"module\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_PARAMETER(self, t: LexToken):
        r"parameter\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_INPUT(self, t: LexToken):
        r"input\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_OUTPUT(self, t: LexToken):
        r"output\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_INOUT(self, t: LexToken):
        r"inout\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_WIRE(self, t: LexToken):
        r"wire\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_SPECPARAM(self, t: LexToken):
        r"specparam\s+[^;]*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_INSTANCE(self, t: LexToken):
        r"\w+\s*(\#\(.*?\)\s*|\s+)\w+\s*\(\s*[^;]*\s*\)\s*;"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_STRING(self, t: LexToken):
        r'"[^"]*"'
        t.value = t.value[1:-1]
        return t


class ModuleHeadLexer(BaseLexer):
    tokens = BaseLexer.tokens + [
        "MODULE_NAME",  # module name
        "PARAMETER_INFO",  # #( ... )
        "PORT_NAMES",  # ( ... );
    ]

    def t_MODULE_NAME(self, t: LexToken):
        r"module\s+(\w+)"
        t.value = t.value.split()[1]
        return t

    def t_PARAMETER_INFO(self, t: LexToken):
        r"\#\([^)]*\)"
        return t

    def t_PORT_NAMES(self, t: LexToken):
        r"(?<!\#)\([^)]*\)\s*;"
        t.value = re.sub(r"\(|\)|,|;", " ", t.value).split()
        return t


class NetsSplitLexer(BaseLexer):
    tokens = BaseLexer.tokens + [
        "BUS_NET",  # [0:7] name ;
        "MULTI_NET",  # name1, name2, ... ;
    ]

    def t_BUS_NET(self, t: LexToken):
        r"(\[\s*\d+\s*:\s*\d+\s*\]\s*\w+|\w+\s*\[\s*\d+\s*:\s*\d+\s*\])\s*;"
        start, end = map(int, re.search(r"(\d+)\s*:\s*(\d+)", t.value).groups())  # type: ignore
        net_name = re.search(r"(\w+)\s*[;\[]", t.value).group(1)  # type: ignore
        reversep = False
        if start > end:
            start, end = end, start
            reversep = True
        nets = [f"{net_name}[{i}]" for i in range(start, end + 1)]
        if reversep:
            nets.reverse()
        t.value = nets
        return t

    def t_MULTI_NET(self, t: LexToken):
        r"\w+(\s*,\s*\w+)*\s*;"
        t.value = re.sub(r",|;", " ", t.value).split()
        return t

    def nets(self) -> List[str]:
        td = tokensToDict(self)
        mn = td.get("MULTI_NET")
        bn = td.get("BUS_NET")
        nets = []
        if mn is None and bn is None:
            raise ValueError("Empty net definition" f"{td}")
        elif mn is not None and bn is not None:
            raise ValueError("Invalid net definition")
        elif mn is not None:
            for t in mn:
                nets.extend(t.value)
        elif bn is not None:
            for t in bn:
                nets.extend(t.value)
        return nets


class InstanceLexer(BaseLexer):
    tokens = BaseLexer.tokens + [
        "PARAMETER_INFO_EMPTY",  # #( )
        "CONNECTION_INFO_EMPTY",  # ( );
        "PARAMETER_INFO_BY_NAME",  # #( .key(value), ... )
        "PARAMETER_INFO_BY_ORDER",  # #( value, ... )
        "CONNECTION_INFO_BY_NAME",  # ( .terminal(net), ... );
        "CONNECTION_INFO_BY_ORDER",  # ( net, ... );
    ]

    def t_PARAMETER_INFO_EMPTY(self, t: LexToken):
        r"\#\(\s*\)"
        t.value = None
        return t

    def t_CONNECTION_INFO_EMPTY(self, t: LexToken):
        r"(?<!\#)\(\s*\)\s*;"
        t.value = None
        return t

    __pvp = r"[\w\.\"]+"  # parameter value pattern
    __pbnp = rf"\.(\w+)\s*\(\s*({__pvp})\s*\)"  # parameter by name pattern

    @TOKEN(rf"\#\(\s*{__pbnp}(\s*,\s*{__pbnp})*\s*\)")
    def t_PARAMETER_INFO_BY_NAME(self, t: LexToken):
        param: Dict[str, Union[str, int, float]] = {}
        for m in re.finditer(self.__pbnp, t.value[2:-1]):
            param[m.group(1)] = evalToBasicType(m.group(2))
        t.value = param
        return t

    @TOKEN(rf"\#\(\s*{__pvp}(\s*,\s*{__pvp})*\s*\)")
    def t_PARAMETER_INFO_BY_ORDER(self, t: LexToken):
        params: List[Union[str, int, float]] = []
        for p in t.value[2:-1].replace(",", " ").split():
            params.append(evalToBasicType(p))
        t.value = params
        return t

    __cnp = r"\w+(\s*\[\s*\d+(\s*\:\s*\d+)?\s*\])?"  # connection net pattern
    __cbnp = rf"\.(\w+)\s*\(\s*({__cnp})\s*\)"  # connection by name pattern

    @TOKEN(r"(?<!\#)" rf"\(\s*{__cbnp}(\s*,\s*{__cbnp})*\s*\)\s*;")
    def t_CONNECTION_INFO_BY_NAME(self, t: LexToken):
        connect: Dict[str, str] = {}
        for m in re.finditer(self.__cbnp, t.value[:-1].rstrip()[1:-1]):
            term = m.group(1)
            for net in flattenMemberName(m.group(2)):
                connect[re.sub(r"^\w+", term, net)] = net
            # connect[m.group(1)] = m.group(2)
        t.value = connect
        return t

    @TOKEN(r"(?<!\#)" rf"\(\s*{__cnp}(\s*,\s*{__cnp})*\s*\)\s*;")
    def t_CONNECTION_INFO_BY_ORDER(self, t: LexToken):
        nets = []
        for item in t.value[:-1].rstrip()[1:-1].split(","):
            nets += flattenMemberName(item)
        t.value = nets
        return t


def flattenMemberName(s: str) -> Tuple[str, ...]:
    if not isinstance(s, str):
        raise TypeError(f"Invalid member name: {s}")
    s = s.strip()
    if s == "":
        return ()
    if "," in s:
        names = []
        for item in s.split(","):
            names += flattenMemberName(item)
        return tuple(names)
    name_pattern = r"(?P<name>\w+)"
    slice_pattern = r"\[\s*(?P<start>\d+)(\s*:\s*(?P<end>\d+))?\]"
    pattern1 = rf"{name_pattern}\s*({slice_pattern})?"
    pattern2 = rf"({slice_pattern})?\s*{name_pattern}"
    m = re.fullmatch(pattern1, s) or re.fullmatch(pattern2, s)
    if m is None:
        raise ValueError(f"Invalid member name: {s}")
    name = m.group("name")
    start = m.group("start")
    end = m.group("end")
    if start is None and end is None:
        return (name,)
    elif end is None:
        start = int(start)
        return (f"{name}[{start}]",)
    else:
        reversep = False
        start = int(start)
        end = int(end)
        if start > end:
            start, end = end, start
            reversep = True
        names = [f"{name}[{i}]" for i in range(start, end + 1)]
        if reversep:
            names.reverse()
        return tuple(names)


def fromFile(file: str) -> ichier.Design:
    with open(file, "r") as f:
        text = f.read()
    design = fromString(text)
    design.name = file
    return design


def fromString(string: str) -> ichier.Design:
    lexer = VerilogLexer(string)

    module_tokens = []
    module_inside = False
    modules: List[ichier.Module] = []

    for token in lexer:
        if module_inside:
            module_tokens.append(token)
            if token.type == "MODULE_END":
                module_inside = False
                modules.append(_moduleAnalyser(module_tokens))
                module_tokens = []
        elif token.type == "MODULE_HEAD":
            module_tokens.append(token)
            module_inside = True
    return ichier.Design(modules=modules)


def _moduleAnalyser(tokens: Iterable[LexToken]) -> ichier.Module:
    td = tokensToDict(tokens)

    # module head
    module_head = td.get("MODULE_HEAD")
    if module_head is None:
        raise ValueError("Invalid module head")
    head_td = tokensToDict(ModuleHeadLexer(module_head[0].value))

    ## module name
    module_name = head_td.get("MODULE_NAME")
    if module_name is None:
        raise ValueError("Invalid module name")
    module_name = module_name[0].value

    ## module ports
    module_ports = head_td.get("PORT_NAMES")
    terminals: List[ichier.Terminal] = []
    if module_ports is not None:
        port_dir: Dict[str, Optional[str]] = {}
        for t in module_ports:
            for p in t.value:
                port_dir[p] = None

        # input, output, inout
        full_ports = []
        for dir, token in {
            "in": "INPUT",
            "out": "OUTPUT",
            "inout": "INOUT",
        }.items():
            for t in td.get(token, []):
                for p in NetsSplitLexer(re.sub(r"^\w+\s*", "", t.value)).nets():
                    pname = p.partition("[")[0]
                    if pname not in port_dir:
                        raise ValueError(
                            f"Invalid port direction definition for module {module_name}: {p}"
                        )
                    if port_dir[pname] is not None and port_dir[pname] != dir:
                        raise ValueError(
                            f"Duplicated port direction for module {module_name}: {p}"
                        )
                    port_dir[pname] = dir
                    full_ports.append(p)

        # 检查未定义方向的端口
        for p in port_dir:
            if port_dir[p] is None:
                raise ValueError(
                    f"Undefined port direction for module {module_name}: {p}"
                )
        for p in full_ports:
            pname = p.partition("[")[0]
            terminals.append(ichier.Terminal(name=p, direction=port_dir[pname]))  # type: ignore

    # wire
    nets: List[ichier.Net] = []
    for t in td.get("WIRE", []):
        for n in NetsSplitLexer(re.sub(r"^\w+\s*", "", t.value)).nets():
            nets.append(ichier.Net(name=n))

    return ichier.Module(
        name=module_name,
        terminals=terminals,
        nets=nets,
        instances=[_instanceAnalyser(t) for t in td.get("INSTANCE", [])],
    )


def _instanceAnalyser(token: LexToken) -> ichier.Instance:
    td = tokensToDict(InstanceLexer(token.value))
    words = td.get("WORD", [])
    if len(words) != 2:
        raise ValueError(f'Invalid instance definition\n"""\n{token.value}\n"""')

    ref, inst = (t.value for t in words)

    connect = ()
    if td.get("CONNECTION_INFO_EMPTY"):
        pass
    else:
        t = td.get("CONNECTION_INFO_BY_NAME") or td.get("CONNECTION_INFO_BY_ORDER")
        if t is not None:
            connect = t[0].value

    params = {}
    if td.get("PARAMETER_INFO_EMPTY"):
        pass
    else:
        t = td.get("PARAMETER_INFO_BY_NAME")  # or td.get("PARAMETER_INFO_BY_ORDER")
        if t is not None:
            params = t[0].value

    return ichier.Instance(
        name=inst,
        reference=ref,
        connection=connect,
        parameters=params,
    )
