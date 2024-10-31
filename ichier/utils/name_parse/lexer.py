from icutk.lex import MetaLexer, LexToken
from ichier.utils.escape import EscapeString


class Lexer(MetaLexer):
    tokens = (
        "ID",
        "ESC_ID",
        "INT",
    )
    literals = "[]<>{},:"

    t_ID = r"[a-zA-Z_]\w*|\\\S+"

    def t_ESC_ID(self, t: LexToken):
        r"\\\S+"
        t.value = EscapeString(t.value)
        return t

    def t_INT(self, t: LexToken):
        r"\d+"
        t.value = int(t.value)
        return t

    def t_newline(self, t: LexToken):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")
