from ply.yacc import yacc

from .lexer import Lexer


class Parser:
    def p_output(self, p):
        """
        output : name
               | group
        """
        p[0] = p[1]

    def p_name(self, p):
        """
        name : bit_name
             | bus_name
             | ID
        """
        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]]

    def p_names(self, p):
        """
        names : names COMMA name
              | name
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[1] + p[3]

    def p_group(self, p):
        """
        group : LBRACE names RBRACE
              | LBRACE names COMMA RBRACE
        """
        p[0] = p[2]

    def p_bit(self, p):
        """
        bit : LBRACKET INT RBRACKET
            | LANGLE INT RANGLE
        """
        p[0] = f"{p[1]}{p[2]}{p[3]}"

    def p_bit_name(self, p):
        """
        bit_name : ID bit
        """
        p[0] = f"{p[1]}{p[2]}"

    def p_bus(self, p):
        """
        bus : LBRACKET INT COLON INT RBRACKET
            | LANGLE INT COLON INT RANGLE
        """
        start = p[2]
        end = p[4]
        reversep = False
        if start > end:
            start, end = end, start
            reversep = True
        bits = [f"{p[1]}{i}{p[5]}" for i in range(start, end + 1)]
        if reversep:
            bits.reverse()
        p[0] = bits

    def p_bus_name(self, p):
        """
        bus_name : ID bus
        """
        p[0] = [f"{p[1]}{bit}" for bit in p[2]]

    def p_error(self, t):
        if t:
            raise SyntaxError(f"Syntax error at {t.value!r}")
        else:
            raise SyntaxError("Syntax error at EOF")

    def __init__(self):
        self.lexer = Lexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc(module=self, debug=False)

    def parse(self, text):
        return self.parser.parse(text, lexer=self.lexer)
