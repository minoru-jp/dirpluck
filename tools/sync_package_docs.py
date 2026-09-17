from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DOCS = ROOT / "src" / "dirpluck" / "docs"
DOCUMENTS = ("USAGE.md",)


def main() -> None:
    PACKAGE_DOCS.mkdir(parents=True, exist_ok=True)
    for path in PACKAGE_DOCS.glob("*.md"):
        if path.name not in DOCUMENTS:
            path.unlink()
    for name in DOCUMENTS:
        source = ROOT / name
        target = PACKAGE_DOCS / name
        target.write_bytes(source.read_bytes())
    print("package documents synchronized")


if __name__ == "__main__":
    main()
