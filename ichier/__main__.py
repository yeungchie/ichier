from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent
from typing import Literal, Union
import os

from . import release
from . import obj
from .parser import fromSpice, fromVerilog


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
) -> obj.Design:
    try:
        if format == "spice":
            return fromSpice(file)
        elif format == "verilog":
            return fromVerilog(file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        raise RuntimeError(f"Error while loading design: {e}")


def show_tips(design: obj.Design, lang: Literal["en", "zh"] = "en"):
    title = f"IC Hierarchy {release.version}"
    if lang == "en":
        banner = dedent(f"""\
                        + Successfully loaded `{design.name}`
                        + Now you can interact with the Design using the `design` variable.
                        + Use `exit` or `quit` to exit the interactive shell.
                        """)
    elif lang == "zh":
        banner = dedent(f"""\
                        + 成功加载 `{design.name}`
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

        design = load_design(args.format, args.file)

        if args.lang == "auto":
            if os.environ.get("LANG", "").startswith("zh"):
                lang = "zh"
            else:
                lang = "en"
        else:
            lang = args.lang

        show_tips(design, lang=lang)
        cli.start({"design": design})


if __name__ == "__main__":
    main()
