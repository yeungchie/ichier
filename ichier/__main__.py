from argparse import ArgumentParser

from .parser import fromSpice, fromVerilog
from . import release


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

    parser = command.add_parser(
        "parser",
        description="Parse a circuit file, and start an interactive shell",
        help="Parse a circuit file, and start an interactive shell",
        epilog=release.copyright,
    )
    parser.add_argument(
        "format",
        type=str,
        choices=["spice", "verilog"],
        help="Format of the circuit file (spice or verilog)",
    )
    parser.add_argument("file", type=str, help="Path to the circuit file")

    return main_parser.parse_args()


def load_design(format, file):
    try:
        if format == "spice":
            return fromSpice(file)
        elif format == "verilog":
            return fromVerilog(file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    except Exception as e:
        raise RuntimeError(f"Error while loading design: {e}")


def main():
    args = parse_arguments()
    if args.command == "version":
        print(release.version)
    elif args.command == "parser":
        design = load_design(args.format, args.file)
        print(
            f"Successfully loaded design.\n"
            f"You can now interact with the Design using the `design` variable.\n"
            f"Use `exit()` or `quit()` to exit the interactive shell.\n\n"
            f"design = {repr(design)}"
        )
        try:
            from IPython import start_ipython

            start_ipython(
                argv=[],
                user_ns={"design": design},
                display_banner=False,
            )
        except ImportError:
            from code import interact

            interact(
                local={"design": design},
                banner="",
            )


if __name__ == "__main__":
    main()
