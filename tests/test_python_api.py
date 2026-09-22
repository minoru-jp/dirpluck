from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import os
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from _temp import resolved_temporary_directory

import dirpluck
from dirpluck.cli import main


CONFIG = '''
[pluck]
must = ["src"]

[always.guidelines]
path = "guidelines"
must = ["*.md"]

[output]
path = "result.zip"
overwrite = true
'''


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
            {"DirpluckError", "RunResult", "__version__", "run"},
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

            result = dirpluck.run("app", cwd=root)
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
                self.assertEqual(tuple(sorted(archive.namelist())), tuple(sorted(result.archive_entries)))

    def test_preview_returns_cli_equivalent_tree_without_writing_archive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._workspace(root)

            result = dirpluck.run("app", preview=True, cwd=root)
            self.assertIsNone(result.output_path)
            self.assertFalse((root / "result.zip").exists())

            previous = Path.cwd()
            output = StringIO()
            try:
                os.chdir(root)
                with redirect_stdout(output):
                    code = main(["app", "--preview"])
            finally:
                os.chdir(previous)
            self.assertEqual(code, 0)
            self.assertEqual(output.getvalue().rstrip("\n"), result.preview_text)

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
                "app",
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
                    '''
                    [output.timestamp]
                    path = "configured/"
                    prefix = "api"
                    suffix = "snapshot"
                    '''
                ),
                encoding="utf-8",
            )

            with patch(
                "dirpluck._output._current_output_timestamp",
                return_value="20260923-022000",
            ):
                result = dirpluck.run(
                    "app",
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
                    '''
                    [pluck]
                    must = ["src"]

                    [pluck.case.audit]
                    must = ["tests"]

                    [output]
                    path = "result.zip"
                    overwrite = true
                    '''
                ),
                encoding="utf-8",
            )
            (root / "calls.dirpluck-inv").write_text(
                textwrap.dedent(
                    '''
                    [invocation.review]
                    targets = ["app"]
                    case = "missing-on-purpose"
                    '''
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

    def test_run_rejects_invalid_cli_style_argument_combinations(self):
        cases = (
            ({"config": "review", "invocation": "calls"}, "config cannot be combined"),
            ({"entry": "review"}, "entry requires invocation"),
            ({"preview": True, "sequence": 1}, "sequence cannot be combined"),
            ({"output": r"bad\path.zip"}, "backslashes are not allowed"),
            ({"force": "yes"}, "force must be a boolean"),
        )
        for kwargs, message in cases:
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(dirpluck.DirpluckError, message):
                dirpluck.run(**kwargs)

        with self.assertRaisesRegex(dirpluck.DirpluckError, "targets cannot be combined"):
            dirpluck.run("app", invocation="calls")


if __name__ == "__main__":
    unittest.main()
