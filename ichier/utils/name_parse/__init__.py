from typing import List

from .parser import Parser

__all__ = [
    "parse",
]

__parser = None


def parse(name: str) -> List[str]:
    global __parser
    if not isinstance(__parser, Parser):
        __parser = Parser()
    return __parser.parse(name)
