from typing import List, Sequence, Tuple, Optional
import re

from .parser import Parser
from ..escape import EscapeString

__all__ = [
    "parse",
    "merge",
    "bitInfoSplit",
]


def parse(name: str) -> List[str]:
    return Parser().parse(name)


def merge(names: Sequence[str]) -> str: ...


def bitInfoSplit(name: str) -> Tuple[str, Optional[int]]:
    if isinstance(name, EscapeString):
        return name, None
    if m := re.fullmatch(r"(?P<head>[a-zA-Z_]\W*)\[(?P<index>\d+)\]", name):
        return m.group("head"), int(m.group("index"))
    elif m := re.fullmatch(r"(?P<head>[a-zA-Z_]\W*)<(?P<index>\d+)>", name):
        return m.group("head"), int(m.group("index"))
    else:
        return name, None
