from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import os
import textwrap
import unittest
import warnings
from unittest.mock import patch
import zipfile

from tests._temp import resolved_temporary_directory

from dirpluck import ConfigurationDeprecationWarning, __version__
from dirpluck.cli import main


CONFIG = """
[pluck]
description = "Default development target."
must = ["src/"]

[pluck.case.review]
description = "Review target."
must = ["tests/"]

[scope]

[always.framework]
path = "framework"
description = "Fixed framework."
must = ["src/"]

[output]
path = "result.zip"
overwrite = false
"""


class CliTests(unittest.TestCase):
    def _workspace(self, root: Path, *, config_path: str = "default.dirpluck") -> None:
        app = root / "app"
        framework = root / "framework"
        (app / "src").mkdir(parents=True)
        (app / "tests").mkdir()
        (framework / "src").mkdir(parents=True)
        (app / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
        (app / "tests" / "test_app.py").write_text("TEST = 1\n", encoding="utf-8")
        (framework / "src" / "core.py").write_text("CORE = 1\n", encoding="utf-8")
        path = root / config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(CONFIG), encoding="utf-8")

    def test_version_reports_package_version(self):
        output = StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            main(["--version"])
        self.assertEqual(caught.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"dirpluck {__version__}")

    def test_deprecated_nested_selection_reference_warns_once_per_config_file(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            app = root / "app"
            (app / "src").mkdir(parents=True)
            (app / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(r"""
                [shared.must]
                required = ["src/"]

                [shared.may]
                optional = ["README.md"]

                [shared.ignore]
                noise = ["*.pyc"]

                [pluck]
                must = [["required"]]
                may = [["optional"]]
                ignore = [["noise"], ["./tests/"]]

                [scope]

                [output]
                path = "result.zip"
            """),
                encoding="utf-8",
            )

            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", ConfigurationDeprecationWarning)
                    with redirect_stdout(StringIO()), redirect_stderr(stderr):
                        result = main(["./app/"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            self.assertFalse(
                any(
                    issubclass(warning.category, ConfigurationDeprecationWarning)
                    for warning in caught
                )
            )
            warning = stderr.getvalue()
            self.assertEqual(warning.count("dirpluck: warning:"), 1)
            self.assertIn("deprecated nested-array Selection reference syntax", warning)
            self.assertIn("1.0.0", warning)
            self.assertIn('{ shared = "..." }', warning)
            self.assertIn('{ path = "..." }', warning)

    def test_deprecated_nested_selection_reference_in_base_config_warns(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            app = root / "app"
            (app / "src").mkdir(parents=True)
            (app / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "base.dirpluck").write_text(
                textwrap.dedent(r"""
                [shared.must]
                required = ["src/"]

                [pluck]
                must = [["required"]]

                [scope]
            """),
                encoding="utf-8",
            )
            (root / "default.dirpluck").write_text(
                textwrap.dedent(r"""
                [about]
                base = "base.dirpluck"

                [output]
                path = "result.zip"
            """),
                encoding="utf-8",
            )

            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    result = main(["./app/"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            warning = stderr.getvalue()
            self.assertEqual(warning.count("dirpluck: warning:"), 1)
            self.assertIn("base.dirpluck", warning)
            self.assertIn("1.0.0", warning)

    def test_direct_invocation_uses_default_target_and_configured_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertEqual(names, {"README.md", "app/src/app.py", "framework/src/core.py"})

    def test_file_target_scope_bundles_returned_archives_with_always_source(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            guidelines = root / "guidelines"
            returned.mkdir()
            guidelines.mkdir()
            (returned / "repo-a.zip").write_bytes(b"a")
            (returned / "repo-b.zip").write_bytes(b"b")
            (guidelines / "rules.md").write_text("rules\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [namespace.returned]

                [scope.returned]
                path = "returned"
                target_kind = "file"
                namespace = "returned"
                description = "Repositories returned from the previous editing cycle."

                [always.guidelines]
                path = "guidelines"
                description = "Guidelines used for the next pass."
                must = ["rules.md"]

                [output]
                path = "result.zip"
            """),
                encoding="utf-8",
            )

            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["returned/"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "README.md",
                        "returned/repo-a.zip",
                        "returned/repo-b.zip",
                        "guidelines/rules.md",
                    },
                )
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `returned/repo-a.zip`", readme)
            self.assertIn("Repositories returned from the previous editing cycle.", readme)
            self.assertIn("Guidelines used for the next pass.", readme)

    def test_file_target_regex_selector_is_accepted_by_cli(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "repo-a.zip").write_bytes(b"a")
            (returned / "repo-b.zip").write_bytes(b"b")
            (returned / "notes.txt").write_text("notes\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [scope.returned]
                path = "returned"
                target_kind = "file"

                [output]
                path = "result.zip"
            """),
                encoding="utf-8",
            )

            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main([r"returned:<.*\.zip>"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"README.md", "repo-a.zip", "repo-b.zip"},
                )

    def test_archive_write_oserror_is_reported_without_traceback(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch.object(zipfile.ZipFile, "write", side_effect=PermissionError("denied")),
                    redirect_stderr(stderr),
                    self.assertRaises(SystemExit) as caught,
                ):
                    main(["./app/"])
            finally:
                os.chdir(previous)

            self.assertEqual(caught.exception.code, 2)
            self.assertIn(
                "dirpluck: error: cannot add selected file to archive:",
                stderr.getvalue(),
            )
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertFalse((root / "result.zip").exists())
            self.assertEqual(list(root.glob(".result.zip.*.tmp")), [])

    def test_multiple_target_directories_are_accepted(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            app_two = root / "./app-two/"
            (app_two / "src").mkdir(parents=True)
            (app_two / "tests").mkdir()
            (app_two / "src" / "app.py").write_text("APP = 2\n", encoding="utf-8")
            (app_two / "tests" / "test_app.py").write_text("TEST = 2\n", encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "./app-two/"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/src/app.py", names)
            self.assertIn("app-two/src/app.py", names)
            self.assertIn("framework/src/core.py", names)

    def test_case_applies_to_all_target_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            app_two = root / "./app-two/"
            (app_two / "src").mkdir(parents=True)
            (app_two / "tests").mkdir()
            (app_two / "src" / "app.py").write_text("APP = 2\n", encoding="utf-8")
            (app_two / "tests" / "test_app.py").write_text("TEST = 2\n", encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "./app-two/", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/tests/test_app.py", names)
            self.assertIn("app-two/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)
            self.assertNotIn("app-two/src/app.py", names)

    def test_default_config_is_not_searched_in_dot_dirpluck_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = root / ".dirpluck" / "default.dirpluck"
            config.parent.mkdir()
            config.write_text(CONFIG, encoding="utf-8")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main([])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("configuration file was not found", stderr.getvalue())
            self.assertIn("default.dirpluck", stderr.getvalue())

    def test_explicit_dot_dirpluck_config_uses_its_own_directory_as_default_scope(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            app = root / ".dirpluck" / "app"
            (app / "src").mkdir(parents=True)
            (app / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            config = root / ".dirpluck" / "default.dirpluck"
            config.write_text(
                textwrap.dedent("""
                [pluck]
                description = "Default development target."
                must = ["src/"]

                [output]
                path = "result.zip"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--config", ".dirpluck/default"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / ".dirpluck" / "result.zip") as archive:
                self.assertIn("app/src/app.py", archive.namelist())

    def test_single_named_config_is_not_implicit_default(self):
        for config_path in ("release.dirpluck", ".dirpluck/release.dirpluck"):
            with self.subTest(config_path=config_path), resolved_temporary_directory() as temp:
                root = Path(temp)
                self._workspace(root, config_path=config_path)
                stderr = StringIO()
                previous = Path.cwd()
                try:
                    os.chdir(root)
                    with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                        main(["./app/"])
                finally:
                    os.chdir(previous)
                self.assertEqual(caught.exception.code, 2)
                self.assertIn(
                    "configuration file was not found",
                    stderr.getvalue(),
                )

    def test_legacy_dirpluck_toml_is_not_an_implicit_default(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="dirpluck.toml")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("configuration file was not found", stderr.getvalue())

    def test_dot_dirpluck_default_is_not_considered_implicitly(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / ".dirpluck").mkdir()
            (root / ".dirpluck" / "default.dirpluck").write_text(CONFIG, encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_case_selects_named_target_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("app/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)
            self.assertIn("framework/src/core.py", names)
            self.assertIn("## `app/`\n\nFiles: 1\n\nReview target.", readme)
            self.assertNotIn("Case:", readme)

    def test_paths_adds_source_column_to_archive_readme(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--paths"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn(f"Source: `{(root / 'app').resolve().as_posix()}`", readme)
            self.assertIn(f"Source: `{(root / 'framework').resolve().as_posix()}`", readme)

    def test_unknown_case_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            stderr = StringIO()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/", "--case", "release"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("case 'release' is not defined", stderr.getvalue())

    def test_always_only_configuration_runs_without_target(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            (root / "documents" / "a.md").write_text("A", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.documents]
                path = "documents"
                description = "Documents."
                must = ["*.md"]

                [output]
                path = "result.zip"
                overwrite = false
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main([])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertEqual(set(archive.namelist()), {"README.md", "documents/a.md"})

    def test_directory_is_rejected_when_configuration_has_no_target(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.documents]
                path = "documents"
                description = "Documents."
                may = ["*.md"]
                allow_empty = true

                [output]
                path = "result.zip"
                overwrite = false
            """),
                encoding="utf-8",
            )
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./documents/"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("TARGET must not be specified", stderr.getvalue())

    def test_directory_is_required_when_configuration_defines_target(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main([])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("TARGET is required", stderr.getvalue())

    def test_always_case_is_selected_and_missing_case_falls_back_to_default(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "documents" / "current").mkdir(parents=True)
            (root / "documents" / "archive").mkdir()
            (root / "documents" / "current" / "now.md").write_text("now", encoding="utf-8")
            (root / "documents" / "archive" / "old.md").write_text("old", encoding="utf-8")
            (root / "assets").mkdir()
            (root / "assets" / "figure.txt").write_text("figure", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.documents]
                path = "documents"
                description = "Current documents."
                must = ["current/"]

                [always.documents.case.archive]
                description = "Archived documents."
                must = ["current/", "archive/"]

                [always.assets]
                path = "assets"
                description = "Assets."
                must = ["*.txt"]

                [output]
                path = "result.zip"
                overwrite = false
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["--case", "archive"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("documents/archive/old.md", names)
            self.assertIn("assets/figure.txt", names)
            self.assertIn("## `documents/`\n\nFiles: 2\n\nArchived documents.", readme)
            self.assertIn("## `assets/`\n\nFiles: 1\n\nAssets.", readme)
            self.assertNotIn("companion", readme.lower())

    def test_case_option_cannot_be_repeated(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["./app/", "--case", "review", "--case", "release"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--case may be specified at most once", stderr.getvalue())

    def test_sequence_must_be_positive_integer(self):
        for value in ("0", "-1", "x"):
            with self.subTest(value=value):
                stderr = StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/", "--sequence", value])
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("integer greater than or equal to 1", stderr.getvalue())

    def test_archive_mtime_option_cannot_be_repeated(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(
                [
                    "app",
                    "--archive-mtime",
                    "zip-epoch",
                    "--archive-mtime",
                    "now",
                ]
            )
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--archive-mtime may be specified at most once", stderr.getvalue())

    def test_invalid_archive_mtime_is_reported_without_traceback(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--archive-mtime", "1970-01-01T00:00:00", "--preview"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("archive mtime timestamp must be within", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_sequence_option_cannot_be_repeated(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["./app/", "--sequence", "1", "--sequence", "2"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--sequence may be specified at most once", stderr.getvalue())

    def test_preview_and_build_report_skipped_symbolic_links(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            app_link = root / "app" / "src" / "linked.py"
            framework_link = root / "framework" / "src" / "linked.py"
            try:
                app_link.symlink_to(root / "app" / "tests" / "test_app.py")
                framework_link.symlink_to(root / "app" / "tests" / "test_app.py")
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            previous = Path.cwd()
            try:
                os.chdir(root)
                preview_output = StringIO()
                with redirect_stdout(preview_output):
                    result = main(["./app/", "--preview"])
                self.assertEqual(result, 0)
                self.assertIn(
                    "Note: 2 link-like filesystem entries (symbolic links or Windows junctions) "
                    + "were skipped and will not be archived.",
                    preview_output.getvalue(),
                )
                self.assertFalse((root / "result.zip").exists())

                build_output = StringIO()
                with redirect_stdout(build_output):
                    result = main(["./app/"])
                self.assertEqual(result, 0)
                self.assertIn(
                    "Note: 2 link-like filesystem entries (symbolic links or Windows junctions) "
                    + "were skipped and not archived.",
                    build_output.getvalue(),
                )
                with zipfile.ZipFile(root / "result.zip") as archive:
                    names = set(archive.namelist())
                self.assertNotIn("app/src/linked.py", names)
                self.assertNotIn("framework/src/linked.py", names)
            finally:
                os.chdir(previous)

    def test_ignored_symbolic_links_do_not_produce_skip_note(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            manifest = root / "default.dirpluck"
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace(
                    'must = ["src/"]',
                    'must = ["src/"]\nignore = ["linked.py"]',
                ),
                encoding="utf-8",
            )
            app_link = root / "app" / "src" / "linked.py"
            framework_link = root / "framework" / "src" / "linked.py"
            try:
                app_link.symlink_to(root / "app" / "tests" / "test_app.py")
                framework_link.symlink_to(root / "app" / "tests" / "test_app.py")
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            previous = Path.cwd()
            try:
                os.chdir(root)
                preview_output = StringIO()
                with redirect_stdout(preview_output):
                    result = main(["./app/", "--preview"])
                self.assertEqual(result, 0)
                self.assertNotIn("link-like filesystem", preview_output.getvalue())

                build_output = StringIO()
                with redirect_stdout(build_output):
                    result = main(["./app/"])
                self.assertEqual(result, 0)
                self.assertNotIn("link-like filesystem", build_output.getvalue())
                with zipfile.ZipFile(root / "result.zip") as archive:
                    names = set(archive.namelist())
                self.assertNotIn("app/src/linked.py", names)
                self.assertNotIn("framework/src/linked.py", names)
            finally:
                os.chdir(previous)

    def test_preview_prints_tree_without_creating_zip(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["./app/", "--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertFalse((root / "result.zip").exists())
            self.assertEqual(
                stdout.getvalue().strip(),
                "\n".join(
                    [
                        "├── README.md",
                        "├── app/",
                        "│   └── src/",
                        "│       └── app.py",
                        "└── framework/",
                        "    └── src/",
                        "        └── core.py",
                    ]
                ),
            )

    def test_wrong_type_may_diagnostic_is_reported_for_preview_and_build(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x", encoding="utf-8")
            (root / "app" / "README.md").write_text("readme", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                    [pluck]
                    must = ["README.md"]
                    may = ["src"]

                    [output]
                    path = "result.zip"
                    overwrite = false
                """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                for arguments in (["./app/", "--preview"], ["./app/"]):
                    stderr = StringIO()
                    with redirect_stdout(StringIO()), redirect_stderr(stderr):
                        result = main(arguments)
                    self.assertEqual(result, 0)
                    self.assertIn("dirpluck: warning:", stderr.getvalue())
                    self.assertIn("directory 'src/' exists", stderr.getvalue())
                    self.assertIn("add a trailing '/'", stderr.getvalue())
            finally:
                os.chdir(previous)

    def test_wrong_type_must_diagnostic_is_reported_during_preview(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                    [pluck]
                    must = ["src"]
                    """
                ),
                encoding="utf-8",
            )
            previous = Path.cwd()
            stdout = StringIO()
            stderr = StringIO()
            try:
                os.chdir(root)
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = main(["./app/", "--preview"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            self.assertIn("src [missing]", stdout.getvalue())
            self.assertIn(
                "dirpluck: warning: target: file pattern 'src' did not match", stderr.getvalue()
            )
            self.assertIn("add a trailing '/'", stderr.getvalue())

    def test_paths_can_be_combined_with_preview_without_changing_tree_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["./app/", "--preview", "--paths"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertFalse((root / "result.zip").exists())
            self.assertIn("README.md", stdout.getvalue())
            self.assertNotIn(root.as_posix(), stdout.getvalue())

    def test_preview_does_not_apply_existing_output_policy(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            output = root / "result.zip"
            output.write_bytes(b"existing")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertEqual(output.read_bytes(), b"existing")

    def test_help_describes_target_reference_forms_and_preview(self):
        stdout = StringIO()
        with redirect_stdout(stdout), self.assertRaises(SystemExit) as caught:
            main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        text = stdout.getvalue()
        normalized = " ".join(text.split())
        self.assertIn("NAME or ./NAME (default file)", normalized)
        self.assertIn("./NAME/ (default directory)", normalized)
        self.assertIn("SCOPE/NAME (named file)", normalized)
        self.assertIn("SCOPE/NAME/ (named directory)", normalized)
        self.assertIn("/ or SCOPE/ (Scope expansion)", normalized)
        self.assertIn(":[...] / SCOPE:[...]", normalized)
        self.assertIn(":<REGEX> / SCOPE:<REGEX>", normalized)
        self.assertIn("--preview", text)
        self.assertNotIn("--dry-run", text)

    def test_removed_dry_run_option_is_rejected(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--dry-run"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("unrecognized arguments: --dry-run", stderr.getvalue())

    def test_named_config_path_in_cwd_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="review.dirpluck")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--config", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_nested_config_path_is_supported_explicitly(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            data = root / "data"
            data.mkdir()
            (data / "x").write_text("x", encoding="utf-8")
            config = root / ".dirpluck" / "review.dirpluck"
            config.parent.mkdir()
            config.write_text(
                textwrap.dedent("""
                [always.data]
                path = "../data"
                description = "Data."
                must = ["x"]

                [output]
                path = "../result.zip"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["--config", ".dirpluck/review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_named_config_name_may_contain_dots_without_suffix(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="release-1.2.dirpluck")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--config", "release-1.2"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_named_config_path_does_not_search_other_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="review.dirpluck")
            (root / ".dirpluck").mkdir()
            (root / ".dirpluck" / "review.dirpluck").write_text(CONFIG, encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--config", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_config_path_may_include_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root, config_path=".dirpluck/review.dirpluck")
            nested = root / ".dirpluck"
            (nested / "app" / "src").mkdir(parents=True)
            (nested / "framework" / "src").mkdir(parents=True)
            (nested / "app" / "src" / "app.py").write_text("APP = 2\n", encoding="utf-8")
            (nested / "framework" / "src" / "core.py").write_text(
                "CORE = 2\n",
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--config", ".dirpluck/review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((nested / "result.zip").is_file())

    def test_invocation_template_reuses_targets_and_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
                case = "review"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "release"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)

    def test_invocation_template_name_may_contain_dots_without_suffix(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "set-2.1.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "set-2.1"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)

    def test_invocation_template_long_option_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["--invocation-template", "release"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)

    def test_invocation_template_path_may_include_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            invocation = root / ".dirpluck" / "release.dirpluck-inv"
            invocation.parent.mkdir()
            invocation.write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", ".dirpluck/release"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)

    def test_invocation_config_is_relative_to_invocation_document(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            data = root / "data"
            data.mkdir()
            (data / "x").write_text("x", encoding="utf-8")
            dot_dir = root / ".dirpluck"
            dot_dir.mkdir()
            (dot_dir / "snapshot.dirpluck").write_text(
                textwrap.dedent("""
                [always.data]
                path = "../data"
                description = "Data."
                must = ["x"]

                [output]
                path = "../snapshot.zip"
            """),
                encoding="utf-8",
            )
            (dot_dir / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                config = "snapshot"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", ".dirpluck/release"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "snapshot.zip").is_file())

    def test_invocation_without_config_uses_cwd_default_configuration(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            invocation = root / ".dirpluck" / "release.dirpluck-inv"
            invocation.parent.mkdir()
            invocation.write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", ".dirpluck/release"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_invocation_template_does_not_apply_implicitly(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "default.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./missing/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)

    def test_named_invocation_entry_is_selected_with_entry_option(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]

                [invocation.review]
                targets = ["./app/"]
                case = "review"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "release", "-e", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)

    def test_entry_long_option_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation.review]
                targets = ["./app/"]
                case = "review"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "release", "--entry", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)

    def test_entry_requires_invocation_template(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--entry", "review"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--entry requires --invocation-template", stderr.getvalue())

    def test_unknown_invocation_entry_is_reported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text("[invocation]\n", encoding="utf-8")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["-i", "release", "-e", "missing"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("invocation entry was not found: missing", stderr.getvalue())

    def test_implicit_empty_default_invocation_is_valid_and_noted(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.data]
                path = "data"
                description = "Data."
                must = ["x"]

                [output]
                path = "result.zip"
            """),
                encoding="utf-8",
            )
            (root / "library.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation.named]
                targets = ["./unused/"]
            """),
                encoding="utf-8",
            )
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["-i", "library"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())
            self.assertIn(
                "selected Invocation provides no config, targets, case, or archive_mtime",
                stdout.getvalue(),
            )

    def test_empty_invocation_is_noted_in_preview(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.data]
                path = "data"
                description = "Data."
                must = ["x"]
            """),
                encoding="utf-8",
            )
            (root / "library.dirpluck-inv").write_text("[invocation]\n", encoding="utf-8")
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["-i", "library", "--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertIn("README.md", stdout.getvalue())
            self.assertIn(
                "selected Invocation provides no config, targets, case, or archive_mtime",
                stdout.getvalue(),
            )

    def test_invocation_template_rejects_target_override(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["-i", "release", "app"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("TARGET arguments cannot be combined", stderr.getvalue())

    def test_invocation_template_accepts_case_when_template_omits_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "release", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)

    def test_cli_case_overrides_invocation_template_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
                case = "missing"
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "release", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)

    def test_invocation_template_rejects_config_override(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["-i", "release", "--config", "other"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--config cannot be combined", stderr.getvalue())

    def test_invocation_template_allows_preview_runtime_modifier(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["-i", "release", "--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertIn("README.md", stdout.getvalue())
            self.assertFalse((root / "result.zip").exists())

    def test_invocation_template_allows_paths_runtime_modifier(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "release.dirpluck-inv").write_text(
                textwrap.dedent("""
                [invocation]
                targets = ["./app/"]
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["-i", "release", "--paths"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Source", readme)
            self.assertIn(str((root / "app").resolve()), readme)

    def test_invocation_template_allows_sequence_runtime_modifier(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            data = root / "data"
            data.mkdir()
            (data / "x").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.data]
                path = "data"
                description = "Data."
                must = ["x"]

                [output.timestamp]
                path = "artifacts/"
                prefix = "snapshot"
            """),
                encoding="utf-8",
            )
            (root / "release.dirpluck-inv").write_text("[invocation]\n", encoding="utf-8")
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["-i", "release", "--sequence", "7"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            output = Path(stdout.getvalue().splitlines()[0])
            self.assertTrue(output.is_file())
            self.assertRegex(output.name, r"^snapshot-\d{8}-\d{6}-7\.zip$")

    def test_entry_may_be_specified_at_most_once(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["-i", "release", "-e", "one", "-e", "two"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--entry may be specified at most once", stderr.getvalue())

    def test_invocation_template_may_be_specified_at_most_once(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["-i", "release", "-i", "other"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--invocation-template may be specified at most once", stderr.getvalue())

    def test_preview_accepts_root_configuration_without_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                [always.data]
                path = "data"
                description = "Data."
                must = ["x"]
            """),
                encoding="utf-8",
            )
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertIn("README.md", stdout.getvalue())
            self.assertIn("└── x", stdout.getvalue())
            self.assertFalse(any(root.glob("*.zip")))

    def test_preview_rejects_sequence(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--preview", "--sequence", "1"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--sequence cannot be combined with --preview", stderr.getvalue())

    def test_preview_rejects_runtime_output_options(self):
        for arguments, message in (
            (["--preview", "--here"], "--here cannot be combined with --preview"),
            (["--preview", "--output", "out.zip"], "--output cannot be combined with --preview"),
            (["--preview", "--force"], "--force cannot be combined with --preview"),
        ):
            with self.subTest(arguments=arguments):
                stderr = StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(arguments)
                self.assertEqual(caught.exception.code, 2)
                self.assertIn(message, stderr.getvalue())

    def test_removed_configs_option_is_rejected(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--configs"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("unrecognized arguments: --configs", stderr.getvalue())

    def test_build_subcommand_is_removed(self):
        with self.assertRaises(SystemExit) as caught:
            main(["build", "app"])
        self.assertEqual(caught.exception.code, 2)

    def test_output_option_selects_runtime_exact_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["./app/", "-o", "artifacts/out.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertEqual(
                stdout.getvalue().strip(),
                str(root / "artifacts" / "out.zip"),
            )
            self.assertTrue((root / "artifacts" / "out.zip").is_file())
            self.assertFalse((root / "result.zip").exists())

    def test_here_uses_runtime_cwd_and_default_timestamp_name(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch(
                        "dirpluck._output._current_output_timestamp",
                        return_value="20260923-021500",
                    ),
                    redirect_stdout(StringIO()),
                ):
                    result = main(["./app/", "--here"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "dirpluck-20260923-021500.zip").is_file())
            self.assertFalse((root / "result.zip").exists())

    def test_here_accepts_explicit_filename_only_with_equals(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "--here=context.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "context.zip").is_file())

            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/", "--here=nested/context.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("filename only", stderr.getvalue())

    def test_output_directory_uses_default_timestamp_name(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch(
                        "dirpluck._output._current_output_timestamp",
                        return_value="20260923-021600",
                    ),
                    redirect_stdout(StringIO()),
                ):
                    result = main(["./app/", "--output", "artifacts/"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "artifacts" / "dirpluck-20260923-021600.zip").is_file())

    def test_runtime_automatic_name_reuses_root_timestamp_naming(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            config = root / "default.dirpluck"
            config.write_text(
                config.read_text(encoding="utf-8").split("[output]", 1)[0]
                + textwrap.dedent(
                    """
                    [output.timestamp]
                    path = "configured/"
                    prefix = "project"
                    suffix = "review"
                    """
                ),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch(
                        "dirpluck._output._current_output_timestamp",
                        return_value="20260923-021700",
                    ),
                    redirect_stdout(StringIO()),
                ):
                    result = main(["./app/", "--output", "runtime/", "--sequence", "4"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "runtime" / "project-20260923-021700-4-review.zip").is_file())
            self.assertFalse((root / "configured").exists())

    def test_runtime_exact_output_does_not_reuse_timestamp_naming(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            config = root / "default.dirpluck"
            config.write_text(
                config.read_text(encoding="utf-8").split("[output]", 1)[0]
                + textwrap.dedent(
                    """
                    [output.timestamp]
                    path = "configured/"
                    prefix = "project"
                    suffix = "review"
                    """
                ),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "-o", "runtime/exact.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "runtime" / "exact.zip").is_file())

    def test_runtime_output_allows_build_without_configuration_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            config = root / "default.dirpluck"
            config.write_text(
                config.read_text(encoding="utf-8").split("[output]", 1)[0],
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./app/", "-o", "runtime.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "runtime.zip").is_file())

    def test_force_allows_runtime_and_configured_output_replacement(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            runtime = root / "runtime.zip"
            runtime.write_bytes(b"old")
            configured = root / "result.zip"
            configured.write_bytes(b"old")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    self.assertEqual(main(["./app/", "-o", "runtime.zip", "-f"]), 0)
                    self.assertEqual(main(["./app/", "--force"]), 0)
            finally:
                os.chdir(previous)
            with zipfile.ZipFile(runtime) as archive:
                self.assertIn("app/src/app.py", archive.namelist())
            with zipfile.ZipFile(configured) as archive:
                self.assertIn("app/src/app.py", archive.namelist())

    def test_runtime_output_rejects_collision_without_force(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "runtime.zip").write_bytes(b"old")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/", "-o", "runtime.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("already exists", stderr.getvalue())
            self.assertEqual((root / "runtime.zip").read_bytes(), b"old")

    def test_here_and_output_are_mutually_exclusive(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--here", "-o", "out.zip"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--here cannot be combined with --output", stderr.getvalue())

    def test_output_rejects_backslash_path_syntax(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/", "-o", r"artifacts\out.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("backslashes are not allowed", stderr.getvalue())

    def test_sequence_requires_automatic_runtime_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["./app/", "-o", "out.zip", "--sequence", "2"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn(
                "sequence can only be used with timestamp output",
                stderr.getvalue(),
            )

    def test_cli_preserves_location_expansion_trailing_slash(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            projects = Path(other) / "projects"
            for name in ("alpha", "beta"):
                (projects / name / "src").mkdir(parents=True)
                (projects / name / "src" / f"{name}.py").write_text(name, encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(f"""
                [pluck]
                description = "Projects."
                must = ["src/"]

                [scope.work]
                path = {projects.as_posix()!r}

                [output]
                path = "result.zip"
                overwrite = false
            """),
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["work/"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("alpha/src/alpha.py", names)
            self.assertIn("beta/src/beta.py", names)


if __name__ == "__main__":
    unittest.main()
