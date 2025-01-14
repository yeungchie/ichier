from __future__ import annotations
from queue import Queue
from pathlib import Path
from typing import Optional, Tuple, Union
from uuid import uuid4
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
        data: Optional[str] = None,
        *,
        path: Optional[Union[str, Path]] = None,
        priority: Tuple[int, ...] = (),
        msg_queue: Optional[Queue] = None,
    ) -> None:
        if path is None:
            self.path = None
        else:
            self.path = Path(path)
        self.priority = priority
        self.msg_queue = msg_queue

        self.id: str = uuid4().hex
        self.total_lines: int = 0
        self.last_percent: int = 0

        super().__init__()
        if data is not None:
            self.input(data)

    def input(self, *args, **kwargs) -> None:
        super().input(*args, **kwargs)
        if self.lexer.lexdata is None:
            self.total_lines = 0
        else:
            self.total_lines = self.lexer.lexdata.count("\n")
        self.cb_input()

    def cb_input(self) -> None:
        if self.msg_queue is None:
            return
        if self.path is None:
            path_name = "Verilog"
        else:
            path_name = self.path.name
        description = f"{'  '*len(self.priority)}{path_name}"
        self.msg_queue.put(dict(id=self.id, type="init", value=description))
        self.msg_queue.put(dict(id=self.id, type="total", value=self.total_lines))

    def token(self) -> Optional[LexToken]:
        t = super().token()
        if t is None:
            return None
        self.cb_token()
        return t

    def cb_token(self) -> None:
        pass

    def line_count(self, s: str) -> None:
        super().line_count(s)
        self.cb_newline()

    def cb_newline(self) -> None:
        if self.msg_queue is None:
            return
        percent = int(self.lexer.lineno / self.total_lines * 100)
        if percent > self.last_percent:
            self.msg_queue.put(
                dict(id=self.id, type="current", value=self.lexer.lineno)
            )
            self.last_percent = percent

    def cb_done(self) -> None:
        if self.msg_queue is None:
            return
        self.msg_queue.put(dict(id=self.id, type="done"))

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
        self.line_count(t.value)
        pass

    def t_compile_block(self, t: LexToken):
        r"\(\*([^*]|\*(?!\)))*\*\)"
        self.line_count(t.value)
        pass
