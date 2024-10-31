from icutk.lex import MetaLexer, LexToken
from ichier.utils.escape import EscapeString

__all__ = [
    "VerilogLexer",
]


class VerilogLexer(MetaLexer):
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
        "`include": "INCLUDE",
    }

    tokens = (
        "ID",  # abc
        "ESC_ID",  # \abc
        "FLOAT",  # 1.23
        "INT",  # 10
        "STRING",  # "abc"
    ) + tuple(reserved.values())

    literals = "()[]{}=;,:."

    def t_ESC_ID(self, t: LexToken):
        r"\\\S+"
        t.value = EscapeString(t.value[1:])
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
        proc, _, value = t.value.partition(" ")
        t_type = self.reserved.get(proc)
        if t_type is None:
            return
        t.type = t_type
        if t.type == "INCLUDE":
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                t.value = value[1:-1]
            else:
                raise ValueError(f"Invalid include value: {t.value!r}")
        else:
            return
        return t

    def t_newline(self, t: LexToken):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")
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
