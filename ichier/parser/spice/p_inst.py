from typing import Optional
from icutk.lex import MetaLexer, LexToken
from ply.yacc import yacc
from ...node import Instance, DesignateReference


class InstLexer(MetaLexer):
    tokens = ["WORD", "PINS", "ASSIGN", "TASSIGN", "DESIGNATE"]

    literals = "/"

    def __init__(self, text: Optional[str] = None) -> None:
        super().__init__()
        if text is not None:
            self.input(text)

    def t_WORD(self, t: LexToken):
        r"[^\s/]+"
        if t.value.upper() == "$PINS":
            t.type = "PINS"
        elif "=" in t.value:
            arg, _, value = t.value.partition("=")
            if arg.upper() == "$T":
                t.type = "TASSIGN"
            else:
                t.type = "ASSIGN"
            t.value = (arg, value)
        elif t.value.startswith("$[") and t.value.endswith("]"):
            t.type = "DESIGNATE"
            t.value = t.value[2:-1]
        return t


class InstParser:
    def __init__(self, *args, **kwargs):
        self.lexer = InstLexer(*args, **kwargs)
        self.tokens = self.lexer.tokens
        self.parser = yacc(module=self, debug=False, write_tables=False)

    def parse(self, text: str) -> Instance:
        return self.parser.parse(text, lexer=self.lexer)

    def p_error(self, t):
        if t is None:
            raise SyntaxError("Syntax error at EOF")
        else:
            raise SyntaxError(f"Syntax error at line {t.lineno} - {t.value!r}")

    def p_inst(self, p):
        """
        inst  :  syntax1
              |  syntax2
              |  syntax3
              |  syntax4
        """
        p[0] = p[1]

    def p_syntax1(self, p):
        """
        syntax1  :  words  assigns
                 |  words
        """
        # X0 net1 net2 net3 net4 nch m=1 length=4u width=10u
        # X0 net1 net2 net3 net4 nch
        inst = p[1].pop(0)
        ref = p[1].pop(-1)
        if len(p) == 3:
            params = p[2]
        else:
            params = None
        p[0] = Instance(
            reference=ref,
            name=inst,
            connection=p[1],
            parameters=params,
        )

    def p_syntax2(self, p):
        """
        syntax2  :  words  "/"  WORD  assigns
                 |  words  "/"  WORD
        """
        # X0 net1 net2 net3 net4 / nch m=1 length=4u width=10u
        # X0 net1 net2 net3 net4 / nch
        inst = p[1].pop(0)
        ref = p[3]
        if len(p) == 5:
            params = p[4]
        else:
            params = None
        p[0] = Instance(
            reference=ref,
            name=inst,
            connection=p[1],
            parameters=params,
        )

    def p_syntax3(self, p):
        """
        syntax3  :  WORD  "/"  WORD  PINS  assigns
                 |  words  PINS  assigns
        """
        # X0 / nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4
        # X0 nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4
        if len(p) == 6:
            inst = p[1]
            ref = p[3]
            conn = p[5]
        else:
            inst = p[1][0]
            ref = p[1][-1]
            conn = p[3]
        p[0] = Instance(
            reference=ref,
            name=inst,
            connection=conn,
        )

    def p_syntax4(self, p):
        """
        syntax4  :  words  DESIGNATE  assigns
                 |  words  assigns  DESIGNATE  assigns
        """
        # R0 net1 net2 1.2 $[res] w=1 l=2
        # C0 net1 net2 1.2 $[cap] w=1 l=2
        # C0 net1 net2 1.2 w=1 l=2 $SUB=3 $[cap] $X=1 $Y=2 $D=3
        # Q0 net1 net2 net3 1.2 $[pnp] $X=1 $Y=2 $D=3
        ws = p[1]
        inst = ws.pop(0)
        if len(p) == 4:
            ref = p[2]
            params = p[3]
        else:
            ref = p[3]
            params = {**p[2], **p[4]}
        if inst[0] in ("R", "C"):
            conn = ws[:2]
            oparams = ws[2:]
        elif inst.startswith("Q"):
            conn = ws[:3]
            oparams = ws[3:]
        else:
            conn = ws
            oparams = None
        p[0] = Instance(
            reference=DesignateReference(ref),
            name=inst,
            connection=conn,
            parameters=params,
            orderparams=oparams,
        )

    def p_words(self, p):
        """
        words  :  words  WORD
               |  WORD
        """
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1]]

    def p_assigns(self, p):
        """
        assigns  :  assigns  assign_pair
                 |  assigns  tassign_pair
                 |  assign_pair
                 |  tassign_pair
        """
        if len(p) == 3:
            p[0] = {**p[1], **p[2]}
        else:
            p[0] = p[1]

    def p_assign_pair(self, p):
        """
        assign_pair  :  ASSIGN
        """
        # width=2e-06
        # length=3.5e-06
        k, v = p[1]
        p[0] = {k: v}

    def p_tassign_pair(self, p):
        """
        tassign_pair  :  TASSIGN  WORD  WORD  WORD
        """
        # $T=0 0 0 0
        k, v = p[1]
        p[0] = {k: " ".join([v] + p[2:])}


def parse(text: str) -> Instance:
    return InstParser().parse(text)
