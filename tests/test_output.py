from pathlib import Path
import os
import stat
import subprocess
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from _temp import resolved_temporary_directory
from _builder_support import BuilderTestCase

import dirpluck._filesystem as filesystem_module
from dirpluck._builder_models import BuildRequest
from dirpluck.builder import build_archive
from dirpluck.config import load_config
from dirpluck.errors import SelectionError


class OutputTests(BuilderTestCase):
    def test_output_parent_directories_are_created(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                description = "Target."
                must = ["src/"]
            ''', output="artifacts/context.zip")
            output = build_archive(config, BuildRequest.create("./application/"))
            self.assertEqual(output, root / "artifacts" / "context.zip")
            self.assertTrue(output.is_file())

    def test_fixed_output_default_policy_rejects_existing_archive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "out.zip").write_bytes(b"old")
            config = self._config(root, '''
                [pluck]
                description = "Target."
                must = ["src/"]
            ''', overwrite=False)
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("./application/"))
            self.assertEqual((root / "out.zip").read_bytes(), b"old")

    def test_existing_output_is_rejected_before_archive_planning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "out.zip").write_bytes(b"old")
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["missing"]
            """, overwrite=False)

            with patch("dirpluck._archive.plan_archive", side_effect=AssertionError("planning should not run")):
                with self.assertRaisesRegex(SelectionError, "output archive already exists"):
                    build_archive(config, BuildRequest.create("./application/"))

    def test_fixed_output_sequence_is_rejected_before_archive_planning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["missing"]
            """)

            with patch("dirpluck._archive.plan_archive", side_effect=AssertionError("planning should not run")):
                with self.assertRaisesRegex(SelectionError, "sequence can only be used with timestamp output"):
                    build_archive(config, BuildRequest.create("./application/", sequence=1))

    def test_fixed_output_overwrite_replaces_existing_archive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            (root / "out.zip").write_bytes(b"old")
            config = self._config(root, '''
                [pluck]
                description = "Target."
                must = ["src/"]
            ''', overwrite=True)
            build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(root / "out.zip") as archive:
                self.assertIn("application/src/main.py", archive.namelist())

    @unittest.skipIf(os.name == "nt", "POSIX mode bits and umask are required")
    def test_new_output_mode_follows_process_umask(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["src/"]
            ''')

            previous_umask = os.umask(0o027)
            try:
                output = build_archive(config, BuildRequest.create("./application/"))
            finally:
                os.umask(previous_umask)

            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o640)

    @unittest.skipIf(os.name == "nt", "POSIX mode bits and umask are required")
    def test_overwrite_uses_new_file_mode_instead_of_preserving_existing_mode(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            output = root / "out.zip"
            output.write_bytes(b"old")
            output.chmod(0o600)
            config = self._config(root, '''
                [pluck]
                must = ["src/"]
            ''', overwrite=True)

            previous_umask = os.umask(0o022)
            try:
                build_archive(config, BuildRequest.create("./application/"))
            finally:
                os.umask(previous_umask)

            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o644)

    def test_fixed_output_may_use_parent_or_absolute_path(self):
        with resolved_temporary_directory() as temp:
            workspace = Path(temp)
            root = workspace / "project"
            root.mkdir()
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")

            parent_config = self._config(root, '''
                [pluck]
                description = "Target."
                must = ["src/"]
                [output]
                path = "../parent.zip"
                overwrite = false
            ''')
            parent_output = build_archive(
                parent_config,
                BuildRequest.create("./application/"),
            )
            self.assertEqual(parent_output, workspace / "parent.zip")
            self.assertTrue(parent_output.is_file())

            absolute = workspace / "absolute.zip"
            absolute_config = self._config(root, f'''
                [pluck]
                description = "Target."
                must = ["src/"]
                [output]
                path = {absolute.as_posix()!r}
                overwrite = false
            ''')
            absolute_output = build_archive(
                absolute_config,
                BuildRequest.create("./application/"),
            )
            self.assertEqual(absolute_output, absolute)
            self.assertTrue(absolute_output.is_file())

    def test_sequence_is_rejected_for_fixed_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["src/"]
            """)
            with self.assertRaises(SelectionError):
                build_archive(
                    config,
                    BuildRequest.create("./application/", sequence=1),
                )

    def test_output_path_may_resolve_through_parent_symlink(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "application" / "src" / "main.py").write_text("x", encoding="utf-8")
            link = root / "artifacts"
            try:
                link.symlink_to(Path(other), target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [pluck]
                description = "Target."
                must = ["src/"]
            ''', output="artifacts/out.zip")
            output = build_archive(config, BuildRequest.create("./application/"))
            self.assertEqual(output, Path(other) / "out.zip")
            self.assertTrue((Path(other) / "out.zip").is_file())


if __name__ == "__main__":
    unittest.main()
