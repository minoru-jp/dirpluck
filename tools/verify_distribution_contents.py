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
        expected_docs = {
            "dirpluck/docs/CLI.md": ROOT / "src" / "dirpluck" / "docs" / "CLI.md",
            "dirpluck/docs/CONFIGURATION.md": ROOT / "src" / "dirpluck" / "docs" / "CONFIGURATION.md",
        }
        required = {"dirpluck/__init__.py", *expected_docs}
        missing = sorted(required - names)
        if missing:
            fail(f"wheel is missing required files: {missing}")

        forbidden_prefixes = ("tests/", "tools/", "_internal/", ".github/")
        forbidden = sorted(
            name for name in names if name.startswith(forbidden_prefixes)
        )
        if forbidden:
            fail(f"wheel contains repository-only files: {forbidden[:10]}")

        for archive_name, source in expected_docs.items():
            if archive.read(archive_name) != source.read_bytes():
                fail(f"wheel document differs from repository source: {archive_name}")

        wheel_docs = {
            name for name in names if name.startswith("dirpluck/docs/") and name.endswith(".md")
        }
        if wheel_docs != set(expected_docs):
            fail(
                "wheel contains unexpected packaged documents: "
                f"{sorted(wheel_docs - set(expected_docs))}"
            )


def strip_sdist_root(name: str) -> str:
    parts = name.split("/", 1)
    return parts[1] if len(parts) == 2 else ""


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


def check_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = {strip_sdist_root(member.name): member for member in archive.getmembers()}
        names = set(members)
        public_documents = {
            "README.md",
            "GLOSSARY.md",
            "CHANGELOG.md",
            "docs/CLI.md",
            "docs/CONFIGURATION.md",
            "docs/SPECIFICATION.md",
            "docs/TRUST.md",
        }
        required = {
            "src/dirpluck/__init__.py",
            "pyproject.toml",
            "LICENSE",
            *public_documents,
        }
        required |= repository_files_under("tests")
        required |= repository_files_under("tools")
        required |= repository_files_under("_internal")
        required |= repository_files_under("docs")
        missing = sorted(required - names)
        if missing:
            fail(f"sdist is missing required files: {missing}")

        forbidden_prefixes = (".github/",)
        forbidden = sorted(
            name for name in names if name.startswith(forbidden_prefixes)
        )
        if forbidden:
            fail(f"sdist contains repository-only files: {forbidden[:10]}")
        if ".gitignore" in names:
            fail("sdist contains repository-only file: .gitignore")

        for document in sorted(public_documents):
            extracted = archive.extractfile(members[document])
            if extracted is None or extracted.read() != (ROOT / document).read_bytes():
                fail(f"sdist document differs from repository source: {document}")


def main() -> None:
    check_wheel(one("*.whl"))
    check_sdist(one("*.tar.gz"))
    print("distribution contents are valid")


if __name__ == "__main__":
    main()
