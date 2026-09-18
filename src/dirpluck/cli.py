"""Command-line interface for dirpluck."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

from . import __version__
from .builder import BuildRequest, build_archive, plan_archive, render_archive_tree
from .config import CONFIG_NAME, discover_config_paths, load_config, resolve_config_path
from .errors import DirpluckError


def _positive_sequence(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer greater than or equal to 1") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be an integer greater than or equal to 1")
    return number


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dirpluck")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--configs",
        action="store_true",
        help="list Configuration files discoverable from the current directory and exit",
    )
    parser.add_argument(
        "directories",
        nargs="*",
        type=Path,
        metavar="DIRECTORY",
        help="one or more target directories when the selected Configuration defines [target]",
    )
    parser.add_argument(
        "--case",
        action="append",
        metavar="NAME",
        help="one named Configuration Case",
    )
    parser.add_argument(
        "--sequence",
        action="append",
        type=_positive_sequence,
        metavar="N",
        help="one explicit positive sequence number for a generated output name",
    )
    parser.add_argument(
        "--config",
        metavar="NAME",
        help=(
            "Configuration filename searched in ./ and ./dirpluck/; "
            f"'.toml' may be omitted (default: {CONFIG_NAME})"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the ZIP contents as a tree without creating an archive",
    )
    parser.add_argument(
        "--paths",
        action="store_true",
        help="include resolved source filesystem paths in the generated archive README",
    )
    return parser


def _display_path(path: Path, cwd: Path) -> str:
    relative = path.resolve().relative_to(cwd.resolve()).as_posix()
    return f"./{relative}"


def _render_configs(cwd: Path | None = None) -> str:
    root = (cwd or Path.cwd()).resolve()
    paths = discover_config_paths(cwd=root)
    if not paths:
        return "No Configurations found."

    counts = Counter(path.name for path in paths)
    lines: list[str] = []
    for path in sorted(paths, key=lambda item: (item.name, item.parent != root, item.as_posix())):
        tags: list[str] = []
        if path.name == CONFIG_NAME:
            tags.append("default")
        if counts[path.name] > 1:
            tags.append("ambiguous")
        suffix = f"  [{' | '.join(tags)}]" if tags else ""
        lines.append(f"{path.name}  {_display_path(path, root)}{suffix}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.configs:
        if (
            bool(args.directories)
            or args.case is not None
            or args.sequence is not None
            or args.config is not None
            or args.dry_run
            or args.paths
        ):
            parser.error("--configs cannot be combined with a target or build options")
        print(_render_configs())
        return 0

    if args.case is not None and len(args.case) > 1:
        parser.error("--case may be specified at most once")
    if args.sequence is not None and len(args.sequence) > 1:
        parser.error("--sequence may be specified at most once")
    selected_case = None if args.case is None else args.case[0]
    selected_sequence = None if args.sequence is None else args.sequence[0]

    try:
        config_path = resolve_config_path(args.config)
        config = load_config(config_path)
        request = BuildRequest.create(
            *args.directories,
            case=selected_case,
            sequence=selected_sequence,
            paths=args.paths,
        )
        if args.dry_run:
            print(render_archive_tree(plan_archive(config, request, allow_missing=True)))
            return 0

        result = build_archive(config, request)
        print(result)
        return 0
    except DirpluckError as exc:
        parser.exit(2, f"dirpluck: error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
