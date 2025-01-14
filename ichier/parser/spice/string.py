from pathlib import Path
from queue import Queue
from typing import Optional, Tuple, Union
from uuid import uuid4
from icutk.string import LineIterator as _LineIterator


class LineIterator(_LineIterator):
    def __init__(
        self,
        *args,
        path: Optional[Union[str, Path]] = None,
        priority: Tuple[int, ...] = (),
        msg_queue: Optional[Queue] = None,
        **kwargs,
    ) -> None:
        if path is None:
            self.path = None
        else:
            self.path = Path(path)
        self.priority = priority
        self.msg_queue = msg_queue

        self.id: str = uuid4().hex
        self.last_percent: int = 0

        super().__init__(*args, **kwargs)
        self.cb_init()

    def cb_init(self) -> None:
        if self.msg_queue is None:
            return
        if self.path is None:
            path_name = "Spice"
        else:
            path_name = self.path.name
        description = f"{'  '*len(self.priority)}{path_name}"
        self.msg_queue.put(dict(id=self.id, type="init", value=description))
        self.msg_queue.put(dict(id=self.id, type="total", value=self.total_lines))

    @property
    def next(self) -> str:
        data = super().next
        self.cb_next()
        return data

    def cb_next(self) -> None:
        if self.msg_queue is None:
            return
        percent = int(self.line / self.total_lines * 100)
        if percent > self.last_percent:
            self.msg_queue.put(dict(id=self.id, type="current", value=self.line))
            self.last_percent = percent
