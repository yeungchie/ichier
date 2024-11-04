from typing import Union
from pathlib import Path

from ichier import Design
from .parser import VerilogParser

__all__ = []

PARSER = VerilogParser()


def fromFile(file: Union[str, Path]) -> Design:
    path = Path(file)
    with open(path, "rt", encoding="utf-8") as f:
        design = fromString(f.read())
    design.name = path.name
    design.path = path
    return design


def fromString(string: str) -> Design:
    return PARSER.parse(string)
