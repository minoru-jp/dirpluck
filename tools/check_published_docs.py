from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Protocol, cast


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DOCUMENTS = ROOT / "devdocs" / "canonical_documents"
MANIFEST = ROOT / "devdocs" / "config" / "publication_manifest.json"
CONTEXT = ROOT / "devdocs" / "config" / "context.json"


class _Arguments(Protocol):
    update: bool


def document_digest(path: Path) -> str:
    # Publication snapshots track Markdown content, not the platform-specific
    # physical line endings produced by a Git checkout. ``read_text`` uses
    # universal-newline handling, so LF and CRLF documents hash identically.
    text = path.read_text(encoding="utf-8")
    return sha256(text.encode("utf-8")).hexdigest()


def _current_version() -> str:
    context = cast(dict[str, object], json.loads(CONTEXT.read_text(encoding="utf-8")))
    version = context.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("devdocs/config/context.json must contain a non-empty version string")
    return version


def _canonical_paths() -> tuple[Path, ...]:
    return tuple(
        sorted(
            path.relative_to(CANONICAL_DOCUMENTS)
            for path in CANONICAL_DOCUMENTS.rglob("*.md")
            if path.is_file()
        )
    )


def _validate_public_document(path: Path, relative: Path) -> None:
    if not path.is_file():
        raise SystemExit(
            f"published English document is missing for {relative.as_posix()!r}: {path}"
        )
    text = path.read_text(encoding="utf-8")
    if "shikumi-devdoc:translation-metadata" in text or "この文書は自動生成された翻訳元" in text:
        raise SystemExit(
            f"published document {relative.as_posix()!r} still contains canonical translation metadata"
        )


def _validate_release_markers() -> None:
    version = _current_version()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"The current version is **{version}**." not in readme:
        raise SystemExit(
            f"README.md does not publish the current release version {version}; "
            + "translate and publish the regenerated canonical README first"
        )
    if f"## {version}" not in changelog:
        raise SystemExit(
            f"CHANGELOG.md does not contain the current release {version}; "
            + "translate and publish the regenerated canonical CHANGELOG first"
        )


def _snapshot() -> dict[str, object]:
    documents: dict[str, dict[str, str]] = {}
    for relative in _canonical_paths():
        canonical = CANONICAL_DOCUMENTS / relative
        public = ROOT / relative
        _validate_public_document(public, relative)
        documents[relative.as_posix()] = {
            "canonical_sha256": document_digest(canonical),
            "public_sha256": document_digest(public),
        }
    _validate_release_markers()
    return {"version": 2, "documents": documents}


def _write_manifest(snapshot: dict[str, object]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    _ = MANIFEST.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"updated published-document snapshot: {MANIFEST.relative_to(ROOT)}")


def _check_manifest(snapshot: dict[str, object]) -> None:
    if not MANIFEST.is_file():
        raise SystemExit(
            "published-document snapshot is missing; after translating canonical documents, "
            + "run `python tools/check_published_docs.py --update`"
        )
    actual = cast(dict[str, object], json.loads(MANIFEST.read_text(encoding="utf-8")))
    if actual == snapshot:
        print("published English documents match the reviewed canonical-document snapshot")
        return

    expected_documents = cast(dict[str, object], snapshot["documents"])
    actual_documents_raw = actual.get("documents")
    actual_documents = (
        cast(dict[str, object], actual_documents_raw)
        if isinstance(actual_documents_raw, dict)
        else {}
    )
    changed = sorted(
        set(expected_documents) ^ set(actual_documents)
        | {
            name
            for name in set(expected_documents) & set(actual_documents)
            if expected_documents[name] != actual_documents[name]
        }
    )
    details = "\n".join(f"  - {name}" for name in changed) or "  - manifest metadata"
    raise SystemExit(
        "published English documents are not synchronized with the reviewed canonical snapshot:\n"
        + details
        + "\ntranslate/publish the regenerated canonical documents, then run "
        + "`python tools/check_published_docs.py --update` and commit the manifest"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that published English Markdown and generated Japanese canonical documents "
            "belong to the same reviewed publication snapshot."
        )
    )
    _ = parser.add_argument(
        "--update",
        action="store_true",
        help="record the current canonical/public document hashes after translation and review",
    )
    args = cast(_Arguments, cast(object, parser.parse_args()))
    snapshot = _snapshot()
    if args.update:
        _write_manifest(snapshot)
    else:
        _check_manifest(snapshot)


if __name__ == "__main__":
    main()
