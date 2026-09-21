from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import json
import re
import unittest

from dirpluck import __version__


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE_DOCUMENTS = ROOT / "devdocs" / "intermediate_documents"
EXPECTED_DOCUMENTS = {
    "README.md",
    "GLOSSARY.md",
    "CHANGELOG.md",
    "docs/CLI.md",
    "docs/PYTHON_API.md",
    "docs/CONFIGURATION.md",
    "docs/SPECIFICATION.md",
    "docs/TRUST.md",
    "devdocs/README.md",
    "package/CLI.md",
    "package/CONFIGURATION.md",
    "package/PYTHON_API.md",
}
CANONICAL_SOURCE = re.compile(r"正本は `([^`]+)` です。")


class DocumentBuildTests(unittest.TestCase):
    def test_japanese_intermediate_document_paths_are_canonical(self):
        actual = {
            path.relative_to(INTERMEDIATE_DOCUMENTS).as_posix()
            for path in INTERMEDIATE_DOCUMENTS.rglob("*.md")
        }
        self.assertEqual(actual, EXPECTED_DOCUMENTS)
        self.assertNotIn("USAGE.md", actual)

    def test_japanese_intermediate_notices_use_portable_canonical_paths(self):
        for relative in sorted(EXPECTED_DOCUMENTS):
            with self.subTest(document=relative):
                text = (INTERMEDIATE_DOCUMENTS / relative).read_text(encoding="utf-8")
                match = CANONICAL_SOURCE.search(text)
                self.assertIsNotNone(match)
                canonical = match.group(1)
                self.assertTrue(canonical.startswith("devdocs/canonical_documents/"), canonical)
                self.assertFalse(PurePosixPath(canonical).is_absolute(), canonical)
                windows_path = PureWindowsPath(canonical)
                self.assertFalse(windows_path.is_absolute(), canonical)
                self.assertFalse(windows_path.drive, canonical)

    def test_canonical_documents_use_direct_package_namespace(self):
        package = ROOT / "devdocs" / "canonical_documents"
        self.assertTrue((package / "__init__.py").is_file())
        self.assertTrue((package / "terms.py").is_file())
        self.assertFalse((package / "dirpluck_docs").exists())

        for canonical in package.glob("*/canonical.py"):
            if canonical.parent.name == "vocabulary":
                continue
            text = canonical.read_text(encoding="utf-8")
            self.assertIn("from canonical_documents import terms", text)
            self.assertNotIn("dirpluck_docs", text)

    def test_document_context_version_matches_package_version(self):
        context_path = ROOT / "devdocs" / "config" / "context.json"
        context = json.loads(context_path.read_text(encoding="utf-8"))
        self.assertEqual(context, {"version": __version__})

    def test_vocabulary_does_not_define_current_release_version(self):
        canonical = (
            ROOT
            / "devdocs"
            / "canonical_documents"
            / "vocabulary"
            / "canonical.py"
        ).read_text(encoding="utf-8")
        self.assertIsNone(re.search(r'@term\("\d+\.\d+\.\d+"\)', canonical))

    def test_packaged_trust_matches_public_trust(self):
        public = (ROOT / "docs" / "TRUST.md").read_bytes()
        packaged = (ROOT / "src" / "dirpluck" / "docs" / "TRUST.md").read_bytes()
        self.assertEqual(packaged, public)

    def test_packaged_python_api_matches_public_python_api(self):
        public = (ROOT / "docs" / "PYTHON_API.md").read_bytes()
        packaged = (ROOT / "src" / "dirpluck" / "docs" / "PYTHON_API.md").read_bytes()
        self.assertEqual(packaged, public)

    def test_readme_uses_external_version_context(self):
        canonical = (
            ROOT
            / "devdocs"
            / "canonical_documents"
            / "readme"
            / "canonical.py"
        ).read_text(encoding="utf-8")
        self.assertIn("{{version}}", canonical)
        self.assertNotIn("TERM_11", canonical)


if __name__ == "__main__":
    unittest.main()
