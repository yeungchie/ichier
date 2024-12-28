from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Union
from pathlib import Path
import re

from ichier import Design
from .parser import VerilogParser

__all__ = []


def fromFile(
    file: Union[str, Path],
    *,
    rebuild: bool = False,
    cb_input: Optional[Callable] = None,
    cb_token: Optional[Callable] = None,
) -> Design:
    path = Path(file)
    with open(path, "rt", encoding="utf-8") as f:
        design = fromString(
            f.read(),
            rebuild=rebuild,
            cb_input=cb_input,
            cb_token=cb_token,
            path=path,
        )
    design.name = path.name
    design.path = path
    for m in design.modules:
        if m.path is None:
            m.path = path
    return design


def fromString(
    string: str,
    *,
    rebuild: bool = False,
    cb_input: Optional[Callable] = None,
    cb_token: Optional[Callable] = None,
    path: Optional[Union[str, Path]] = None,
) -> Design:
    queue = []
    designs = []
    for item in parseHier(string, queue=queue):
        if isinstance(item, NetlistString):
            d = __fromString(
                item.string,
                rebuild=False,
                cb_input=cb_input,
                cb_token=cb_token,
                path=path,
            )
        elif isinstance(item, NetlistFile):
            d = __fromFile(
                item.path,
                rebuild=False,
                cb_input=cb_input,
                cb_token=cb_token,
                priority=item.priority,
            )
            d.priority = item.priority
        designs.append(d)
    design = Design()
    for d in designs:
        design.includeOtherDesign(d)
    if rebuild:
        design.modules.rebuild(verilog_style=True)
    return design


def __fromFile(
    file: Union[str, Path],
    *,
    rebuild: bool = False,
    cb_input: Optional[Callable] = None,
    cb_token: Optional[Callable] = None,
    priority: Tuple[int, ...] = (),
) -> Design:
    path = Path(file)
    with open(path, "rt", encoding="utf-8") as f:
        design = __fromString(
            string=f.read(),
            rebuild=rebuild,
            cb_input=cb_input,
            cb_token=cb_token,
            priority=priority,
            path=path,
        )
    design.name = path.name
    design.path = path
    return design


def __fromString(
    string: str,
    *,
    rebuild: bool = False,
    cb_input: Optional[Callable] = None,
    cb_token: Optional[Callable] = None,
    priority: Tuple[int, ...] = (),
    path: Optional[Union[str, Path]] = None,
) -> Design:
    vparser = VerilogParser(
        cb_input=cb_input,
        cb_token=cb_token,
        priority=priority,
        path=path,
    )
    design = vparser.parse(string)
    if rebuild:
        for m in design.modules:
            m.rebuild(verilog_style=True)
    return design


def removeComments(string: str) -> str:
    return re.sub(
        r"/\*.*?\*/",
        lambda m: "\n" * m.group().count("\n"),
        string,
        flags=re.DOTALL,
    )


def parseHier(
    string: str,
    *,
    queue: Optional[list] = None,
    priority: tuple = (),
):
    if queue is None:
        queue = []
    if priority is None:
        priority = ()
    if not priority:
        queue.append(NetlistString(string=string))
    for i, line in enumerate(removeComments(string).splitlines()):
        if m := re.fullmatch(r'`include "([^"\s]+)"', line):
            file_priority = priority + (i + 1,)
            path = Path(m.group(1))
            queue.append(
                NetlistFile(
                    priority=file_priority,
                    path=path,
                )
            )
            parseHier(
                string=path.read_text(encoding="utf-8"),
                queue=queue,
                priority=file_priority,
            )
    return queue


@dataclass
class NetlistString:
    string: str = field(default_factory=str, repr=False)


@dataclass
class NetlistFile:
    priority: tuple
    path: Path
