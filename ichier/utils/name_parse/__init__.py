from typing import List


from .parser import Parser

__all__ = [
    "parse",
]

_Parser = Parser()


def parse(name: str) -> List[str]:
    return _Parser.parse(name)
