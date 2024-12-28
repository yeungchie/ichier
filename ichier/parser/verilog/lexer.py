from pathlib import Path
from typing import Optional, Tuple, Union
from icutk.lex import BaseLexer, LexToken
from ichier.utils.escape import EscapeString

__all__ = [
    "VerilogLexer",
]


class VerilogLexer(BaseLexer):
    reserved = {
        "module": "MODULE",
        "input": "INPUT",
        "output": "OUTPUT",
        "inout": "INOUT",
        "wire": "WIRE",
        "specify": "SPECIFY",
        "specparam": "SPECPARAM",
        "endspecify": "ENDSPECIFY",
        "endmodule": "ENDMODULE",
    }

    tokens = [
        "ESC_ID",  # \abc
        "STRING",  # "abc"
        *BaseLexer.tokens,
        *reserved.values(),
    ]

    def __init__(
        self,
        *args,
        priority: Tuple[int, ...] = (),
        path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lexer.priority = priority
        self.lexer.path = path

    def t_ESC_ID(self, t: LexToken):
        r"\\\S+"
        t.value = EscapeString(t.value)
        return t

    def t_ID(self, t: LexToken):
        r"[a-zA-Z_]\w*"
        t.type = self.reserved.get(t.value, t.type)
        return t

    def t_FLOAT(self, t: LexToken):
        r"\d+\.\d+"
        t.value = float(t.value)
        return t

    def t_INT(self, t: LexToken):
        r"\d+"
        t.value = int(t.value)
        return t

    def t_STRING(self, t: LexToken):
        r'"[^"]*"'
        t.value = t.value[1:-1]
        return t

    def t_pre_proc(self, t: LexToken):
        r"`\w.*"
        pass

    def t_comment_line(self, t: LexToken):
        r"//.*"
        pass

    def t_comment_block(self, t: LexToken):
        r"/\*([^*]|\*(?!/))*\*/"
        t.lexer.lineno += t.value.count("\n")
        pass

    def t_compile_block(self, t: LexToken):
        r"\(\*([^*]|\*(?!\)))*\*\)"
        t.lexer.lineno += t.value.count("\n")
        pass
