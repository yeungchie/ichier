from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent
from typing import Literal, Optional, Union
import os

from . import release
from .node import obj


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
    try:
        from .utils.progress import LoadProgress, LoadTask
        from icutk.string import LineIterator
        from .parser.spice import fromFile

        load_progress = LoadProgress()

        def line_init_cb(lineiter: LineIterator):
            id = load_progress.add("Spice")
            task = load_progress.task(id)
            task.total = lineiter.total_lines
            lineiter.task = task  # type: ignore

        def line_next_cb(lineiter: LineIterator, data: str):
            task: LoadTask = lineiter.task  # type: ignore
            if task.isdone():
                return
            if task.current == 0:
                task.description = f"{"  "*len(lineiter.priority)}{lineiter.path.name}"  # type: ignore
            task.current = lineiter.line

        with load_progress:
            path = Path(file)
            design = fromFile(path, cb_init=line_init_cb, cb_next=line_next_cb)
            design.name = path.name
            design.path = path
    except ImportError:
        from .parser.spice import fromFile

        design = fromFile(file)
    return design


def __load_verilog(file) -> obj.Design:
    try:
        from .utils.progress import LoadProgress, LoadTask
        from icutk.lex import Lexer, LexToken
        from .parser.verilog import VerilogParser

        load_progress = LoadProgress()

        def verilog_input_cb(lexer: Lexer):
            if not isinstance(lexer.lexdata, str):
                raise ValueError("lexer.lexdata should be a string")
            id = load_progress.add("Parsing ...")
            task = load_progress.task(id)
            task.total = lexer.lexdata.count("\n") + 1
            lexer.task = task  # type: ignore

        def verilog_token_cb(lexer: Lexer, token: LexToken):
            task: LoadTask = lexer.task  # type: ignore
            if task.isdone():
                return
            task.current = lexer.lineno

        with load_progress:
            vparser = VerilogParser(
                cb_input=verilog_input_cb,
                cb_token=verilog_token_cb,
            )
            path = Path(file)
            design = vparser.parse(path.read_text())
            # load_progress.done()
            design.name = path.name
            design.path = path
            design.modules.rebuild(mute=True, verilog_style=True)
    except ImportError:
        from .parser.verilog import fromFile

        design = fromFile(file)
        design.modules.rebuild(mute=True, verilog_style=True)
    return design


def create_progress():
    try:
        from .utils.progress import LoadProgress

        return LoadProgress(clear=False)
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

    modules_lines = repr(design.modules).splitlines(keepends=True)
    modules_repr = modules_lines[0]
    for line in modules_lines[1:]:
        modules_repr += " " * 36 + f"# {line}"

    code = dedent(f"""\
                    design          # {design!r}
                    design.path     # {design.path!r}
                    design.modules  # {modules_repr}

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
