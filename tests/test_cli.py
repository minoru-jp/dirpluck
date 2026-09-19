from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import os
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from dirpluck import __version__
from dirpluck.cli import main


CONFIG = '''
[target]
description = "Default development target."
include = ["src"]

[target.case.review]
description = "Review target."
include = ["tests"]

[companion.framework]
path = "framework"
description = "Fixed framework."
include = ["src"]

[output]
path = "result.zip"
if_exists = "error"
'''


class CliTests(unittest.TestCase):
    def _workspace(self, root: Path, *, config_path: str = "dirpluck.toml") -> None:
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

    def test_direct_invocation_uses_default_target_and_configured_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertEqual(names, {"README.md", "app/src/app.py", "framework/src/core.py"})

    def test_multiple_target_directories_are_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            app_two = root / "app-two"
            (app_two / "src").mkdir(parents=True)
            (app_two / "tests").mkdir()
            (app_two / "src" / "app.py").write_text("APP = 2\n", encoding="utf-8")
            (app_two / "tests" / "test_app.py").write_text("TEST = 2\n", encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "app-two"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/src/app.py", names)
            self.assertIn("app-two/src/app.py", names)
            self.assertIn("framework/src/core.py", names)

    def test_case_applies_to_all_target_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            app_two = root / "app-two"
            (app_two / "src").mkdir(parents=True)
            (app_two / "tests").mkdir()
            (app_two / "src" / "app.py").write_text("APP = 2\n", encoding="utf-8")
            (app_two / "tests" / "test_app.py").write_text("TEST = 2\n", encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "app-two", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("app/tests/test_app.py", names)
            self.assertIn("app-two/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)
            self.assertNotIn("app-two/src/app.py", names)

    def test_default_config_can_live_in_dirpluck_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="dirpluck/dirpluck.toml")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_duplicate_default_config_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "dirpluck").mkdir()
            (root / "dirpluck" / "dirpluck.toml").write_text(CONFIG, encoding="utf-8")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("configuration 'dirpluck.toml' is ambiguous", stderr.getvalue())

    def test_case_selects_named_target_case(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("app/tests/test_app.py", names)
            self.assertNotIn("app/src/app.py", names)
            self.assertIn("framework/src/core.py", names)
            self.assertIn("| app/ | Review target. | 1 |", readme)
            self.assertNotIn("Case:", readme)

    def test_paths_adds_source_column_to_archive_readme(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "--paths"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertEqual(readme.splitlines()[2], "| Path | Description | Files | Source |")
            self.assertIn((root / "app").resolve().as_posix(), readme)
            self.assertIn((root / "framework").resolve().as_posix(), readme)

    def test_unknown_case_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            stderr = StringIO()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app", "--case", "release"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("case 'release' is not defined", stderr.getvalue())

    def test_case_is_required_when_default_target_is_absent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [target.case.review]
                description = "Review only."
                include = ["src"]
                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            previous = Path.cwd()
            stderr = StringIO()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("no default [target]", stderr.getvalue())


    def test_companion_only_configuration_runs_without_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            (root / "documents" / "a.md").write_text("A", encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.documents]
                path = "documents"
                description = "Documents."
                include = ["*.md"]

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
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
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.documents]
                path = "documents"
                description = "Documents."
                include_if_exists = ["*.md"]
                if_empty = "allow"

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["documents"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("TARGET must not be specified", stderr.getvalue())

    def test_directory_is_required_when_configuration_defines_target(self):
        with tempfile.TemporaryDirectory() as temp:
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

    def test_companion_case_is_selected_and_missing_case_falls_back_to_base(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "documents" / "current").mkdir(parents=True)
            (root / "documents" / "archive").mkdir()
            (root / "documents" / "current" / "now.md").write_text("now", encoding="utf-8")
            (root / "documents" / "archive" / "old.md").write_text("old", encoding="utf-8")
            (root / "assets").mkdir()
            (root / "assets" / "figure.txt").write_text("figure", encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.documents]
                path = "documents"
                description = "Current documents."
                include = ["current"]

                [companion.documents.case.archive]
                description = "Archived documents."
                include = ["current", "archive"]

                [companion.assets]
                path = "assets"
                description = "Assets."
                include = ["*.txt"]

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
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
            self.assertIn("| documents/ | Archived documents. | 2 |", readme)
            self.assertIn("| assets/ | Assets. | 1 |", readme)
            self.assertNotIn("companion", readme.lower())

    def test_case_option_cannot_be_repeated(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["app", "--case", "review", "--case", "release"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--case may be specified at most once", stderr.getvalue())

    def test_generated_output_accepts_explicit_sequence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "app" / "src"
            app.mkdir(parents=True)
            (app / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent("""
                [target]
                description = "Target."
                include = ["src"]
                [output]
                directory = "snapshots"
                prefix = "project"
                timestamp = true
                suffix = "review"
            """), encoding="utf-8")
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with patch("dirpluck.builder._current_output_timestamp", return_value="20260916-011623"):
                    with redirect_stdout(stdout):
                        result = main(["app", "--sequence", "4"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            expected = root / "snapshots" / "project-20260916-011623-4-review.zip"
            self.assertTrue(expected.is_file())
            self.assertEqual(Path(stdout.getvalue().strip()), expected)

    def test_sequence_is_rejected_for_fixed_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app", "--sequence", "1"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("output sequence can only be used with generated output", stderr.getvalue())
            self.assertFalse((root / "result.zip").exists())

    def test_sequence_must_be_positive_integer(self):
        for value in ("0", "-1", "x"):
            with self.subTest(value=value):
                stderr = StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app", "--sequence", value])
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("integer greater than or equal to 1", stderr.getvalue())

    def test_sequence_option_cannot_be_repeated(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["app", "--sequence", "1", "--sequence", "2"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--sequence may be specified at most once", stderr.getvalue())

    def test_dry_run_prints_tree_without_creating_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["app", "--dry-run"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertFalse((root / "result.zip").exists())
            self.assertEqual(
                stdout.getvalue().strip(),
                "\n".join([
                    "├── README.md",
                    "├── app/",
                    "│   └── src/",
                    "│       └── app.py",
                    "└── framework/",
                    "    └── src/",
                    "        └── core.py",
                ]),
            )

    def test_paths_can_be_combined_with_dry_run_without_changing_tree_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["app", "--dry-run", "--paths"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertFalse((root / "result.zip").exists())
            self.assertIn("README.md", stdout.getvalue())
            self.assertNotIn(root.as_posix(), stdout.getvalue())

    def test_dry_run_does_not_apply_existing_output_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            output = root / "result.zip"
            output.write_bytes(b"existing")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "--dry-run"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertEqual(output.read_bytes(), b"existing")

    def test_dry_run_marks_missing_and_optional_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app").mkdir()
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [target]
                description = "Target."
                include = ["src"]
                include_if_exists = ["README.md"]
                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["app", "--dry-run"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            text = stdout.getvalue()
            self.assertIn("README.md [optional missing]", text)
            self.assertIn("src [missing]", text)
            self.assertIn("target (`app/`): empty, would error", text)

    def test_named_config_is_searched_in_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="review.toml")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "--config", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_named_config_is_searched_in_dirpluck_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="dirpluck/review.toml")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app", "--config", "review.toml"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertTrue((root / "result.zip").is_file())

    def test_duplicate_named_config_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="review.toml")
            (root / "dirpluck").mkdir()
            (root / "dirpluck" / "review.toml").write_text(CONFIG, encoding="utf-8")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app", "--config", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("configuration 'review.toml' is ambiguous", stderr.getvalue())

    def test_config_path_is_rejected_because_discovery_scope_is_fixed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="dirpluck/review.toml")
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                    main(["app", "--config", "dirpluck/review.toml"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("configuration name must be a filename, not a path", stderr.getvalue())

    def test_configs_lists_discoverable_configs_and_ignores_pyproject(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            (root / "review.toml").write_text(CONFIG, encoding="utf-8")
            (root / "snapshot.toml").write_text(textwrap.dedent('''
                [companion.documents]
                path = "documents"
                description = "Documents."
                include = ["*.md"]
                [output]
                path = "snapshot.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            (root / "pyproject.toml").write_text('[project]\nname = "example"\n', encoding="utf-8")
            (root / "dirpluck").mkdir()
            (root / "dirpluck" / "release.toml").write_text(CONFIG, encoding="utf-8")
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["--configs"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            text = stdout.getvalue()
            self.assertIn("dirpluck.toml  ./dirpluck.toml  [default]", text)
            self.assertIn("review.toml  ./review.toml", text)
            self.assertIn("snapshot.toml  ./snapshot.toml", text)
            self.assertIn("release.toml  ./dirpluck/release.toml", text)
            self.assertNotIn("pyproject.toml", text)

    def test_configs_rejects_paths_option(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            main(["--configs", "--paths"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--configs cannot be combined", stderr.getvalue())

    def test_configs_marks_same_filename_as_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root, config_path="review.toml")
            (root / "dirpluck").mkdir()
            (root / "dirpluck" / "review.toml").write_text(CONFIG, encoding="utf-8")
            stdout = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["--configs"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            lines = [line for line in stdout.getvalue().splitlines() if line.startswith("review.toml")]
            self.assertEqual(len(lines), 2)
            self.assertTrue(all("ambiguous" in line for line in lines))

    def test_build_subcommand_is_removed(self):
        with self.assertRaises(SystemExit) as caught:
            main(["build", "app"])
        self.assertEqual(caught.exception.code, 2)

    def test_removed_output_option_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._workspace(root)
            previous = Path.cwd()
            try:
                os.chdir(root)
                with self.assertRaises(SystemExit) as caught:
                    main(["app", "-o", "out.zip"])
            finally:
                os.chdir(previous)
            self.assertEqual(caught.exception.code, 2)
            self.assertFalse((root / "out.zip").exists())


    def test_import_only_configuration_runs_without_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            (external / "data").mkdir(parents=True)
            (external / "data" / "artifact.txt").write_text("x", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Imported data."
                include = ["artifact.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main([])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertIn("data/artifact.txt", archive.namelist())
            self.assertFalse((external / "unused.zip").exists())

    def test_imported_target_definition_accepts_cli_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            target = root / "app"
            (target / "src").mkdir(parents=True)
            (target / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            external.mkdir()
            (external / "config.toml").write_text(textwrap.dedent('''
                [target]
                description = "Reusable imported Target definition."
                include = ["src"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent('''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["app"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertIn("app/src/app.py", archive.namelist())
            self.assertFalse((external / "unused.zip").exists())

    def test_configs_lists_import_only_root_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "review.toml").write_text(textwrap.dedent('''
                [import.external]
                root = ".."
                configuration = "external/config.toml"

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            previous = Path.cwd()
            stdout = StringIO()
            try:
                os.chdir(root)
                with redirect_stdout(stdout):
                    result = main(["--configs"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            self.assertIn("review.toml", stdout.getvalue())

    def test_cli_preserves_location_expansion_trailing_slash(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            projects = Path(other) / "projects"
            for name in ("alpha", "beta"):
                (projects / name / "src").mkdir(parents=True)
                (projects / name / "src" / f"{name}.py").write_text(name, encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent(f'''
                [target]
                description = "Projects."
                include = ["src"]

                [target.location.work]
                path = {projects.as_posix()!r}

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
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

    def test_cli_dot_slash_bypasses_location_lookup(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            cwd_target = root / "work" / "app" / "src"
            external_target = Path(other) / "app" / "src"
            cwd_target.mkdir(parents=True)
            external_target.mkdir(parents=True)
            (cwd_target / "cwd.py").write_text("cwd", encoding="utf-8")
            (external_target / "external.py").write_text("external", encoding="utf-8")
            (root / "dirpluck.toml").write_text(textwrap.dedent(f'''
                [target]
                description = "Project."
                include = ["src"]

                [target.location.work]
                path = {Path(other).as_posix()!r}

                [output]
                path = "result.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    result = main(["./work/app"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("work/app/src/cwd.py", names)
            self.assertNotIn("app/src/external.py", names)


if __name__ == "__main__":
    unittest.main()
