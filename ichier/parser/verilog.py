from typing import List, Iterable, Dict, Optional, Tuple, Union
from pathlib import Path
import re

from icutk.lex import BaseLexer, tokensToDict, LexToken, TOKEN
from icutk.string import evalToBasicType

import ichier

__all__ = []


class VerilogParser(BaseLexer):
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

    BaseLexer.t_WORD += r"|\\\S+"
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

    def parse(self) -> "ichier.Design":
        module_tokens = []
        module_inside = False
        modules: List[ichier.Module] = []
        for token in self:
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


class ModuleHeadParser(BaseLexer):
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

    def parse(self) -> Tuple[str, List[str]]:
        name = None
        ports = []
        for t in self:
            if t.type == "MODULE_NAME":
                if name is None:
                    name = t.value
            elif t.type == "PORT_NAMES":
                ports += t.value
        if name is None:
            raise ValueError("Invalid module name")
        return name, ports


class NetsSplitParser(BaseLexer):
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
        r"(\w+|\\\S+)(\s*,\s*(\w+|\\\S+))*\s*;"
        t.value = re.sub(r",|;", " ", t.value).split()
        return t

    def parse(self) -> List[str]:
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


class InstanceParser(BaseLexer):
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

    __cnp = r"(\w+(\[\s*\d+(\s*\:\s*\d+)?\s*\])?|\\\S+)"  # connection net pattern
    __ccnp = rf"{{?\s*{__cnp}(\s*,\s*{__cnp})*\s*}}?"  # combo connection net pattern
    __cbnp = rf"\.(\w+)\s*\(\s*({__ccnp})\s*\)"  # connection by name pattern

    @TOKEN(r"(?<!\#)" rf"\(\s*{__cbnp}(\s*,\s*{__cbnp})*\s*\)\s*;")
    def t_CONNECTION_INFO_BY_NAME(self, t: LexToken):
        connect: Dict[str, Union[str, List[str]]] = {}
        for m in re.finditer(self.__cbnp, t.value[:-1].rstrip()[1:-1]):
            connect[m.group(1)] = m.group(2).strip()
            # connect[m.group(1)] = NameParser().parse(m.group(2).strip())
        t.value = connect
        return t

    __ccnp_cnp = rf"({__ccnp}|{__cnp})"  # combo or no

    @TOKEN(r"(?<!\#)" rf"\(\s*{__ccnp_cnp}(\s*,\s*{__ccnp_cnp})*\s*\)\s*;")
    def t_CONNECTION_INFO_BY_ORDER(self, t: LexToken):
        nets = []
        for m in re.finditer(self.__ccnp_cnp, t.value[:-1].rstrip()[1:-1]):
            nets.append(m.group(1).strip())
            # nets.append(NameParser().parse(m.group(1).strip()))
        t.value = nets
        return t

    def parse(self) -> "ichier.Instance":
        td = tokensToDict(self)
        words = td.get("WORD", [])
        if len(words) != 2:
            raise ValueError("Invalid instance definition")

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


def fromFile(file: Union[str, Path], *, name: Optional[str] = None) -> "ichier.Design":
    file = str(file)
    with open(file, "r") as f:
        text = f.read()
    design = fromString(text)
    design.name = file if name is None else str(name)
    return design


def fromString(string: str) -> "ichier.Design":
    return VerilogParser(string).parse()


def _moduleAnalyser(tokens: Iterable[LexToken]) -> "ichier.Module":
    td = tokensToDict(tokens)

    # module head
    module_head = td.get("MODULE_HEAD")
    if module_head is None:
        raise ValueError("Invalid module head")
    module_name, module_ports = ModuleHeadParser(module_head[0].value).parse()

    # terminals
    terminals: List[ichier.Terminal] = []
    if module_ports:
        port_dir: Dict[str, Optional[str]] = {}
        for p in module_ports:
            port_dir[p] = None

        # input, output, inout
        full_ports = []
        for dir, token in {
            "in": "INPUT",
            "out": "OUTPUT",
            "inout": "INOUT",
        }.items():
            for t in td.get(token, []):
                for p in NetsSplitParser(re.sub(r"^\w+\s*", "", t.value)).parse():
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
    # nets: List[ichier.Net] = []
    # for t in td.get("WIRE", []):
    #     for n in NetsSplitParser(re.sub(r"^\w+\s*", "", t.value)).parse():
    #         nets.append(ichier.Net(name=n))

    return ichier.Module(
        name=module_name,
        terminals=terminals,
        # nets=nets,
        instances=[InstanceParser(t.value).parse() for t in td.get("INSTANCE", [])],
    )
