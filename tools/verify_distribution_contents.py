from __future__ import annotations

import tarfile
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def fail(message: str) -> None:
    raise SystemExit(message)


def one(pattern: str) -> Path:
    matches = sorted(DIST.glob(pattern))
    if len(matches) != 1:
        fail(f"expected exactly one {pattern!r} in dist/, found {len(matches)}")
    return matches[0]


def repository_files_under(directory: str) -> set[str]:
    root = ROOT / directory
    return {
        path.relative_to(ROOT).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
        and path.name != ".DS_Store"
    }


def public_documents() -> set[str]:
    return {
        "README.md",
        "GLOSSARY.md",
        "CHANGELOG.md",
        "STATUS.md",
        *repository_files_under("docs"),
    }


def packaged_document_sources() -> dict[str, Path]:
    return {
        f"dirpluck/_docs/{relative}": ROOT / relative for relative in sorted(public_documents())
    }


def check_wheel(path: Path) -> None:
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        expected_docs = packaged_document_sources()
        required = {"dirpluck/__init__.py", *expected_docs}
        missing = sorted(required - names)
        if missing:
            fail(f"wheel is missing required files: {missing}")

        forbidden_prefixes = (
            "tests/",
            "tools/",
            "devdocs/",
            ".github/",
            "dirpluck/docs/",
        )
        forbidden = sorted(name for name in names if name.startswith(forbidden_prefixes))
        if forbidden:
            fail(
                "wheel contains files outside the wheel distribution boundary: "
                + f"{forbidden[:10]}"
            )

        for archive_name, source in expected_docs.items():
            if archive.read(archive_name) != source.read_bytes():
                fail(f"wheel document differs from repository source: {archive_name}")

        wheel_docs = {
            name for name in names if name.startswith("dirpluck/_docs/") and name.endswith(".md")
        }
        if wheel_docs != set(expected_docs):
            fail(
                "wheel documentation set differs from the public documentation set: "
                + f"unexpected={sorted(wheel_docs - set(expected_docs))}, "
                + f"missing={sorted(set(expected_docs) - wheel_docs)}"
            )


def strip_sdist_root(name: str) -> str:
    parts = name.split("/", 1)
    return parts[1] if len(parts) == 2 else ""


def release_source_files() -> set[str]:
    required = {
        ".gitignore",
        "pyproject.toml",
        "LICENSE",
        *public_documents(),
    }
    for directory in ("src", "tests", "tools", "devdocs"):
        required |= repository_files_under(directory)
    return required


def check_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = {
            strip_sdist_root(member.name): member
            for member in archive.getmembers()
            if strip_sdist_root(member.name)
        }
        names = set(members)
        required = release_source_files()
        missing = sorted(required - names)
        if missing:
            fail(f"sdist is missing required release-source files: {missing}")

        forbidden_prefixes = (
            ".github/",
            "dist/",
            "build/",
            "src/dirpluck.egg-info/",
            "__pycache__/",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            ".venv/",
            "venv/",
        )
        forbidden = sorted(name for name in names if name.startswith(forbidden_prefixes))
        if forbidden:
            fail(f"sdist contains repository-operation or generated files: {forbidden[:10]}")
        if "MANIFEST.in" in names:
            fail("sdist contains obsolete setuptools file: MANIFEST.in")

        for document in sorted(public_documents()):
            extracted = archive.extractfile(members[document])
            if extracted is None or extracted.read() != (ROOT / document).read_bytes():
                fail(f"sdist document differs from repository source: {document}")


def main() -> None:
    check_wheel(one("*.whl"))
    check_sdist(one("*.tar.gz"))
    print("distribution contents are valid")


if __name__ == "__main__":
    main()
