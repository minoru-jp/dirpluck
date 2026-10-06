from __future__ import annotations

from pathlib import Path
import textwrap
import unittest

from tests._temp import resolved_temporary_directory

import dirpluck


class ExtraContractTests(unittest.TestCase):
    def _write_config(self, root: Path, body: str) -> None:
        (root / "default.dirpluck").write_text(textwrap.dedent(body), encoding="utf-8")

    def test_extra_is_inactive_until_added_by_always_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for name, filename in (("base", "base.txt"), ("tools", "tool.txt")):
                directory = root / name
                directory.mkdir()
                (directory / filename).write_text(name, encoding="utf-8")
            self._write_config(
                root,
                """
                [always.base]
                path = "base"
                must = ["base.txt"]

                [extra.tools]
                path = "tools"
                description = "Optional tools."
                must = ["tool.txt"]

                [case.always.tools]
                add = ["tools"]
                """,
            )

            default = dirpluck.run(preview=True, cwd=root)
            selected = dirpluck.run(case=".tools", preview=True, cwd=root)

            self.assertEqual(default.archive_entries, ("README.md", "base/base.txt"))
            self.assertEqual(
                selected.archive_entries,
                ("README.md", "base/base.txt", "tools/tool.txt"),
            )
            self.assertNotIn("Optional tools.", default.archive_readme)
            self.assertIn("Optional tools.", selected.archive_readme)

    def test_always_case_include_may_select_only_extra_sources(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "base").mkdir()
            (root / "base" / "base.txt").write_text("base", encoding="utf-8")
            (root / "tools").mkdir()
            (root / "tools" / "tool.txt").write_text("tool", encoding="utf-8")
            self._write_config(
                root,
                """
                [always.base]
                path = "base"
                must = ["base.txt"]

                [extra.tools]
                path = "tools"
                must = ["tool.txt"]

                [case.always.tools-only]
                include = ["tools"]
                """,
            )

            result = dirpluck.run(case=".tools-only", preview=True, cwd=root)

            self.assertEqual(result.archive_entries, ("README.md", "tools/tool.txt"))

    def test_extra_uses_always_layout_and_counts_as_always_for_readme_state(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools" / "tool.txt").write_text("tool", encoding="utf-8")
            self._write_config(
                root,
                """
                [about]
                description_no_always = "NO ALWAYS"
                description_no_targets = "NO TARGETS"
                always_layout = "dependencies"

                [layout.dependencies]
                description = "Dependencies."

                [extra.tools]
                path = "tools"
                must = ["tool.txt"]

                [case.always.tools]
                add = ["tools"]
                """,
            )

            result = dirpluck.run(case=".tools", preview=True, cwd=root)

            self.assertEqual(
                result.archive_entries,
                ("README.md", "dependencies/tools/tool.txt"),
            )
            self.assertIn("NO TARGETS", result.archive_readme)
            self.assertNotIn("NO ALWAYS", result.archive_readme)
            self.assertIn("Dependencies.", result.archive_readme)

    def test_extra_layout_overrides_default_always_layout(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools" / "tool.txt").write_text("tool", encoding="utf-8")
            self._write_config(
                root,
                """
                [about]
                always_layout = "dependencies"

                [layout.dependencies]

                [layout.optional]

                [extra.tools]
                path = "tools"
                layout = "optional"
                must = ["tool.txt"]

                [case.always.tools]
                add = ["tools"]
                """,
            )

            result = dirpluck.run(case=".tools", preview=True, cwd=root)

            self.assertEqual(
                result.archive_entries,
                ("README.md", "optional/tools/tool.txt"),
            )

    def test_extra_may_be_defined_in_base_and_activated_by_root_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools" / "tool.txt").write_text("tool", encoding="utf-8")
            (root / "base.dirpluck").write_text(
                textwrap.dedent(
                    """
                    [extra.tools]
                    path = "tools"
                    must = ["tool.txt"]
                    """
                ),
                encoding="utf-8",
            )
            self._write_config(
                root,
                """
                [about]
                base = "base.dirpluck"

                [case.always.tools]
                add = ["tools"]
                """,
            )

            result = dirpluck.run(case=".tools", preview=True, cwd=root)

            self.assertEqual(result.archive_entries, ("README.md", "tools/tool.txt"))

    def test_selected_extra_participates_in_final_archive_root_collision_checks(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "fixed").mkdir()
            (root / "fixed" / "note.txt").write_text("fixed", encoding="utf-8")
            target = root / "targets" / "tools"
            target.mkdir(parents=True)
            (target / "note.txt").write_text("target", encoding="utf-8")
            self._write_config(
                root,
                """
                [extra.tools]
                path = "fixed"
                must = ["note.txt"]

                [case.always.tools]
                add = ["tools"]

                [scope.projects]
                path = "targets"

                [pluck]
                must = ["note.txt"]
                """,
            )

            with self.assertRaises(dirpluck.DirpluckError):
                dirpluck.run("projects/tools/", case=".tools", preview=True, cwd=root)

    def test_include_cannot_be_combined_with_delta_fields(self):
        for field in ("add", "exclude"):
            with self.subTest(field=field), resolved_temporary_directory() as temp:
                root = Path(temp)
                self._write_config(
                    root,
                    f"""
                    [case.always.invalid]
                    include = []
                    {field} = []
                    """,
                )

                with self.assertRaisesRegex(dirpluck.DirpluckError, "mutually exclusive"):
                    dirpluck.run(case=".invalid", preview=True, cwd=root)

    def test_add_accepts_only_extra_sources(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "base").mkdir()
            self._write_config(
                root,
                """
                [always.base]
                path = "base"
                may = ["*.txt"]
                allow_empty = true

                [case.always.invalid]
                add = ["base"]
                """,
            )

            with self.assertRaisesRegex(dirpluck.DirpluckError, "add accepts Extra sources only"):
                dirpluck.run(case=".invalid", preview=True, cwd=root)

    def test_exclude_accepts_only_always_sources(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            self._write_config(
                root,
                """
                [extra.tools]
                path = "tools"
                may = ["*.txt"]
                allow_empty = true

                [case.always.invalid]
                exclude = ["tools"]
                """,
            )

            with self.assertRaisesRegex(
                dirpluck.DirpluckError, "exclude accepts Always sources only"
            ):
                dirpluck.run(case=".invalid", preview=True, cwd=root)

    def test_add_and_exclude_form_a_delta_over_default_always_sources(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for name in ("base", "optional", "tools"):
                directory = root / name
                directory.mkdir()
                (directory / f"{name}.txt").write_text(name, encoding="utf-8")
            self._write_config(
                root,
                """
                [always.base]
                path = "base"
                must = ["base.txt"]

                [always.optional]
                path = "optional"
                must = ["optional.txt"]

                [extra.tools]
                path = "tools"
                must = ["tools.txt"]

                [case.always.delta]
                add = ["tools"]
                exclude = ["optional"]
                """,
            )

            result = dirpluck.run(case=".delta", preview=True, cwd=root)

            self.assertEqual(
                result.archive_entries,
                ("README.md", "base/base.txt", "tools/tools.txt"),
            )


if __name__ == "__main__":
    unittest.main()
