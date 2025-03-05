import re
from typing import Optional
from icutk.lex import lex, MetaLexer, LexToken
from ply.yacc import yacc
from ...node import Instance, DesignateReference


class InstLexer(MetaLexer):
    tokens = [
        "ASSIGN",
        "TASSIGN",
        "PINS",
        "DESIGNATE",
        "C",  # cap
        "D",  # diode
        "L",  # inductor
        "M",  # mosfet
        "Q",  # bjt
        "R",  # resistor
        "X",  # subcircuit
        "ID",
    ]

    literals = "/"

    def __init__(self, text: Optional[str] = None) -> None:
        self.lexer = lex(module=self, debug=False, reflags=re.IGNORECASE)
        if text is not None:
            self.input(text)

    def t_ASSIGN(self, t: LexToken):
        r"\S+?=\S+"
        arg, value = t.value.split("=")
        t.value = (arg, value)
        if arg.upper() == "$T":
            t.type = "TASSIGN"
        return t

    def t_PINS(self, t: LexToken):
        r"\$PINS"
        return t

    def t_DESIGNATE(self, t: LexToken):
        r"\$\[\S+\]"
        t.value = DesignateReference(t.value[2:-1])
        return t

    def t_C(self, t: LexToken):
        r"C\S+"
        return t

    def t_D(self, t: LexToken):
        r"D\S+"
        return t

    def t_L(self, t: LexToken):
        r"L\S+"
        return t

    def t_M(self, t: LexToken):
        r"M\S+"
        return t

    def t_Q(self, t: LexToken):
        r"Q\S+"
        return t

    def t_R(self, t: LexToken):
        r"R\S+"
        return t

    def t_X(self, t: LexToken):
        r"X\S+"
        return t

    def t_ID(self, t: LexToken):
        r"\S+"
        if t.value == "/":
            t.type = "/"
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
        inst  :  inst_subckt1
              |  inst_subckt2
              |  inst_subckt3
              |  inst_subckt4
              |  inst_2t
              |  inst_2td
              |  inst_3t
              |  inst_3td
              |  inst_4t
              |  inst_4td
        """
        p[0] = p[1]

    def p_inst_subckt1(self, p):
        """
        inst_subckt1  :  X  words  assigns
                      |  X  words
        """
        # X0 net1 net2 net3 net4 nch m=1 length=4u width=10u
        # X0 net1 net2 net3 net4 nch
        name = p[1]
        ref = p[2].pop(-1)
        conn = p[2]
        if len(p) == 4:
            params = p[3]
        else:
            params = None
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            prefix="X",
        )

    def p_inst_subckt2(self, p):
        """
        inst_subckt2  :  X  words  "/"  word  assigns
                      |  X  words  "/"  word
        """
        # X0 net1 net2 net3 net4 / nch m=1 length=4u width=10u
        # X0 net1 net2 net3 net4 / nch
        name = p[1]
        conn = p[2]
        ref = p[4]
        if len(p) == 6:
            params = p[5]
        else:
            params = None
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            prefix="X",
        )

    def p_inst_subckt3(self, p):
        """
        inst_subckt3  :  X  word  assigns  PINS  assigns
                      |  X  word  PINS  assigns
                      |  X  word  PINS
        """
        # X0 nch m=1 length=4u width=10u $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4
        # X0 nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4
        # X0 nch $PINS
        name = p[1]
        if len(p) == 6:
            ref = p[2]
            conn = p[5]
            params = p[3]
        elif len(p) == 5:
            ref = p[2]
            conn = p[4]
            params = None
        else:
            ref = p[2]
            conn = None
            params = None
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            prefix="X",
        )

    def p_inst_subckt4(self, p):
        """
        inst_subckt4  :  X  "/"  word  assigns  PINS  assigns
                      |  X  "/"  word  PINS  assigns
                      |  X  "/"  word  PINS
                      |  X  "/"  word
        """
        # X0 / nch m=1 length=4u width=10u $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4
        # X0 / nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4
        # X0 / nch $PINS
        # X0 / nch
        name = p[1]
        if len(p) == 7:
            ref = p[3]
            conn = p[6]
            params = p[4]
        elif len(p) == 6:
            ref = p[3]
            conn = p[5]
            params = None
        else:
            ref = p[3]
            conn = None
            params = None
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            prefix="X",
        )

    def p_inst_2t(self, p):
        """
        inst_2t  :  dev_2t  words
                 |  dev_2t  words  assigns
        """
        # R0 net1 net2 pdk_res 1.2K length=10u width=1u
        name = p[1]
        conn = p[2][:2]
        ref = p[2][2]
        oparams = p[2][3:]
        if len(p) == 3:
            params = None
        else:
            params = p[3]
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            orderparams=oparams,
            prefix=name[0],
        )

    def p_inst_2td(self, p):
        """
        inst_2td  :  dev_2t  words  DESIGNATE
                  |  dev_2t  words  DESIGNATE  assigns
                  |  dev_2t  words  assigns  DESIGNATE  assigns
        """
        # R0 net1 net2 1.2K $[pdk_res] length=10u width=1u
        name = p[1]
        conn = p[2][:2]
        oparams = p[2][2:]
        if len(p) == 4:
            ref = p[3]
            params = None
        elif len(p) == 5:
            ref = p[3]
            params = p[4]
        else:
            ref = p[4]
            params = {**p[3], **p[5]}
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            orderparams=oparams,
            prefix=name[0],
        )

    def p_inst_3t(self, p):
        """
        inst_3t  :  dev_3t  words
                 |  dev_3t  words  assigns
        """
        # Q0 net1 net2 net3 pdk_pnp 25 length=5u width=5u
        name = p[1]
        conn = p[2][:3]
        ref = p[2][3]
        oparams = p[2][4:]
        if len(p) == 3:
            params = None
        else:
            params = p[3]
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            orderparams=oparams,
            prefix=name[0],
        )

    def p_inst_3td(self, p):
        """
        inst_3td  :  dev_3t  words  DESIGNATE
                  |  dev_3t  words  DESIGNATE  assigns
                  |  dev_3t  words  assigns  DESIGNATE  assigns
        """
        # Q0 net1 net2 net3 25 $[pdk_pnp] length=5u width=5u
        name = p[1]
        conn = p[2][:3]
        oparams = p[2][3:]
        if len(p) == 4:
            ref = p[3]
            params = None
        elif len(p) == 5:
            ref = p[3]
            params = p[4]
        else:
            ref = p[4]
            params = {**p[3], **p[5]}
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            orderparams=oparams,
            prefix=name[0],
        )

    def p_inst_4t(self, p):
        """
        inst_4t  :  dev_4t  words
                 |  dev_4t  words  assigns
        """
        # M0 net1 net2 net3 net4 pdk_mos length=1u width=2u
        name = p[1]
        conn = p[2][:4]
        ref = p[2][4]
        oparams = p[2][5:]
        if len(p) == 3:
            params = None
        else:
            params = p[3]
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            orderparams=oparams,
            prefix=name[0],
        )

    def p_inst_4td(self, p):
        """
        inst_4td  :  dev_4t  words  DESIGNATE
                  |  dev_4t  words  DESIGNATE  assigns
                  |  dev_4t  words  assigns  DESIGNATE  assigns
        """
        # M0 net1 net2 net3 net4 $[pdk_mos] length=1u width=2u
        name = p[1]
        conn = p[2][:4]
        oparams = p[2][4:]
        if len(p) == 4:
            ref = p[3]
            params = None
        elif len(p) == 5:
            ref = p[3]
            params = p[4]
        else:
            ref = p[4]
            params = {**p[3], **p[5]}
        p[0] = Instance(
            reference=ref,
            name=name,
            connection=conn,
            parameters=params,
            orderparams=oparams,
            prefix=name[0],
        )

    def p_dev_2t(self, p):
        """
        dev_2t  :  C
                |  D
                |  L
                |  R
        """
        p[0] = p[1]

    def p_dev_3t(self, p):
        """
        dev_3t  :  Q
        """
        p[0] = p[1]

    def p_dev_4t(self, p):
        """
        dev_4t  :  M
        """
        p[0] = p[1]

    def p_word(self, p):
        """
        word  :  ID
              |  X
              |  dev_2t
              |  dev_3t
              |  dev_4t
        """
        p[0] = p[1]

    def p_words(self, p):
        """
        words  :  words  word
               |  word
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
        tassign_pair  :  TASSIGN  word  word  word
        """
        # $T=0 0 0 0
        k, v = p[1]
        p[0] = {k: " ".join([v] + p[2:])}


def parse(text: str) -> Instance:
    return InstParser().parse(text)
