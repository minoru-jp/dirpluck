from __future__ import annotations

from pathlib import Path
import textwrap
import unittest

from tests._temp import resolved_temporary_directory

import dirpluck


class ChangedContractTests(unittest.TestCase):
    def _write_config(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")

    def test_distinct_scopes_may_resolve_to_the_same_filesystem_root(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "repos" / "app"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("x\n", encoding="utf-8")
            self._write_config(
                root / "default.dirpluck",
                """
                [pluck]
                must = ["src/"]

                [scope.foo]
                path = "repos"

                [scope.bar]
                path = "repos"
                """,
            )

            result = dirpluck.run("foo/app/", preview=True, cwd=root)

            self.assertIn("app/src/main.py", result.archive_entries)

    def test_inactive_base_output_does_not_conflict_with_root_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._write_config(
                root / "base.dirpluck",
                """
                [output.timestamp]
                path = "artifacts/"
                """,
            )
            self._write_config(
                root / "default.dirpluck",
                """
                [about]
                base = "base.dirpluck"

                [output]
                path = "artifacts/result.zip"
                """,
            )

            result = dirpluck.run(preview=True, cwd=root)

            self.assertEqual(result.archive_entries, ("README.md",))


if __name__ == "__main__":
    unittest.main()
