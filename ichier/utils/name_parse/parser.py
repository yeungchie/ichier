from ply.yacc import yacc

from .lexer import Lexer


class NameGroup(tuple):
    pass


class Parser:
    def p_start(self, p):
        """
        start  :  names
               |  names  ','
        """
        if isinstance(p[1], tuple) and len(p[1]) == 1:
            p[0] = p[1][0]
        else:
            p[0] = p[1]

    def p_names(self, p):  # A, B[1], C[1:0], {D[2:0]}
        """
        names  :  names  ','  name
               |  name
        """
        if len(p) == 4:
            if isinstance(p[3], NameGroup):
                p[0] = p[1] + (p[3],)
            elif isinstance(p[3], tuple):
                p[0] = p[1] + p[3]
            else:
                p[0] = p[1] + (p[3],)
        else:
            if isinstance(p[1], NameGroup):
                p[0] = (p[1],)
            elif isinstance(p[1], tuple):
                p[0] = p[1]
            else:
                p[0] = (p[1],)

    def p_name(self, p):
        """
        name  :  bit_name
              |  bus_name
              |  ID
              |  ESC_ID
              |  group
        """
        p[0] = p[1]

    def p_group(self, p):  # {A, B[1], C[1:0]}
        """
        group  :  '{'  names  '}'
               |  '{'  names  ','  '}'
        """
        p[0] = NameGroup(p[2])

    def p_bit_name(self, p):  # A[1]
        """
        bit_name  :  ID  bit
                  |  bit  ID
        """
        id, bit = p[1], p[2]
        if ("<" in id) or ("[" in id):
            bit, id = id, bit
        p[0] = id + bit

    def p_bit(self, p):  # [1]
        """
        bit  :  '['  INT  ']'
             |  '<'  INT  '>'
        """
        p[0] = f"{p[1]}{p[2]}{p[3]}"

    def p_bus_name(self, p):  # A[1:0]
        """
        bus_name  :  ID  bus
                  |  bus  ID
        """
        id, bus = p[1], p[2]
        if isinstance(p[2], str):
            bus, id = id, bus
        p[0] = tuple(id + bit for bit in bus)

    def p_bus(self, p):  # [1:0]
        """
        bus  :  '['  INT  ':'  INT  ']'
             |  '<'  INT  ':'  INT  '>'
        """
        start, end = p[2], p[4]
        if start <= end:
            step = 1
        else:
            step = -1
        p[0] = tuple(f"{p[1]}{i}{p[5]}" for i in range(start, end + step, step))

    def p_error(self, t):
        if t:
            raise SyntaxError(f"Syntax error at {t.value!r}")
        else:
            raise SyntaxError("Syntax error at EOF")

    def __init__(self):
        self.lexer = Lexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc(module=self, debug=False, write_tables=False)

    def parse(self, text):
        return self.parser.parse(text, lexer=self.lexer)
