from typing import List

from .parser import Parser

__all__ = [
    "parse",
]


def parse(name: str) -> List[str]:
    return Parser().parse(name)
