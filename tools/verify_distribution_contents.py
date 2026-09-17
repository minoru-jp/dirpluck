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


def check_wheel(path: Path) -> None:
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        required = {
            "dirpluck/__init__.py",
            "dirpluck/docs/README.md",
            "dirpluck/docs/CONFIGURATION.md",
            "dirpluck/docs/GLOSSARY.md",
            "dirpluck/docs/SPECIFICATION.md",
        }
        missing = sorted(required - names)
        if missing:
            fail(f"wheel is missing required files: {missing}")

        forbidden_prefixes = ("tests/", "_internal/", ".github/")
        forbidden = sorted(
            name for name in names if name.startswith(forbidden_prefixes)
        )
        if forbidden:
            fail(f"wheel contains repository-only files: {forbidden[:10]}")

        expected_docs = {
            "dirpluck/docs/README.md": ROOT / "README.md",
            "dirpluck/docs/CONFIGURATION.md": ROOT / "CONFIGURATION.md",
            "dirpluck/docs/GLOSSARY.md": ROOT / "GLOSSARY.md",
            "dirpluck/docs/SPECIFICATION.md": ROOT / "SPECIFICATION.md",
        }
        for archive_name, source in expected_docs.items():
            if archive.read(archive_name) != source.read_bytes():
                fail(f"wheel document differs from repository source: {archive_name}")


def strip_sdist_root(name: str) -> str:
    parts = name.split("/", 1)
    return parts[1] if len(parts) == 2 else ""


def check_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = {strip_sdist_root(member.name): member for member in archive.getmembers()}
        names = set(members)
        required = {
            "src/dirpluck/__init__.py",
            "tests/test_builder.py",
            "tests/test_cli.py",
            "tests/test_config.py",
            "tests/test_public_interface.py",
            "README.md",
            "CONFIGURATION.md",
            "GLOSSARY.md",
            "SPECIFICATION.md",
            "CHANGELOG.md",
            "pyproject.toml",
            "LICENSE",
        }
        missing = sorted(required - names)
        if missing:
            fail(f"sdist is missing required files: {missing}")

        forbidden_prefixes = ("_internal/", ".github/")
        forbidden = sorted(
            name for name in names if name.startswith(forbidden_prefixes)
        )
        if forbidden:
            fail(f"sdist contains repository-only files: {forbidden[:10]}")
        if ".gitignore" in names:
            fail("sdist contains repository-only file: .gitignore")

        for document in ("README.md", "CONFIGURATION.md", "GLOSSARY.md", "SPECIFICATION.md", "CHANGELOG.md"):
            extracted = archive.extractfile(members[document])
            if extracted is None or extracted.read() != (ROOT / document).read_bytes():
                fail(f"sdist document differs from repository source: {document}")


def main() -> None:
    check_wheel(one("*.whl"))
    check_sdist(one("*.tar.gz"))
    print("distribution contents are valid")


if __name__ == "__main__":
    main()
