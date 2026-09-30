"""Command-line interface for dirpluck."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from ._application import run
from ._archive import render_link_skip_note
from ._config_parser import collect_configuration_deprecations
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


def _normalize_here_arguments(argv: list[str]) -> tuple[list[str], str | None, int]:
    """Normalize --here[=FILENAME] while requiring '=' for the optional filename."""

    normalized: list[str] = []
    filename: str | None = None
    count = 0
    positional_only = False
    for token in argv:
        if positional_only:
            normalized.append(token)
            continue
        if token == "--":
            positional_only = True
            normalized.append(token)
            continue
        if token == "--here":
            count += 1
            normalized.append("--here")
            continue
        if token.startswith("--here="):
            count += 1
            filename = token.partition("=")[2]
            normalized.append("--here")
            continue
        normalized.append(token)
    return normalized, filename, count


def _validate_here_filename(parser: argparse.ArgumentParser, value: str) -> str:
    if not value:
        parser.error("--here filename must not be empty")
    if value in {".", ".."} or "/" in value or "\\" in value:
        parser.error("--here accepts a filename only; use --output for a path")
    if any(char in value for char in '<>:"|?*') or any(
        ord(char) < 32 or ord(char) == 127 for char in value
    ):
        parser.error("--here filename must be one portable filename")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dirpluck")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "directories",
        nargs="*",
        metavar="TARGET",
        help=(
            "Target reference: NAME or ./NAME (default file), ./NAME/ (default directory), "
            "SCOPE/NAME (named file), SCOPE/NAME/ (named directory), "
            "/ or SCOPE/ (Scope expansion), :[...] / SCOPE:[...] (literal Target lists), "
            "or :<REGEX> / SCOPE:<REGEX> (regular-expression Target selectors); "
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
        "--here",
        action="store_true",
        help=(
            "write to cwd; use --here=FILENAME for an explicit filename, "
            "otherwise use an automatic timestamp name"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        action="append",
        metavar="PATH",
        help=(
            "runtime output path; a trailing '/' selects automatic timestamp naming "
            "in that directory"
        ),
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="allow the effective output archive to be replaced if it already exists",
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
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    normalized_argv, here_filename, here_count = _normalize_here_arguments(raw_argv)
    args = parser.parse_args(normalized_argv)

    if here_count > 1:
        parser.error("--here may be specified at most once")

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
    if args.output is not None and len(args.output) > 1:
        parser.error("--output may be specified at most once")
    selected_case = None if args.case is None else args.case[0]
    selected_sequence = None if args.sequence is None else args.sequence[0]
    selected_archive_mtime = (
        None if args.archive_mtime is None else args.archive_mtime[0]
    )
    selected_invocation = (
        None if args.invocation_template is None else args.invocation_template[0]
    )
    selected_entry = None if args.entry is None else args.entry[0]
    selected_output = None if args.output is None else args.output[0]
    if args.here and selected_output is not None:
        parser.error("--here cannot be combined with --output")
    if args.here:
        selected_output = (
            "./" if here_filename is None else _validate_here_filename(parser, here_filename)
        )

    # Preserve CLI-specific diagnostics while the same combinations are also
    # validated by the public Python API.
    if args.preview and selected_sequence is not None:
        parser.error("--sequence cannot be combined with --preview")
    if args.preview and args.here:
        parser.error("--here cannot be combined with --preview")
    if args.preview and selected_output is not None:
        parser.error("--output cannot be combined with --preview")
    if args.preview and args.force:
        parser.error("--force cannot be combined with --preview")
    if selected_entry is not None and selected_invocation is None:
        parser.error("--entry requires --invocation-template")
    if selected_invocation is not None:
        if args.config is not None:
            parser.error("--config cannot be combined with --invocation-template")
        if args.directories:
            parser.error("TARGET arguments cannot be combined with --invocation-template")

    try:
        with collect_configuration_deprecations() as configuration_deprecations:
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
                    output=selected_output,
                    force=args.force,
                )
            finally:
                for warning in configuration_deprecations:
                    print(f"dirpluck: warning: {warning}", file=sys.stderr)
        for warning in result.warnings:
            print(f"dirpluck: warning: {warning}", file=sys.stderr)
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
