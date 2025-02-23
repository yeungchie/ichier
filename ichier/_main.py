from argparse import ArgumentParser
from multiprocessing import Process
from pathlib import Path
from textwrap import dedent
from typing import Literal, Optional, Union
import os
import re

from . import release
from .parser import fromVerilog, fromSpice
import ichier


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

    command = main_parser.add_subparsers(dest="command", required=False)
    parse = command.add_parser(
        "parse",
        description="Parse a circuit file, and start an interactive shell",
        help="Parse a circuit file, and start an interactive shell",
        epilog=release.copyright,
    )

    parse.add_argument("file", type=str, help="Path to the circuit file")
    parse.add_argument(
        "--lang",
        type=str,
        choices=["auto", "en", "zh"],
        default="auto",
        help="Language for tips",
    )

    command.add_parser(
        "version",
        description="Show version information",
        help="Show version information",
        epilog=release.copyright,
    )

    return main_parser.parse_args()


def load_file(
    file: Union[str, Path],
    format: Optional[Literal["spice", "verilog"]] = None,
) -> Optional[ichier.Design]:
    if format is None:
        if ":" in str(file):
            file, _, mark = str(file).rpartition(":")
        else:
            mark = str(file).rpartition(".")[-1]

        spice_pattern = r"sp|spi|spice|cdl|cir"
        verilog_pattern = r"v|vh|vhd|verilog"
        if re.match(spice_pattern, mark, re.IGNORECASE):
            format = "spice"
        elif re.match(verilog_pattern, mark, re.IGNORECASE):
            format = "verilog"
        else:
            raise ValueError(
                f"support format mark: spice({spice_pattern}) or verilog({verilog_pattern}) - {mark!r}"
            )

    if format == "spice":
        loader = load_spice
    elif format == "verilog":
        loader = load_verilog
    else:
        raise ValueError(f"Unsupported format: {format}")

    try:
        return loader(file)
    except KeyboardInterrupt:
        return
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e.filename}")


try:
    from .utils.progress import Daemon

    def load_verilog(file) -> ichier.Design:
        PD = Daemon()
        pdp = Process(target=PD.worker, daemon=True)
        pdp.start()
        design = fromVerilog(file, msg_queue=PD.msg_queue)
        design.modules.rebuild(mute=True, verilog_style=True)
        pdp.join(300)
        if pdp.is_alive():
            pdp.terminate()
        return design

    def load_spice(file) -> ichier.Design:
        PD = Daemon()
        pdp = Process(target=PD.worker, daemon=True)
        pdp.start()
        design = fromSpice(file, msg_queue=PD.msg_queue)
        design.modules.rebuild(mute=True)
        pdp.join(300)
        if pdp.is_alive():
            pdp.terminate()
        return design

except ImportError:

    def load_verilog(file) -> ichier.Design:
        design = fromVerilog(file)
        design.modules.rebuild(mute=True, verilog_style=True)
        return design

    def load_spice(file) -> ichier.Design:
        design = fromSpice(file)
        design.modules.rebuild(mute=True)
        return design


def show_tips(
    design: ichier.Design, used_time: float, lang: Literal["en", "zh"] = "en"
):
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
        return

    from icutk import cli

    variables = {name: getattr(ichier, name) for name in ichier.__all__}
    if args.command is None:
        pass
    elif args.command == "parse":
        from time import perf_counter

        if args.lang == "auto":
            if os.environ.get("LANG", "").startswith("zh"):
                lang = "zh"
            else:
                lang = "en"
        else:
            lang = args.lang
        if lang not in ("en", "zh"):
            raise ValueError(f"Unsupported language: {lang}")

        start = perf_counter()
        design = load_file(args.file)
        if design is None:
            return
        used = perf_counter() - start

        show_tips(design, used_time=used, lang=lang)

        variables["design"] = design

    cli.start(variables)
