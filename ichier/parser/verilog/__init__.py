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
    try:
        if isinstance(item, CodeItem):
            design = item.load(path=path, msg_queue=msg_queue)
        elif isinstance(item, FileItem):
            path = item.path
            design = item.load(msg_queue=msg_queue)
    except Exception as err:
        if path is None:
            raise err
        raise type(err)(f"{path}, {err}")
    return design


class PreProc:
    @staticmethod
    def process(code: str) -> str:
        return PreProc.removeAloneWires(PreProc.removeComments(code))

    @staticmethod
    def preserveLineFeed(m: re.Match) -> str:
        return "\n" * m.group().count("\n")

    @staticmethod
    def removeComments(code: str) -> str:
        return re.sub(
            r"/\*.*?\*/",
            PreProc.preserveLineFeed,
            code,
            flags=re.DOTALL,
        )

    @staticmethod
    def removeAloneWires(code: str) -> str:
        return re.sub(
            r"wire\s+[^[\s].+?;",
            PreProc.preserveLineFeed,
            code,
            flags=re.DOTALL,
        )


def parseInclude(
    code: str,
    *,
    queue: Optional[list] = None,
    priority: tuple = (),
    preprocessed: bool = False,
) -> List[Union[CodeItem, FileItem]]:
    if queue is None:
        queue = []
    if priority is None:
        priority = ()
    if not preprocessed:
        code = PreProc.process(code)
    if not priority:
        queue.append(
            CodeItem(
                priority=priority,
                code=code,
                removed_comments=True,
                removed_alone_wires=True,
            )
        )
    for i, line in enumerate(code.splitlines()):
        if m := re.match(r'`include "([^"\s]+)"', line):
            file_priority = priority + (i + 1,)
            path = Path(os.path.expandvars(m.group(1))).expanduser()
            code = PreProc.process(path.read_text(encoding="utf-8"))
            queue.append(FileItem(priority=file_priority, path=path, code=code))
            parseInclude(
                code=code,
                queue=queue,
                priority=file_priority,
                preprocessed=True,
            )
    return queue


@dataclass
class CodeItem:
    priority: tuple
    code: str = field(repr=False, default_factory=str)
    removed_comments: bool = False
    removed_alone_wires: bool = False

    def __post_init__(self):
        if self.code != "":
            if not self.removed_comments:
                self.code = PreProc.removeComments(self.code)
            if not self.removed_alone_wires:
                self.code = PreProc.removeAloneWires(self.code)

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
    code: str = field(repr=False, default_factory=str)
    removed_comments: bool = False
    removed_alone_wires: bool = False

    def __post_init__(self):
        if self.code == "":
            self.code = self.path.read_text(encoding="utf-8")
        if self.code != "":
            if not self.removed_comments:
                self.code = PreProc.removeComments(self.code)
            if not self.removed_alone_wires:
                self.code = PreProc.removeAloneWires(self.code)

    def load(
        self,
        msg_queue: Optional[Queue] = None,
    ) -> Design:
        path = Path(self.path)
        return CodeItem(
            priority=self.priority,
            code=self.code,
            removed_comments=self.removed_comments,
            removed_alone_wires=self.removed_alone_wires,
        ).load(path=path, msg_queue=msg_queue)
