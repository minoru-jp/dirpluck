from pathlib import Path
import os
import subprocess
import sys
import textwrap
import unittest
import warnings

from tests._temp import resolved_temporary_directory

import dirpluck


class Pre10PythonApiCompatibilityTests(unittest.TestCase):
    # Moved from tests/test_python_api.py:PythonApiTests.test_run_emits_layout_migration_warning_only_when_archive_identity_changes
    def test_run_emits_layout_migration_warning_only_when_archive_identity_changes(self):
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

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", dirpluck.AlwaysMigrationWarning)
                result = dirpluck.run(preview=True, cwd=root)

            migrations = [
                warning
                for warning in caught
                if issubclass(warning.category, dirpluck.AlwaysMigrationWarning)
            ]
            self.assertEqual(len(migrations), 1)
            self.assertEqual(Path(migrations[0].filename).resolve(), Path(__file__).resolve())
            message = str(migrations[0].message)
            self.assertIn("0.14.x would place this source under 'source'", message)
            self.assertIn("0.16.x uses 'docs'", message)
            self.assertEqual(result.archive_entries, ("README.md", "docs/guide.md"))
            self.assertEqual(result.warnings, ())

    # Moved from tests/test_python_api.py:PythonApiTests.test_run_does_not_emit_layout_migration_warning_when_identity_is_unchanged
    def test_run_does_not_emit_layout_migration_warning_when_identity_is_unchanged(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [always.docs]
                        path = "docs"
                        must = ["guide.md"]

                        [output]
                        path = "result.zip"
                        """
                ),
                encoding="utf-8",
            )

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", dirpluck.AlwaysMigrationWarning)
                result = dirpluck.run(preview=True, cwd=root)

            migrations = [
                warning
                for warning in caught
                if issubclass(warning.category, dirpluck.AlwaysMigrationWarning)
            ]
            self.assertEqual(migrations, [])
            self.assertEqual(result.archive_entries, ("README.md", "docs/guide.md"))

    def test_run_suppresses_legacy_layout_migration_warning_when_017_layout_is_explicit(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "source").mkdir()
            (root / "source" / "guide.md").write_text("guide\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [about]
                        always_layout = "shared"

                        [layout.shared]

                        [always.docs]
                        path = "source"
                        must = ["guide.md"]
                        """
                ),
                encoding="utf-8",
            )

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", dirpluck.AlwaysMigrationWarning)
                result = dirpluck.run(preview=True, cwd=root)

            migrations = [
                warning
                for warning in caught
                if issubclass(warning.category, dirpluck.AlwaysMigrationWarning)
            ]
            self.assertEqual(migrations, [])
            self.assertEqual(result.archive_entries, ("README.md", "shared/docs/guide.md"))

    # Moved from tests/test_python_api.py:PythonApiTests.test_run_always_migration_warning_is_visible_by_default
    def test_run_always_migration_warning_is_visible_by_default(self):
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
                        """
                ),
                encoding="utf-8",
            )
            script = root / "caller.py"
            script.write_text(
                "from pathlib import Path\n"
                + "import dirpluck\n"
                + "root = Path(__file__).parent\n"
                + "dirpluck.run(preview=True, cwd=root)\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            source_root = str(Path(__file__).resolve().parents[2] / "src")
            existing = env.get("PYTHONPATH")
            env["PYTHONPATH"] = (
                source_root if not existing else os.pathsep.join((source_root, existing))
            )

            completed = subprocess.run(
                [sys.executable, str(script)],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("AlwaysMigrationWarning", completed.stderr)
            self.assertIn("0.14.x would place this source under 'source'", completed.stderr)
            self.assertIn(str(script), completed.stderr)
            self.assertNotIn("_effective.py", completed.stderr)

    # Moved from tests/test_python_api.py:PythonApiTests.test_run_emits_namespace_transition_warning_alongside_layout_warning
    def test_run_emits_namespace_transition_warning_alongside_layout_warning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [namespace.docs]

                        [always.source]
                        path = "docs"
                        namespace = "docs"
                        must = ["guide.md"]

                        [output]
                        path = "result.zip"
                        """
                ),
                encoding="utf-8",
            )

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", dirpluck.AlwaysMigrationWarning)
                result = dirpluck.run(preview=True, cwd=root)

            messages = [
                str(warning.message)
                for warning in caught
                if issubclass(warning.category, dirpluck.AlwaysMigrationWarning)
            ]
            self.assertEqual(len(messages), 2)
            self.assertTrue(
                any("deprecated and will be removed in 1.0.0" in message for message in messages)
            )
            self.assertTrue(
                any("replaces the Always source name 'source'" in message for message in messages)
            )
            self.assertTrue(
                any(
                    "0.14.x would place this source under 'docs/docs'" in message
                    for message in messages
                )
            )
            self.assertEqual(result.archive_entries, ("README.md", "docs/guide.md"))

    # Moved from tests/test_python_api.py:PythonApiTests.test_run_emits_deprecation_warning_for_legacy_configuration_syntax
    def test_run_emits_deprecation_warning_for_legacy_configuration_syntax(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    r"""
                        [shared.must]
                        required = ["src/"]

                        [pluck]
                        must = [["required"]]
                        """
                ),
                encoding="utf-8",
            )

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", dirpluck.ConfigurationDeprecationWarning)
                result = dirpluck.run("./app/", preview=True, cwd=root)

            deprecations = [
                warning
                for warning in caught
                if issubclass(warning.category, dirpluck.ConfigurationDeprecationWarning)
            ]
            self.assertEqual(len(deprecations), 1)
            self.assertEqual(Path(deprecations[0].filename).resolve(), Path(__file__).resolve())
            message = str(deprecations[0].message)
            self.assertIn("deprecated nested-array Selection reference syntax", message)
            self.assertIn("0.14.0", message)
            self.assertIn("1.0.0", message)
            self.assertIn('{ shared = "..." }', message)
            self.assertEqual(result.warnings, ())

    # Moved from tests/test_python_api.py:PythonApiTests.test_run_emits_deprecation_warning_for_legacy_syntax_in_base_config
    def test_run_emits_deprecation_warning_for_legacy_syntax_in_base_config(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "base.dirpluck").write_text(
                textwrap.dedent(
                    r"""
                        [shared.must]
                        required = ["src/"]

                        [pluck]
                        must = [["required"]]
                        """
                ),
                encoding="utf-8",
            )
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [about]
                        base = "base.dirpluck"
                        """
                ),
                encoding="utf-8",
            )

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", dirpluck.ConfigurationDeprecationWarning)
                result = dirpluck.run("./app/", preview=True, cwd=root)

            deprecations = [
                warning
                for warning in caught
                if issubclass(warning.category, dirpluck.ConfigurationDeprecationWarning)
            ]
            self.assertEqual(len(deprecations), 1)
            self.assertEqual(Path(deprecations[0].filename).resolve(), Path(__file__).resolve())
            self.assertIn("base.dirpluck", str(deprecations[0].message))
            self.assertEqual(result.warnings, ())

    # Moved from tests/test_python_api.py:PythonApiTests.test_run_configuration_deprecation_warning_is_visible_by_default
    def test_run_configuration_deprecation_warning_is_visible_by_default(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                        [shared.must]
                        required = ["src/"]

                        [pluck]
                        must = [["required"]]
                        """
                ),
                encoding="utf-8",
            )
            script = root / "caller.py"
            script.write_text(
                "from pathlib import Path\n"
                + "import dirpluck\n"
                + "root = Path(__file__).parent\n"
                + "dirpluck.run('./app/', preview=True, cwd=root)\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            source_root = str(Path(__file__).resolve().parents[2] / "src")
            existing = env.get("PYTHONPATH")
            env["PYTHONPATH"] = (
                source_root if not existing else os.pathsep.join((source_root, existing))
            )

            completed = subprocess.run(
                [sys.executable, str(script)],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("ConfigurationDeprecationWarning", completed.stderr)
            self.assertIn(str(script), completed.stderr)
            self.assertNotIn("_config_parser.py", completed.stderr)
