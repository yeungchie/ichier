from __future__ import annotations
from typing import Optional, overload
from rich.console import Console
from rich.progress import (
    Task,
    TaskID,
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from shutil import get_terminal_size


class LoadProgress:
    def __init__(self, *, clear: bool = True) -> None:
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=get_terminal_size().columns),
            TaskProgressColumn(),
            TextColumn("[red]{task.completed}[/red]"),
            TextColumn("/"),
            TextColumn("[green]{task.total}[/green]"),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=Console(log_time_format="[%T]"),
            transient=clear,
            expand=True,
        )
        self.add = self.progress.add_task
        self.update = self.progress.update

    def __enter__(self) -> LoadProgress:
        self.progress.__enter__()
        return self

    def __exit__(self, *args) -> None:
        self.progress.__exit__(*args)

    def task(self, id: TaskID) -> LoadTask:
        return LoadTask(self, self.progress.tasks[id])

    @overload
    def total(self, id: TaskID) -> float: ...
    @overload
    def total(self, id: TaskID, value: float) -> None: ...
    def total(self, id: TaskID, value: Optional[float] = None):
        if value is None:
            return self.progress.tasks[id].total
        elif value != self.total(id):
            self.update(id, total=value)

    @overload
    def current(self, id: TaskID) -> float: ...
    @overload
    def current(self, id: TaskID, value: float) -> None: ...
    def current(self, id: TaskID, value: Optional[float] = None):
        if value is None:
            return self.progress.tasks[id].completed
        elif value != self.current(id):
            self.update(id, completed=value)

    def done(self, id: TaskID) -> None:
        self.update(id, completed=self.progress.tasks[id].total)

    def isdone(self, id: TaskID) -> bool:
        return self.progress.tasks[id].finished


class LoadTask:
    def __init__(self, progress: LoadProgress, task: Task) -> None:
        self.__progress = progress
        self.__task = task

    @property
    def progress(self) -> LoadProgress:
        return self.__progress

    @property
    def task(self) -> Task:
        return self.__task

    @property
    def id(self) -> TaskID:
        return self.__task.id

    @property
    def description(self) -> str:
        return self.__task.description

    @description.setter
    def description(self, value: str) -> None:
        self.progress.update(self.id, description=value)

    @property
    def total(self) -> float:
        return self.progress.total(self.id)

    @total.setter
    def total(self, value: float) -> None:
        self.progress.total(self.id, value)

    @property
    def current(self) -> float:
        return self.progress.current(self.id)

    @current.setter
    def current(self, value: float) -> None:
        self.progress.current(self.id, value)

    def done(self) -> None:
        self.progress.done(self.id)

    def isdone(self) -> bool:
        return self.progress.isdone(self.id)


if __name__ == "__main__":
    from random import randint, choice
    from time import sleep

    with LoadProgress(clear=False) as p:
        tasks: list[LoadTask] = []
        for i in range(5):
            id = p.add(f"Task {i}")
            task = p.task(id)
            tasks.append(task)
            task.total = randint(20, 200)

        while True:
            if not tasks:
                break
            task = choice(tasks)
            task.current += randint(0, int(task.total / 10))
            if task.isdone():
                tasks.remove(task)
            sleep(randint(1, 5) / 100)
