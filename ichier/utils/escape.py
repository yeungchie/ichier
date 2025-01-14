from typing import Union
import re


def needEscape(s: str) -> bool:
    if " " in s:
        raise ValueError(f"Space is not allowed in the string - {s!r}")
    if s.startswith("\\"):
        return True  # \abc
    if s.isidentifier():
        return False  # abc
    if re.fullmatch(r"[a-zA-Z_]\w*(\[\d+\]|<\d+>)?", s):
        return False  # abc[1]
    return True


class EscapeString(str):
    def __new__(cls, value):
        if isinstance(value, EscapeString):
            return super().__new__(cls, value)
        s = str(value)
        if not needEscape(s):
            raise ValueError(f"String is not need to be escaped - {value!r}")
        if not s.startswith("\\"):
            s = "\\" + s
        return super().__new__(cls, s)

    def __repr__(self):
        return f"EscapeString({super().__repr__()})"

    def __str__(self):
        return f"{super().__str__()}"


def makeSafeString(s: str) -> Union[str, EscapeString]:
    if isinstance(s, EscapeString):
        return s
    try:
        return EscapeString(s)
    except ValueError:
        return s
