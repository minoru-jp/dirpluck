from pathlib import Path
import unittest

from tests._builder_support import BuilderTestCase
from tests._temp import resolved_temporary_directory

from dirpluck._builder_models import BuildRequest
from dirpluck._effective import resolve_sources
from dirpluck._selection import select_files
from dirpluck.errors import SelectionError


class StrictEntryTypeTests(BuilderTestCase):
    def test_string_selection_requires_trailing_slash_for_directory_leaf(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "app" / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("x", encoding="utf-8")

            file_form = self._config(
                root,
                """
                [pluck]
                must = ["src"]
            """,
            )
            source = resolve_sources(file_form, BuildRequest.create("./app/"))[0]
            with self.assertRaisesRegex(SelectionError, "add a trailing '/'"):
                select_files(source)

            directory_form = self._config(
                root,
                """
                [pluck]
                must = ["src/"]
            """,
            )
            source = resolve_sources(directory_form, BuildRequest.create("./app/"))[0]
            self.assertEqual(
                [
                    path.relative_to(source.directory).as_posix()
                    for path in select_files(source).files
                ],
                ["src/main.py"],
            )

    def test_optional_wrong_type_keeps_may_semantics_and_reports_diagnostic(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "app" / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("x", encoding="utf-8")
            (root / "app" / "README.md").write_text("readme", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["README.md"]
                may = ["src"]
            """,
            )

            source = resolve_sources(config, BuildRequest.create("./app/"))[0]
            result = select_files(source)
            self.assertEqual(
                [path.relative_to(source.directory).as_posix() for path in result.files],
                ["README.md"],
            )
            self.assertEqual(result.optional_missing, ("src",))
            self.assertEqual(len(result.diagnostics), 1)
            self.assertIn("directory 'src/' exists", result.diagnostics[0])
            self.assertIn("add a trailing '/'", result.diagnostics[0])

    def test_required_wrong_type_preview_reports_diagnostic_without_changing_missing_semantics(
        self,
    ):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "app" / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src"]
            """,
            )

            source = resolve_sources(config, BuildRequest.create("./app/"))[0]
            result = select_files(source, allow_missing=True)
            self.assertEqual(result.missing, ("src",))
            self.assertEqual(len(result.diagnostics), 1)
            self.assertIn("target: file pattern 'src' did not match", result.diagnostics[0])
            self.assertIn("add a trailing '/'", result.diagnostics[0])

    def test_required_wrong_type_error_uses_source_colon_grammar(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            config = self._config(
                root,
                """
                [pluck]
                must = ["src"]
            """,
            )

            source = resolve_sources(config, BuildRequest.create("./app/"))[0]
            with self.assertRaises(SelectionError) as caught:
                select_files(source)
            message = str(caught.exception)
            self.assertIn("target: file pattern 'src' did not match", message)
            self.assertNotIn("target has file pattern", message)

    def test_literal_target_wrong_type_error_suggests_directory_marker(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "mixed" / "project" / "src").mkdir(parents=True)
            (root / "mixed" / "project" / "src" / "main.py").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            with self.assertRaisesRegex(SelectionError, "add a trailing '/'"):
                resolve_sources(config, BuildRequest.create("mixed/project"))

    def test_literal_target_reference_encodes_entry_type(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            (mixed / "project" / "src").mkdir(parents=True)
            (mixed / "project" / "src" / "main.py").write_text("x", encoding="utf-8")
            (mixed / "artifact.zip").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            directory = resolve_sources(config, BuildRequest.create("mixed/project/"))[0]
            file_source = resolve_sources(config, BuildRequest.create("mixed/artifact.zip"))[0]
            self.assertEqual(directory.source_kind, "directory")
            self.assertEqual(file_source.source_kind, "file")
            with self.assertRaisesRegex(SelectionError, "not a regular file"):
                resolve_sources(config, BuildRequest.create("mixed/project"))
            with self.assertRaisesRegex(SelectionError, "not a directory"):
                resolve_sources(config, BuildRequest.create("mixed/artifact.zip/"))

    def test_default_scope_directory_target_uses_dot_slash_form(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "project" / "src").mkdir(parents=True)
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]
            """,
            )

            source = resolve_sources(config, BuildRequest.create("./project/"))[0]
            self.assertEqual((source.source_root, source.source_kind), ("project", "directory"))
            with self.assertRaisesRegex(SelectionError, "Scope 'project' is not defined"):
                resolve_sources(config, BuildRequest.create("project/"))

    def test_target_list_uses_double_slash_for_directory_item_plus_separator(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            mixed.mkdir()
            (mixed / "a.zip").write_bytes(b"a")
            for name in ("project", "other"):
                (mixed / name / "src").mkdir(parents=True)
                (mixed / name / "src" / "main.py").write_text(name, encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("mixed:[a.zip/project//other/]"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in sources],
                [("a.zip", "file"), ("project", "directory"), ("other", "directory")],
            )
            with self.assertRaisesRegex(SelectionError, "three or more consecutive"):
                resolve_sources(config, BuildRequest.create("mixed:[a.zip///project]"))

    def test_target_regex_matches_normalized_file_and_directory_names(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            mixed.mkdir()
            (mixed / "repo-file").write_bytes(b"file")
            (mixed / "repo-dir" / "src").mkdir(parents=True)
            (mixed / "repo-dir" / "src" / "main.py").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            both = resolve_sources(config, BuildRequest.create(r"mixed:<repo-(file|dir)/?>"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in both],
                [("repo-dir", "directory"), ("repo-file", "file")],
            )
            only_file = resolve_sources(config, BuildRequest.create(r"mixed:<repo-file>"))
            self.assertEqual(
                [(s.source_root, s.source_kind) for s in only_file], [("repo-file", "file")]
            )
            only_directory = resolve_sources(config, BuildRequest.create(r"mixed:<repo-dir/>"))
            self.assertEqual(
                [(s.source_root, s.source_kind) for s in only_directory],
                [("repo-dir", "directory")],
            )

    def test_scope_ignore_without_trailing_slash_is_broad(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            mixed.mkdir()
            (mixed / "skip.zip").write_bytes(b"skip")
            (mixed / "skip-dir" / "src").mkdir(parents=True)
            (mixed / "skip-dir" / "src" / "x.py").write_text("x", encoding="utf-8")
            (mixed / "keep.zip").write_bytes(b"keep")
            (mixed / "old" / "src").mkdir(parents=True)
            (mixed / "old" / "src" / "x.py").write_text("x", encoding="utf-8")
            (mixed / "keep-dir" / "src").mkdir(parents=True)
            (mixed / "keep-dir" / "src" / "x.py").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
                ignore = ["skip*", "old/"]
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("mixed/"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in sources],
                [("keep-dir", "directory"), ("keep.zip", "file")],
            )

    def test_scope_ignore_with_trailing_slash_is_directory_only(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            mixed.mkdir()
            (mixed / "skip.zip").write_bytes(b"keep")
            (mixed / "skip-dir" / "src").mkdir(parents=True)
            (mixed / "skip-dir" / "src" / "x.py").write_text("drop", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
                ignore = ["skip*/"]
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("mixed/"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in sources],
                [("skip.zip", "file")],
            )

    def test_structured_match_can_explicitly_match_file_or_directory_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            app = root / "app"
            app.mkdir()
            (app / "leaf").write_text("file", encoding="utf-8")
            (app / "tree").mkdir()
            (app / "tree" / "child.txt").write_text("child", encoding="utf-8")
            config = self._config(
                root,
                r"""
                [pluck]
                must = [{ match = '(leaf|tree)/?' }]
            """,
            )
            source = resolve_sources(config, BuildRequest.create("./app/"))[0]
            selected = [
                path.relative_to(source.directory).as_posix() for path in select_files(source).files
            ]
            self.assertEqual(selected, ["leaf", "tree/child.txt"])


if __name__ == "__main__":
    unittest.main()
