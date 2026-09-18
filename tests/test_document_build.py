from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
JA_BUILD = ROOT / "_internal" / "document_build" / "ja"
EXPECTED_DOCUMENTS = {
    "README.md",
    "USAGE.md",
    "CONFIGURATION.md",
    "GLOSSARY.md",
    "SPECIFICATION.md",
    "CHANGELOG.md",
}
CANONICAL_SOURCE = re.compile(r"正本は `([^`]+)` です。")


class DocumentBuildTests(unittest.TestCase):
    def test_japanese_intermediate_document_names_are_canonical(self):
        actual = {path.name for path in JA_BUILD.glob("*.md")}
        self.assertEqual(actual, EXPECTED_DOCUMENTS)
        self.assertNotIn("glossary.md", actual)

    def test_japanese_intermediate_notices_use_portable_canonical_paths(self):
        for name in sorted(EXPECTED_DOCUMENTS):
            with self.subTest(document=name):
                text = (JA_BUILD / name).read_text(encoding="utf-8")
                match = CANONICAL_SOURCE.search(text)
                self.assertIsNotNone(match)
                canonical = match.group(1)
                self.assertTrue(canonical.startswith("dirpluck_docs/"), canonical)
                self.assertFalse(PurePosixPath(canonical).is_absolute(), canonical)
                windows_path = PureWindowsPath(canonical)
                self.assertFalse(windows_path.is_absolute(), canonical)
                self.assertFalse(windows_path.drive, canonical)


if __name__ == "__main__":
    unittest.main()
