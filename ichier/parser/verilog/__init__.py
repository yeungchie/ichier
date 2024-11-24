from typing import Union
from pathlib import Path

from ichier import Design
from .parser import VerilogParser

__all__ = []


def fromFile(file: Union[str, Path], *, rebuild: bool = False) -> Design:
    path = Path(file)
    with open(path, "rt", encoding="utf-8") as f:
        design = fromString(f.read(), rebuild=rebuild)
    design.name = path.name
    design.path = path
    return design


def fromString(string: str, *, rebuild: bool = False) -> Design:
    vparser = VerilogParser()
    design = vparser.parse(string)
    if rebuild:
        for m in design.modules:
            m.rebuild(verilog_style=True)
    return design
