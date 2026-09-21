"""Command-line interface for dirpluck."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from ._application import run
from ._archive import render_link_skip_note
from .config import CONFIG_NAME
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
        "directories",
        nargs="*",
        metavar="TARGET",
        help=(
            "Target reference: NAME (default Scope), SCOPE/NAME (named Scope), "
            "/ (all in default Scope), or SCOPE/ (all in named Scope); "
            "one or more required when [pluck] is defined"
        ),
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
        help="one explicit positive sequence number for a timestamp output name",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help=(
            "Configuration document path; relative paths use cwd and '.dirpluck' "
            f"may be omitted (default: ./{CONFIG_NAME})"
        ),
    )
    parser.add_argument(
        "-i",
        "--invocation-template",
        action="append",
        metavar="PATH",
        help=(
            "Invocation Template document path; relative paths use cwd and "
            "'.dirpluck-inv' may be omitted"
        ),
    )
    parser.add_argument(
        "-e",
        "--entry",
        action="append",
        metavar="NAME",
        help="one named Invocation entry from the selected Invocation Template",
    )
    parser.add_argument(
        "--archive-mtime",
        action="append",
        metavar="VALUE",
        help=(
            "set one timestamp on every ZIP entry: YYYY-MM-DDTHH:MM:SS, "
            "'now', or 'zip-epoch'"
        ),
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="preview the ZIP contents as a tree without creating an archive",
    )
    parser.add_argument(
        "--paths",
        action="store_true",
        help="include resolved source filesystem paths in the generated archive README",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.case is not None and len(args.case) > 1:
        parser.error("--case may be specified at most once")
    if args.sequence is not None and len(args.sequence) > 1:
        parser.error("--sequence may be specified at most once")
    if args.archive_mtime is not None and len(args.archive_mtime) > 1:
        parser.error("--archive-mtime may be specified at most once")
    if args.invocation_template is not None and len(args.invocation_template) > 1:
        parser.error("--invocation-template may be specified at most once")
    if args.entry is not None and len(args.entry) > 1:
        parser.error("--entry may be specified at most once")
    selected_case = None if args.case is None else args.case[0]
    selected_sequence = None if args.sequence is None else args.sequence[0]
    selected_archive_mtime = (
        None if args.archive_mtime is None else args.archive_mtime[0]
    )
    selected_invocation = (
        None if args.invocation_template is None else args.invocation_template[0]
    )
    selected_entry = None if args.entry is None else args.entry[0]

    # Preserve CLI-specific diagnostics while the same combinations are also
    # validated by the public Python API.
    if args.preview and selected_sequence is not None:
        parser.error("--sequence cannot be combined with --preview")
    if selected_entry is not None and selected_invocation is None:
        parser.error("--entry requires --invocation-template")
    if selected_invocation is not None:
        if args.config is not None:
            parser.error("--config cannot be combined with --invocation-template")
        if args.directories:
            parser.error("TARGET arguments cannot be combined with --invocation-template")

    try:
        result = run(
            *args.directories,
            config=args.config,
            case=selected_case,
            sequence=selected_sequence,
            invocation=selected_invocation,
            entry=selected_entry,
            preview=args.preview,
            paths=args.paths,
            archive_mtime=selected_archive_mtime,
        )
        if args.preview:
            print(result.preview_text)
        else:
            print(result.output_path)
        if result.invocation_empty:
            print(
                "note: selected Invocation provides no config, targets, case, or archive_mtime; "
                "execution uses CLI values and normal defaults"
            )
        if not args.preview and result.skipped_link_count:
            print(render_link_skip_note(result.skipped_link_count, preview=False))
        return 0
    except DirpluckError as exc:
        parser.exit(2, f"dirpluck: error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
