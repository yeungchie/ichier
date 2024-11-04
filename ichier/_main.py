from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent
from typing import Literal, Optional, Union
import os

from . import release
from . import obj


def parse_arguments():
    main_parser = ArgumentParser(
        prog="ichier",
        description="Interactive Circuit Hierarchy (ICHier)",
        epilog=release.copyright,
    )
    main_parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {release.version}",
    )
    command = main_parser.add_subparsers(dest="command", required=True)
    command.add_parser(
        "version",
        description="Show version information",
        help="Show version information",
        epilog=release.copyright,
    )

    parse = command.add_parser(
        "parse",
        description="Parse a circuit file, and start an interactive shell",
        help="Parse a circuit file, and start an interactive shell",
        epilog=release.copyright,
    )
    parse.add_argument(
        "format",
        type=str,
        choices=["spice", "verilog"],
        help="Format of the circuit file (spice or verilog)",
    )
    parse.add_argument("file", type=str, help="Path to the circuit file")
    parse.add_argument(
        "--lang",
        type=str,
        choices=["auto", "en", "zh"],
        default="auto",
        help="Language for tips",
    )

    return main_parser.parse_args()


def load_design(
    format: Literal["spice", "verilog"],
    file: Union[str, Path],
) -> Optional[obj.Design]:
    try:
        if format == "spice":
            return __load_spice(file)
        elif format == "verilog":
            return __load_verilog(file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except KeyboardInterrupt:
        return
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e.filename}")
    except Exception as e:
        raise RuntimeError(f"Error while loading design.\n{e}")


def __load_spice(file) -> obj.Design:
    if load_progress := create_progress():
        from icutk.string import LineIterator
        from .parser.spice import fromFile

        def line_next_cb(lineiter: LineIterator, data: str):
            if load_progress.finished:
                return
            if lineiter.line > load_progress.completed:
                load_progress.set_completed(lineiter.line)

        with load_progress:
            path = Path(file)
            design = fromFile(path, cb_next=line_next_cb)
            load_progress.done()
            design.name = path.name
            design.path = path
    else:
        from .parser.spice import fromFile

        design = fromFile(file)
    return design


def __load_verilog(file) -> obj.Design:
    if load_progress := create_progress():
        from icutk.lex import Lexer, LexToken
        from .parser.verilog import VerilogParser

        def verilog_input_cb(lexer: Lexer):
            if not isinstance(lexer.lexdata, str):
                raise ValueError("lexer.lexdata should be a string")
            load_progress.set_total(lexer.lexdata.count("\n"))

        def verilog_token_cb(lexer: Lexer, token: LexToken):
            if load_progress.finished:
                return
            if lexer.lineno > load_progress.completed:
                load_progress.set_completed(lexer.lineno)

        with load_progress:
            parser = VerilogParser(cb_input=verilog_input_cb, cb_token=verilog_token_cb)
            path = Path(file)
            design = parser.parse(path.read_text())
            load_progress.done()
            design.name = path.name
            design.path = path
    else:
        from .parser.verilog import fromFile

        design = fromFile(file)
    return design


def create_progress():
    try:
        from rich.console import Console
        from rich.progress import (
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
            def __init__(self):
                self.progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=get_terminal_size().columns),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    TimeElapsedColumn(),
                    console=Console(log_time_format="[%T]"),
                    transient=True,
                    expand=True,
                )
                self.progress.add_task("Parsing")
                self.task = self.progress.tasks[0]

            @property
            def finished(self):
                return self.progress.finished or self.task.finished

            @property
            def total(self):
                return self.task.total

            @property
            def completed(self):
                return self.task.completed

            def set_total(self, total: int):
                if self.finished:
                    return
                self.progress.update(self.task.id, total=total)

            def set_completed(self, current: int):
                if self.finished:
                    return
                self.progress.update(self.task.id, completed=current)

            def done(self):
                self.progress.update(self.task.id, completed=self.task.total)

            def __enter__(self):
                self.progress.__enter__()
                return self

            def __exit__(self, *args, **kwargs):
                self.progress.__exit__(*args, **kwargs)

        return LoadProgress()
    except ImportError:
        return


def show_tips(design: obj.Design, used_time: float, lang: Literal["en", "zh"] = "en"):
    title = f"IC Hierarchy {release.version}"
    if lang == "en":
        banner = dedent(f"""\
                        + Successfully loaded `{design.name}` used {used_time:.2f} seconds.
                        + Now you can interact with the Design using the `design` variable.
                        + Use `exit` or `quit` to exit the interactive shell.
                        """)
    elif lang == "zh":
        banner = dedent(f"""\
                        + 成功加载 `{design.name}` 用时 {used_time:.2f} 秒。
                        + 现在你可以使用 `design` 变量与设计进行交互了。
                        + 使用 `exit` 或 `quit` 退出交互界面。
                        """)
    else:
        raise ValueError(f"Unsupported language: {lang}")
    code = dedent(f"""\
                    design          # {design!r}
                    design.path     # {design.path!r}
                    design.modules  # {design.modules!r}

                    for module in design.modules:       # iterate over modules in the design
                        for inst in module.instances:   # iterate over instances in each module
                            ...
                    """)
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich.syntax import Syntax

        console = Console()
        console.print(
            Panel(Markdown(banner), title=f"\U0001f349 {title}", border_style="blue")
        )
        console.print()
        console.print(
            Syntax(
                code.rstrip(), "python", theme="monokai", line_numbers=True, padding=1
            )
        )
    except ImportError:
        print(title)
        print(banner)
        print(code)


def main():
    args = parse_arguments()
    if args.command == "version":
        print(release.version)
    elif args.command == "parse":
        from icutk import cli
        from time import perf_counter

        start = perf_counter()
        design = load_design(args.format, args.file)
        if design is None:
            return
        used = perf_counter() - start

        if args.lang == "auto":
            if os.environ.get("LANG", "").startswith("zh"):
                lang = "zh"
            else:
                lang = "en"
        else:
            lang = args.lang

        show_tips(design, used_time=used, lang=lang)
        cli.start({"design": design})
