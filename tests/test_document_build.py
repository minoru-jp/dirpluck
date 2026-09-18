from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import json
import re
import unittest

from dirpluck import __version__


ROOT = Path(__file__).resolve().parents[1]
JA_BUILD = ROOT / "_internal" / "document_build" / "ja"
EXPECTED_DOCUMENTS = {
    "README.md",
    "GLOSSARY.md",
    "CHANGELOG.md",
    "docs/CLI.md",
    "docs/CONFIGURATION.md",
    "docs/SPECIFICATION.md",
    "docs/TRUST.md",
    "package/CLI.md",
    "package/CONFIGURATION.md",
}
CANONICAL_SOURCE = re.compile(r"正本は `([^`]+)` です。")


class DocumentBuildTests(unittest.TestCase):
    def test_japanese_intermediate_document_paths_are_canonical(self):
        actual = {
            path.relative_to(JA_BUILD).as_posix()
            for path in JA_BUILD.rglob("*.md")
        }
        self.assertEqual(actual, EXPECTED_DOCUMENTS)
        self.assertNotIn("USAGE.md", actual)

    def test_japanese_intermediate_notices_use_portable_canonical_paths(self):
        for relative in sorted(EXPECTED_DOCUMENTS):
            with self.subTest(document=relative):
                text = (JA_BUILD / relative).read_text(encoding="utf-8")
                match = CANONICAL_SOURCE.search(text)
                self.assertIsNotNone(match)
                canonical = match.group(1)
                self.assertTrue(canonical.startswith("dirpluck_docs/"), canonical)
                self.assertFalse(PurePosixPath(canonical).is_absolute(), canonical)
                windows_path = PureWindowsPath(canonical)
                self.assertFalse(windows_path.is_absolute(), canonical)
                self.assertFalse(windows_path.drive, canonical)

    def test_document_context_version_matches_package_version(self):
        context_path = ROOT / "_internal" / "document_source" / "context.json"
        context = json.loads(context_path.read_text(encoding="utf-8"))
        self.assertEqual(context, {"version": __version__})

    def test_vocabulary_does_not_define_current_release_version(self):
        canonical = (
            ROOT
            / "_internal"
            / "document_source"
            / "dirpluck_docs"
            / "vocabulary"
            / "canonical.py"
        ).read_text(encoding="utf-8")
        self.assertIsNone(re.search(r'@term\("\d+\.\d+\.\d+"\)', canonical))

    def test_packaged_trust_matches_public_trust(self):
        public = (ROOT / "docs" / "TRUST.md").read_bytes()
        packaged = (ROOT / "src" / "dirpluck" / "docs" / "TRUST.md").read_bytes()
        self.assertEqual(packaged, public)

    def test_readme_uses_external_version_context(self):
        canonical = (
            ROOT
            / "_internal"
            / "document_source"
            / "dirpluck_docs"
            / "readme"
            / "canonical.py"
        ).read_text(encoding="utf-8")
        self.assertIn("{{version}}", canonical)
        self.assertNotIn("TERM_11", canonical)


if __name__ == "__main__":
    unittest.main()
