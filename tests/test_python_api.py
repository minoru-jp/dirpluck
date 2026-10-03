from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import cast
import os
import subprocess
import sys
import textwrap
import unittest
import warnings
from unittest.mock import patch
import zipfile

from tests._temp import resolved_temporary_directory

import dirpluck
from dirpluck.cli import main


CONFIG = """
[pluck]
must = ["src/"]

[always.guidelines]
path = "guidelines"
must = ["*.md"]

[output]
path = "result.zip"
overwrite = true
"""


class PythonApiTests(unittest.TestCase):
    def _workspace(self, root: Path) -> None:
        (root / "app" / "src").mkdir(parents=True)
        (root / "guidelines").mkdir()
        (root / "app" / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
        (root / "guidelines" / "review.md").write_text("Review\n", encoding="utf-8")
        (root / "default.dirpluck").write_text(textwrap.dedent(CONFIG), encoding="utf-8")

    def test_package_root_exposes_only_the_supported_python_surface(self):
        self.assertEqual(
            set(dirpluck.__all__),
            {"ConfigurationDeprecationWarning", "DirpluckError", "RunResult", "__version__", "run"},
        )
        for name in dirpluck.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(dirpluck, name))

        for name in (
            "ArchivePlan",
            "BuildRequest",
            "Config",
            "InvocationTemplate",
            "build_archive",
            "load_config",
            "load_invocation",
            "plan_archive",
            "resolve_sources",
        ):
            with self.subTest(private=name):
                self.assertFalse(hasattr(dirpluck, name))

    def test_run_builds_the_same_archive_as_a_direct_cli_invocation(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)

            result = dirpluck.run("./app/", cwd=root)
            self.assertEqual(result.output_path, root / "result.zip")
            self.assertEqual(
                result.archive_entries,
                ("README.md", "app/src/app.py", "guidelines/review.md"),
            )
            self.assertIn("├── app/", result.preview_text)
            self.assertIn("## `app/`", result.archive_readme)
            self.assertEqual(result.skipped_link_count, 0)
            self.assertFalse(result.invocation_empty)

            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertEqual(
                    tuple(sorted(archive.namelist())), tuple(sorted(result.archive_entries))
                )

    def test_preview_returns_cli_equivalent_tree_without_writing_archive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)

            result = dirpluck.run("./app/", preview=True, cwd=root)
            self.assertIsNone(result.output_path)
            self.assertFalse((root / "result.zip").exists())

            previous = Path.cwd()
            output = StringIO()
            try:
                os.chdir(root)
                with redirect_stdout(output):
                    code = main(["./app/", "--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(code, 0)
            self.assertEqual(output.getvalue().rstrip("\n"), result.preview_text)

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
            source_root = str(Path(__file__).resolve().parents[1] / "src")
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

    def test_run_returns_wrong_type_warnings_without_changing_may_semantics(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "README.md").write_text("readme", encoding="utf-8")
            (root / "app" / "src" / "main.py").write_text("x", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                    [pluck]
                    must = ["README.md"]
                    may = ["src"]

                    [output]
                    path = "result.zip"
                    overwrite = true
                    """
                ),
                encoding="utf-8",
            )

            result = dirpluck.run("./app/", cwd=root)

            self.assertEqual(result.archive_entries, ("README.md", "app/README.md"))
            self.assertEqual(len(result.warnings), 1)
            self.assertIn("target: optional file pattern 'src' did not match", result.warnings[0])
            self.assertIn("directory 'src/' exists", result.warnings[0])

    def test_run_keeps_wrong_type_warnings_distinct_per_target(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for name in ("projA", "projB"):
                (root / name / "src").mkdir(parents=True)
                (root / name / "README.md").write_text(name, encoding="utf-8")
                (root / name / "src" / "main.py").write_text(name, encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                    [pluck]
                    must = ["README.md"]
                    may = ["src"]
                    """
                ),
                encoding="utf-8",
            )

            result = dirpluck.run("./projA/", "./projB/", preview=True, cwd=root)

            self.assertEqual(len(result.warnings), 2)
            self.assertTrue(any("target 'projA':" in warning for warning in result.warnings))
            self.assertTrue(any("target 'projB':" in warning for warning in result.warnings))

    def test_preview_rejects_runtime_output_and_force(self):
        with self.assertRaises(dirpluck.DirpluckError) as output_error:
            dirpluck.run(preview=True, output="out.zip")
        self.assertIn("output cannot be combined with preview", str(output_error.exception))

        with self.assertRaises(dirpluck.DirpluckError) as force_error:
            dirpluck.run(preview=True, force=True)
        self.assertIn("force cannot be combined with preview", str(force_error.exception))

    def test_run_supports_runtime_output_and_force(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)
            output = root / "runtime.zip"
            output.write_bytes(b"old")

            result = dirpluck.run(
                "./app/",
                output="runtime.zip",
                force=True,
                cwd=root,
            )
            self.assertEqual(result.output_path, output)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("app/src/app.py", archive.namelist())

    def test_run_runtime_output_directory_uses_configuration_timestamp_naming(self):
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
                    prefix = "api"
                    suffix = "snapshot"
                    """
                ),
                encoding="utf-8",
            )

            with patch(
                "dirpluck._output._current_output_timestamp",
                return_value="20260923-022000",
            ):
                result = dirpluck.run(
                    "./app/",
                    output="runtime/",
                    sequence=2,
                    cwd=root,
                )
            self.assertEqual(
                result.output_path,
                root / "runtime" / "api-20260923-022000-2-snapshot.zip",
            )

    def test_run_supports_invocation_entry_and_cli_case_override(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "tests").mkdir()
            (root / "app" / "src" / "app.py").write_text("APP = 1\n", encoding="utf-8")
            (root / "app" / "tests" / "test_app.py").write_text("TEST = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                    [pluck]
                    must = ["src/"]

                    [pluck.case.audit]
                    must = ["tests/"]

                    [output]
                    path = "result.zip"
                    overwrite = true
                    """
                ),
                encoding="utf-8",
            )
            (root / "calls.dirpluck-inv").write_text(
                textwrap.dedent(
                    """
                    [invocation.review]
                    targets = ["./app/"]
                    case = "missing-on-purpose"
                    """
                ),
                encoding="utf-8",
            )

            result = dirpluck.run(
                invocation="calls",
                entry="review",
                case="audit",
                preview=True,
                cwd=root,
            )
            self.assertIn("tests/", result.preview_text)
            self.assertIn("test_app.py", result.preview_text)
            self.assertNotIn("src/", result.preview_text)

    def test_invocation_template_targets_accept_file_selectors(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "repo-a.zip").write_bytes(b"a")
            (returned / "repo-b.zip").write_bytes(b"b")
            (returned / "notes.txt").write_text("notes\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                textwrap.dedent(
                    """
                    [scope.returned]
                    path = "returned"
                    target_kind = "file"

                    [output]
                    path = "result.zip"
                    overwrite = true
                    """
                ),
                encoding="utf-8",
            )
            (root / "calls.dirpluck-inv").write_text(
                textwrap.dedent(
                    r"""
                    [invocation]
                    targets = ["returned:<.*\\.zip>"]
                    """
                ),
                encoding="utf-8",
            )

            result = dirpluck.run(invocation="calls", preview=True, cwd=root)
            self.assertEqual(
                set(result.archive_entries),
                {"README.md", "repo-a.zip", "repo-b.zip"},
            )
            self.assertNotIn("notes.txt", result.archive_entries)

    def test_run_rejects_invalid_cli_style_argument_combinations(self):
        cases = (
            (
                lambda: dirpluck.run(config="review", invocation="calls"),
                "config cannot be combined",
            ),
            (lambda: dirpluck.run(entry="review"), "entry requires invocation"),
            (lambda: dirpluck.run(preview=True, sequence=1), "sequence cannot be combined"),
            (lambda: dirpluck.run(output=r"bad\path.zip"), "backslashes are not allowed"),
            (
                lambda: dirpluck.run(force=cast(bool, cast(object, "yes"))),
                "force must be a boolean",
            ),
        )
        for call, message in cases:
            with (
                self.subTest(message=message),
                self.assertRaisesRegex(dirpluck.DirpluckError, message),
            ):
                call()

        with self.assertRaisesRegex(dirpluck.DirpluckError, "targets cannot be combined"):
            dirpluck.run("./app/", invocation="calls")


if __name__ == "__main__":
    unittest.main()
