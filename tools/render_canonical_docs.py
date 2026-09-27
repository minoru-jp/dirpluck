from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from shikumi_devdoc.cli import main as devdoc_main


CANONICAL_DOCUMENTS = ROOT / "devdocs" / "canonical_documents"
CONTEXT_PATH = ROOT / "devdocs" / "config" / "context.json"
NOTICE_PATH = ROOT / "devdocs" / "config" / "notice.toml"

# kind, canonical source module, shikumi-devdoc output target
DOCUMENT_ARTIFACTS: tuple[tuple[str, str, Path], ...] = (
    ("document", "devdocs.canonical_sources.readme.canonical", Path(".")),
    ("document", "devdocs.canonical_sources.changelog.canonical", Path(".")),
    ("document", "devdocs.canonical_sources.status.canonical", Path(".")),
    ("glossary", "devdocs.canonical_sources.vocabulary.canonical", Path("GLOSSARY.md")),
    ("document", "devdocs.canonical_sources.getting_started.canonical", Path("docs")),
    ("document", "devdocs.canonical_sources.trust.canonical", Path("docs")),
    ("document", "devdocs.canonical_sources.devdocs_readme.canonical", Path("devdocs")),
    ("document", "devdocs.canonical_sources.cli.overview", Path("docs/cli")),
    ("document", "devdocs.canonical_sources.cli.invocation_templates", Path("docs/cli")),
    ("document", "devdocs.canonical_sources.cli.targets", Path("docs/cli")),
    ("document", "devdocs.canonical_sources.cli.output", Path("docs/cli")),
    ("document", "devdocs.canonical_sources.configuration.overview", Path("docs/configuration")),
    ("document", "devdocs.canonical_sources.configuration.sources", Path("docs/configuration")),
    ("document", "devdocs.canonical_sources.configuration.selection", Path("docs/configuration")),
    ("document", "devdocs.canonical_sources.configuration.composition", Path("docs/configuration")),
    ("document", "devdocs.canonical_sources.configuration.output", Path("docs/configuration")),
    ("document", "devdocs.canonical_sources.configuration.examples", Path("docs/configuration")),
    ("document", "devdocs.canonical_sources.python_api.overview", Path("docs/python_api")),
    ("document", "devdocs.canonical_sources.python_api.run", Path("docs/python_api")),
    ("document", "devdocs.canonical_sources.python_api.result", Path("docs/python_api")),
    ("document", "devdocs.canonical_sources.python_api.errors", Path("docs/python_api")),
    ("document", "devdocs.canonical_sources.python_api.surface", Path("docs/python_api")),
    ("document", "devdocs.canonical_sources.specification.overview", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.document_selection", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.configuration_schema", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.paths", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.composition", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.runtime_targets", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.namespace", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.selection", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.filesystem", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.archive", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.output", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.preview", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.specification.cli_contract", Path("docs/specification")),
    ("document", "devdocs.canonical_sources.package_cli.canonical", Path("package")),
    ("document", "devdocs.canonical_sources.package_configuration.canonical", Path("package")),
    ("document", "devdocs.canonical_sources.package_trust.canonical", Path("package")),
    ("document", "devdocs.canonical_sources.python_api.overview", Path("package/python_api")),
    ("document", "devdocs.canonical_sources.python_api.run", Path("package/python_api")),
    ("document", "devdocs.canonical_sources.python_api.result", Path("package/python_api")),
    ("document", "devdocs.canonical_sources.python_api.errors", Path("package/python_api")),
    ("document", "devdocs.canonical_sources.python_api.surface", Path("package/python_api")),
)

# canonical source package, output directory, index title
INDEX_ARTIFACTS: tuple[tuple[str, Path, str], ...] = (
    ("devdocs.canonical_sources.cli", Path("docs/cli"), "dirpluck CLI Guide"),
    ("devdocs.canonical_sources.configuration", Path("docs/configuration"), "dirpluck Configuration Guide"),
    ("devdocs.canonical_sources.python_api", Path("docs/python_api"), "dirpluck Python API"),
    ("devdocs.canonical_sources.specification", Path("docs/specification"), "dirpluck Specification"),
    ("devdocs.canonical_sources.python_api", Path("package/python_api"), "dirpluck Python API"),
)

def _context() -> str:
    return CONTEXT_PATH.read_text(encoding="utf-8")


def _run(argv: list[str]) -> None:
    exit_code = devdoc_main(argv)
    if exit_code != 0:
        raise SystemExit(exit_code)


def _base_args(kind: str, module: str, output: Path, context: str) -> list[str]:
    return [
        "render",
        kind,
        module,
        "-o",
        str(output),
        "--context",
        context,
        "--notice",
        str(NOTICE_PATH),
        "--translation-source",
    ]


def _render_all(output_root: Path) -> None:
    context = _context()
    for kind, module, relative_output in DOCUMENT_ARTIFACTS:
        _run(_base_args(kind, module, output_root / relative_output, context))

    for module, relative_output, index_title in INDEX_ARTIFACTS:
        output = output_root / relative_output
        index_args = _base_args("index", module, output, context)
        index_args.extend(["--index-title", index_title])
        _run(index_args)


def _files_under(root: Path) -> set[Path]:
    if not root.exists():
        return set()
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def _check() -> None:
    with tempfile.TemporaryDirectory(prefix="dirpluck-docs-") as raw_temp:
        temp_root = Path(raw_temp) / "canonical_documents"
        _render_all(temp_root)

        actual_files = _files_under(CANONICAL_DOCUMENTS)
        rendered_files = _files_under(temp_root)
        mismatches = sorted(
            (actual_files ^ rendered_files)
            | {
                path
                for path in actual_files & rendered_files
                if (CANONICAL_DOCUMENTS / path).read_bytes()
                != (temp_root / path).read_bytes()
            }
        )

    if mismatches:
        rendered = "\n".join(f"  - {path.as_posix()}" for path in mismatches)
        raise SystemExit(
            "canonical documents are out of date:\n"
            f"{rendered}\n"
            "run `python tools/render_canonical_docs.py` and commit the results"
        )
    print("canonical documents are up to date")


def _write() -> None:
    if CANONICAL_DOCUMENTS.exists():
        shutil.rmtree(CANONICAL_DOCUMENTS)
    CANONICAL_DOCUMENTS.mkdir(parents=True)
    _render_all(CANONICAL_DOCUMENTS)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate committed Japanese canonical documents with shikumi-devdoc."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed canonical documents without modifying them",
    )
    args = parser.parse_args()
    if args.check:
        _check()
    else:
        _write()


if __name__ == "__main__":
    main()
