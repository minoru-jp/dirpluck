from __future__ import annotations

from pathlib import Path
import textwrap
import unittest

from tests._temp import resolved_temporary_directory

import dirpluck


class LayoutContractTests(unittest.TestCase):
    def _write_config(self, path: Path, body: str) -> None:
        path.write_text(textwrap.dedent(body), encoding="utf-8")

    def _workspace(self, root: Path) -> None:
        wheels = root / "wheelhouse"
        wheels.mkdir()
        (wheels / "tool.whl").write_bytes(b"wheel")
        app = root / "repos" / "app"
        (app / "src").mkdir(parents=True)
        (app / "src" / "main.py").write_text("print('app')\n", encoding="utf-8")

    def test_layout_controls_public_archive_paths_and_readme(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            self._write_config(
                root / "default.dirpluck",
                """
                [about]
                description = "Development bundle."
                always_layout = "dependencies"
                targets_layout = "development-targets"

                [layout.dependencies]
                description = "Fixed development dependencies."

                [layout.development-targets]
                description = "Selected development targets."

                [always.wheels]
                path = "wheelhouse"
                must = ["*.whl"]

                [scope.projects]
                path = "repos"

                [pluck]
                must = ["src/"]
                """,
            )

            result = dirpluck.run("projects/app/", preview=True, cwd=root)

            self.assertEqual(
                result.archive_entries,
                (
                    "README.md",
                    "dependencies/wheels/tool.whl",
                    "development-targets/app/src/main.py",
                ),
            )
            self.assertIn("Development bundle.", result.archive_readme)
            self.assertIn("## Layouts", result.archive_readme)
            self.assertIn("`dependencies/`", result.archive_readme)
            self.assertIn("Fixed development dependencies.", result.archive_readme)
            self.assertIn("`development-targets/`", result.archive_readme)
            self.assertIn("Selected development targets.", result.archive_readme)

    def test_layout_conditional_descriptions_follow_resolved_source_roles(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            self._write_config(
                root / "default.dirpluck",
                """
                [about]
                description = "Always visible."
                description_no_targets = "NO TARGETS"
                description_no_always = "NO ALWAYS"
                description_empty = "EMPTY"
                always_layout = "fixed"

                [layout.fixed]

                [always.wheels]
                path = "wheelhouse"
                must = ["*.whl"]

                [case.always.none]
                include = []

                [scope.projects]
                path = "repos"

                [pluck]
                must = ["src/"]
                """,
            )

            always_only = dirpluck.run(preview=True, cwd=root)
            target_only = dirpluck.run("projects/app/", case=".none", preview=True, cwd=root)
            empty = dirpluck.run(case=".none", preview=True, cwd=root)
            both = dirpluck.run("projects/app/", preview=True, cwd=root)

            for result in (always_only, target_only, empty, both):
                self.assertIn("Always visible.", result.archive_readme)

            self.assertIn("NO TARGETS", always_only.archive_readme)
            self.assertNotIn("NO ALWAYS", always_only.archive_readme)
            self.assertNotIn("EMPTY", always_only.archive_readme)

            self.assertIn("NO ALWAYS", target_only.archive_readme)
            self.assertNotIn("NO TARGETS", target_only.archive_readme)
            self.assertNotIn("EMPTY", target_only.archive_readme)

            self.assertIn("EMPTY", empty.archive_readme)
            self.assertNotIn("NO TARGETS", empty.archive_readme)
            self.assertNotIn("NO ALWAYS", empty.archive_readme)
            self.assertEqual(empty.archive_entries, ("README.md",))

            self.assertNotIn("NO TARGETS", both.archive_readme)
            self.assertNotIn("NO ALWAYS", both.archive_readme)
            self.assertNotIn("EMPTY", both.archive_readme)

    def test_unknown_layout_reference_is_rejected_through_public_api(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._write_config(
                root / "default.dirpluck",
                """
                [about]
                targets_layout = "missing"
                """,
            )

            with self.assertRaises(dirpluck.DirpluckError):
                dirpluck.run(preview=True, cwd=root)

    def test_layout_final_archive_root_collision_is_rejected_through_public_api(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            fixed = root / "fixed"
            fixed.mkdir()
            (fixed / "note.txt").write_text("fixed\n", encoding="utf-8")
            self._write_config(
                root / "default.dirpluck",
                """
                [layout.shared]

                [always.app]
                path = "fixed"
                layout = "shared"
                must = ["note.txt"]

                [scope.projects]
                path = "repos"
                layout = "shared"

                [pluck]
                must = ["src/"]
                """,
            )

            with self.assertRaises(dirpluck.DirpluckError):
                dirpluck.run("projects/app/", preview=True, cwd=root)


if __name__ == "__main__":
    unittest.main()
