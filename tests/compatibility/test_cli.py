from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import os
import textwrap
import unittest
import warnings

from tests._temp import resolved_temporary_directory
from tests.contract.test_cli import CONFIG

from dirpluck import AlwaysMigrationWarning, ConfigurationDeprecationWarning
from dirpluck.cli import main


class Pre10CliCompatibilityTests(unittest.TestCase):
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

    # Moved from tests/test_cli.py:CliTests.test_always_layout_migration_warning_is_emitted_only_for_changed_identity
    def test_always_layout_migration_warning_is_emitted_only_for_changed_identity(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "source").mkdir()
            (root / "source" / "guide.md").write_text("guide\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [always.docs]
                        path = "source"
                        must = ["guide.md"]

                        [output]
                        path = "result.zip"
                        """
                ),
                encoding="utf-8",
            )
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    result = main([])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            warning = stderr.getvalue()
            self.assertEqual(warning.count("Always archive layout changed in 0.16.0"), 1)
            self.assertIn("0.14.x would place this source under 'source'", warning)
            self.assertIn("0.16.x uses 'docs'", warning)

    # Moved from tests/test_cli.py:CliTests.test_always_layout_migration_warning_is_not_emitted_for_unchanged_identity
    def test_always_layout_migration_warning_is_not_emitted_for_unchanged_identity(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    result = main(["./app/"])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            self.assertNotIn("Always archive layout changed in 0.16.0", stderr.getvalue())

    # Moved from tests/test_cli.py:CliTests.test_cli_collects_always_migration_warning_instead_of_emitting_python_warning
    def test_cli_collects_always_migration_warning_instead_of_emitting_python_warning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "source").mkdir()
            (root / "source" / "guide.md").write_text("guide\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [always.docs]
                        path = "source"
                        must = ["guide.md"]

                        [output]
                        path = "result.zip"
                        """
                ),
                encoding="utf-8",
            )
            stderr = StringIO()
            previous = Path.cwd()
            try:
                os.chdir(root)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always", AlwaysMigrationWarning)
                    with redirect_stdout(StringIO()), redirect_stderr(stderr):
                        result = main([])
            finally:
                os.chdir(previous)

            self.assertEqual(result, 0)
            self.assertEqual(
                [item for item in caught if issubclass(item.category, AlwaysMigrationWarning)],
                [],
            )
            self.assertIn("Always archive layout changed in 0.16.0", stderr.getvalue())

    # Moved from tests/test_cli.py:CliTests.test_deprecated_nested_selection_reference_warns_once_per_config_file
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

    # Moved from tests/test_cli.py:CliTests.test_deprecated_nested_selection_reference_in_base_config_warns
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

    # Moved from tests/test_cli.py:CliTests.test_legacy_pluck_case_cli_warning_points_to_canonical_syntax
    def test_legacy_pluck_case_cli_warning_points_to_canonical_syntax(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "tests").mkdir(parents=True)
            (root / "app" / "tests" / "test_app.py").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent("""
                    [pluck.case.review]
                    must = ["tests/"]
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
                    result = main(["./app/", "--case", "review"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            warning = stderr.getvalue()
            self.assertIn("[pluck.case.<name>]", warning)
            self.assertIn("[case.pluck.<name>]", warning)
            self.assertIn("1.0.0", warning)
