from typing import Union
from pathlib import Path

from ichier import Design
from .parser import VerilogParser

__all__ = [
    "fromFile",
    "fromString",
]

PARSER = VerilogParser()


def fromFile(file: Union[str, Path]) -> Design:
    with open(file, "rt", encoding="utf-8") as f:
        design = fromString(f.read())
    design.name = str(file)
    return design


def fromString(string: str) -> Design:
    return PARSER.parse(string)