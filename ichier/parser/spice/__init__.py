from __future__ import annotations
from dataclasses import dataclass, field
from multiprocessing import Pool
from pathlib import Path
from queue import Queue
from typing import List, Optional, Union
import re
import os

from .string import LineIterator
from .parser import parse, SpiceIncludeError
import ichier


def fromFile(
    file: Union[str, Path],
    *,
    rebuild: bool = False,
    msg_queue: Optional[Queue] = None,
) -> ichier.Design:
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
    path: Optional[Path] = None,
    msg_queue: Optional[Queue] = None,
) -> ichier.Design:
    args_array = [(item, msg_queue) for item in parseInclude(file=str(path), code=code)]
    # designs = [worker(*args) for args in args_array]
    with Pool() as pool:
        designs = pool.starmap(worker, args_array)
    design = ichier.Design()
    for d in designs:
        design.includeOtherDesign(d)
    if rebuild:
        design.modules.rebuild()
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
    msg_queue: Optional[Queue] = None,
) -> ichier.Design:
    try:
        design = item.load(msg_queue=msg_queue)
    except Exception as err:
        if item.path is None:
            raise err
        raise type(err)(f"{item.path}, {err}")
    return design


def removeComments(code: str) -> str:
    lines = []
    for line in code.splitlines(keepends=True):
        if line.startswith("*"):
            lines.append("\n")
        elif line.startswith("$"):
            lines.append("\n")
        else:
            lines.append(line)
    return "".join(lines)


def parseInclude(
    *,
    file: Optional[str] = None,
    code: Optional[str] = None,
    queue: Optional[list] = None,
    _priority: tuple = (),
) -> List[Union[CodeItem, FileItem]]:
    path = None
    if file is None and code is None:
        raise ValueError("file and code cannot be None at the same time")
    elif file is not None:
        path = Path(file)
        if code is None:
            code = path.read_text(encoding="utf-8")
    elif code is not None:
        pass
    else:
        raise ValueError("file and code cannot be both None")
    if queue is None:
        queue = []
    if not _priority:
        queue.append(
            CodeItem(
                priority=_priority,
                code=code,
                path=path,
            )
        )
    for i, line in enumerate(removeComments(code).splitlines()):
        if line.upper().startswith(".INCLUDE"):
            if m := re.match(r"\.INCLUDE\s+\"?([^\"\s]*)\"?", line, re.IGNORECASE):
                file_priority = _priority + (i + 1,)
                path = Path(os.path.expandvars(m.group(1))).expanduser()
                queue.append(FileItem(priority=file_priority, path=path, code=""))
                parseInclude(
                    code=path.read_text(encoding="utf-8"),
                    queue=queue,
                    _priority=file_priority,
                )
            else:
                raise SpiceIncludeError(
                    f"Invalid include statement at line {i + 1}:\n>>> {line}"
                )
    return queue


@dataclass
class CodeItem:
    priority: tuple
    code: str = field(repr=False)
    path: Optional[Path] = None

    def load(
        self,
        msg_queue: Optional[Queue] = None,
    ) -> ichier.Design:
        lineiter = LineIterator(
            data=self.code.splitlines(),
            path=self.path,
            priority=self.priority,
            msg_queue=msg_queue,
        )
        lineiter.priority = self.priority
        if self.path is not None:
            lineiter.path = self.path
        design = parse(
            lineiter=lineiter,
            priority=self.priority,
        )
        if self.path is not None:
            design.path = self.path
            design.name = self.path.name
        return design


@dataclass
class FileItem:
    priority: tuple
    path: Path
    code: str = field(repr=False)

    def load(
        self,
        msg_queue: Optional[Queue] = None,
    ) -> ichier.Design:
        return CodeItem(
            priority=self.priority,
            code=self.path.read_text(encoding="utf-8"),
            path=self.path,
        ).load(msg_queue=msg_queue)
