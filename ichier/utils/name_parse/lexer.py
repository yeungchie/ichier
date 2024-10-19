from ply.lex import lex


class Lexer:
    tokens = (
        "ID",
        "INT",
        "LBRACKET",  # [
        "RBRACKET",  # ]
        "LANGLE",  # <
        "RANGLE",  # >
        "LBRACE",  # {
        "RBRACE",  # }
        "COMMA",  # ,
        "COLON",  # :
    )

    t_ID = r"[a-zA-Z_]\w*|\\\S+"
    t_LBRACKET = r"\["
    t_RBRACKET = r"\]"
    t_LANGLE = r"<"
    t_RANGLE = r">"
    t_LBRACE = r"\{"
    t_RBRACE = r"\}"
    t_COMMA = r","
    t_COLON = r":"

    def t_INT(self, t):
        r"\d+"
        t.value = int(t.value)
        return t

    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        t.lexer.skip(1)

    t_ignore = " \t"

    def build(self):
        self.lexer = lex(module=self, debug=False)

    def __init__(self):
        self.build()

    def input(self, data):
        self.lexer.input(data)

    def token(self):
        return self.lexer.token()
