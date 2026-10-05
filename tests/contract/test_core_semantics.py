from __future__ import annotations

from pathlib import Path
import textwrap
import unittest

from tests._temp import resolved_temporary_directory

import dirpluck


class CoreContractTests(unittest.TestCase):
    def _write_config(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def test_base_relative_always_path_is_anchored_to_declaring_configuration(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            (base / "refs").mkdir(parents=True)
            (base / "refs" / "note.txt").write_text("base\n", encoding="utf-8")
            self._write_config(
                base / "base.dirpluck",
                """
                [always.refs]
                path = "refs"
                must = ["note.txt"]
                """,
            )
            self._write_config(
                derived / "default.dirpluck",
                """
                [about]
                base = "../base/base.dirpluck"
                """,
            )

            result = dirpluck.run(config="derived/default.dirpluck", preview=True, cwd=root)

            self.assertEqual(result.archive_entries, ("README.md", "refs/note.txt"))

    def test_outer_shared_definition_rebinds_selection_inherited_from_base(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            project = base / "project"
            project.mkdir(parents=True)
            (project / "inner.txt").write_text("inner\n", encoding="utf-8")
            (project / "outer.txt").write_text("outer\n", encoding="utf-8")
            self._write_config(
                base / "base.dirpluck",
                """
                [shared.must]
                chosen = ["inner.txt"]

                [pluck]
                must = [{ shared = "chosen" }]

                [scope.base]
                path = "."
                """,
            )
            self._write_config(
                derived / "default.dirpluck",
                """
                [about]
                base = "../base/base.dirpluck"

                [shared.must]
                chosen = ["outer.txt"]
                """,
            )

            result = dirpluck.run(
                "base/project/",
                config="derived/default.dirpluck",
                preview=True,
                cwd=root,
            )

            self.assertIn("project/outer.txt", result.archive_entries)
            self.assertNotIn("project/inner.txt", result.archive_entries)

    def test_canonical_shared_match_and_path_ignore_compose(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            app = root / "app"
            (app / "src" / "generated").mkdir(parents=True)
            (app / "src" / "main.py").write_text("main\n", encoding="utf-8")
            (app / "src" / "notes.txt").write_text("notes\n", encoding="utf-8")
            (app / "src" / "generated" / "skip.py").write_text("skip\n", encoding="utf-8")
            self._write_config(
                root / "default.dirpluck",
                r"""
                [shared.must]
                python = [{ match = 'src/.*\.py' }]

                [pluck]
                must = [{ shared = "python" }]
                ignore = [{ path = "src/generated/" }]
                """,
            )

            result = dirpluck.run("./app/", preview=True, cwd=root)

            self.assertIn("app/src/main.py", result.archive_entries)
            self.assertNotIn("app/src/notes.txt", result.archive_entries)
            self.assertNotIn("app/src/generated/skip.py", result.archive_entries)

    def test_scope_namespace_and_both_target_selector_define_archive_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            (returned / "repo-dir" / "src").mkdir(parents=True)
            (returned / "repo-dir" / "src" / "main.py").write_text("x\n", encoding="utf-8")
            (returned / "repo-file.zip").write_bytes(b"zip")
            self._write_config(
                root / "default.dirpluck",
                """
                [namespace.review]

                [pluck]
                must = ["src/"]

                [scope.returned]
                path = "returned"
                target_kind = "both"
                namespace = "review"
                """,
            )

            result = dirpluck.run(
                "returned:<repo-.*/?>",
                preview=True,
                cwd=root,
            )

            self.assertIn("review/repo-dir/src/main.py", result.archive_entries)
            self.assertIn("review/repo-file.zip", result.archive_entries)

    def test_nested_directory_symlink_is_not_traversed(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            external = Path(other) / "external"
            external.mkdir()
            (external / "secret.txt").write_text("secret\n", encoding="utf-8")
            app = root / "app"
            (app / "src").mkdir(parents=True)
            (app / "src" / "main.py").write_text("main\n", encoding="utf-8")
            link = app / "src" / "external"
            try:
                link.symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            self._write_config(
                root / "default.dirpluck",
                """
                [pluck]
                must = ["src/"]
                """,
            )

            result = dirpluck.run("./app/", preview=True, cwd=root)

            self.assertIn("app/src/main.py", result.archive_entries)
            self.assertNotIn("app/src/external/secret.txt", result.archive_entries)
            self.assertEqual(result.skipped_link_count, 1)

    def test_archive_entry_collision_is_rejected_through_public_api(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "bundle"
            (project / "dist").mkdir(parents=True)
            (project / "dist" / "artifact.whl").write_bytes(b"target")
            external = Path(other) / "bundle"
            (external / "dist").mkdir(parents=True)
            (external / "dist" / "artifact.whl").write_bytes(b"always")
            self._write_config(
                root / "default.dirpluck",
                f"""
                [pluck]
                must = ["dist/"]

                [always.bundle]
                path = {external.as_posix()!r}
                must = ["dist/*.whl"]
                """,
            )

            with self.assertRaises(dirpluck.DirpluckError):
                dirpluck.run("./bundle/", preview=True, cwd=root)

    def test_output_archive_cannot_be_selected_as_an_input(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            app = root / "app"
            app.mkdir()
            (app / "out.zip").write_bytes(b"old")
            self._write_config(
                root / "default.dirpluck",
                """
                [pluck]
                must = ["*"]

                [output]
                path = "app/out.zip"
                overwrite = true
                """,
            )

            with self.assertRaises(dirpluck.DirpluckError):
                dirpluck.run("./app/", cwd=root)


if __name__ == "__main__":
    unittest.main()
