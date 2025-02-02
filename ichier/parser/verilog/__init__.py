from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union
from pathlib import Path
from multiprocessing import Pool
from queue import Queue
import re
import os

from ichier import Design
from .parser import VerilogParser

__all__ = []


def fromFile(
    file: Union[str, Path],
    *,
    rebuild: bool = False,
    msg_queue: Optional[Queue] = None,
) -> Design:
    path = Path(file)
    return fromCode(
        path.read_text(encoding="utf-8"),
        rebuild=rebuild,
        path=path,
        msg_queue=msg_queue,
    )


def fromCode(
    code: str,
    *,
    rebuild: bool = False,
    path: Optional[Union[str, Path]] = None,
    msg_queue: Optional[Queue] = None,
) -> Design:
    args_array = []
    for item in parseInclude(code):
        if isinstance(item, CodeItem):
            args_array.append((item, path, msg_queue))
        elif isinstance(item, FileItem):
            args_array.append((item, None, msg_queue))

    design = Design()
    # designs = [worker(*args) for args in args_array]
    with Pool() as pool:
        designs = pool.starmap(worker, args_array)
    for d in designs:
        design.includeOtherDesign(d)

    if rebuild:
        design.modules.rebuild(verilog_style=True)
    if path is not None:
        path = Path(path)
        design.path = path
        design.name = path.name
        for m in design.modules:
            if m.path is None:
                m.path = path
    return design


def worker(
    item: Union[CodeItem, FileItem],
    path: Optional[Union[str, Path]] = None,
    msg_queue: Optional[Queue] = None,
) -> Design:
    if isinstance(item, CodeItem):
        design = item.load(path=path, msg_queue=msg_queue)
    elif isinstance(item, FileItem):
        design = item.load(msg_queue=msg_queue)
    return design


def removeComments(code: str) -> str:
    return re.sub(
        r"/\*.*?\*/",
        lambda m: "\n" * m.group().count("\n"),
        code,
        flags=re.DOTALL,
    )


def parseInclude(
    code: str,
    *,
    queue: Optional[list] = None,
    priority: tuple = (),
) -> List[Union[CodeItem, FileItem]]:
    if queue is None:
        queue = []
    if priority is None:
        priority = ()
    if not priority:
        queue.append(CodeItem(priority=priority, code=code))
    for i, line in enumerate(removeComments(code).splitlines()):
        if m := re.match(r'`include "([^"\s]+)"', line):
            file_priority = priority + (i + 1,)
            path = Path(os.path.expandvars(m.group(1))).expanduser()
            queue.append(FileItem(priority=file_priority, path=path, code=""))
            parseInclude(
                code=path.read_text(encoding="utf-8"),
                queue=queue,
                priority=file_priority,
            )
    return queue


@dataclass
class CodeItem:
    priority: tuple
    code: str = field(repr=False)

    def load(
        self,
        path: Optional[Union[str, Path]] = None,
        msg_queue: Optional[Queue] = None,
    ) -> Design:
        vparser = VerilogParser(
            priority=self.priority,
            path=path,
            msg_queue=msg_queue,
        )
        return vparser.parse(self.code)


@dataclass
class FileItem:
    priority: tuple
    path: Path
    code: str = field(repr=False)

    def load(
        self,
        msg_queue: Optional[Queue] = None,
    ) -> Design:
        path = Path(self.path)
        return CodeItem(
            priority=self.priority,
            code=path.read_text(encoding="utf-8"),
        ).load(path=path, msg_queue=msg_queue)
