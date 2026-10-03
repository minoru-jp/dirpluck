from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
import os
import unittest
from unittest.mock import patch
import zipfile

from tests._temp import resolved_temporary_directory

import dirpluck
from dirpluck._archive_mtime import resolve_archive_mtime, validate_archive_mtime_spec
from dirpluck._builder_models import ArchivePlan
from dirpluck._output import _write_archive
from dirpluck.cli import main


class ArchiveMtimeTests(unittest.TestCase):
    def test_archive_mtime_spec_accepts_keywords_and_strict_timestamp(self):
        self.assertEqual(validate_archive_mtime_spec("now"), "now")
        self.assertEqual(validate_archive_mtime_spec("zip-epoch"), "zip-epoch")
        self.assertEqual(
            validate_archive_mtime_spec("2026-01-02T03:04:05"),
            "2026-01-02T03:04:05",
        )

    def test_archive_mtime_spec_rejects_invalid_forms_and_zip_range(self):
        for value in (
            "",
            "auto",
            "1970-01-01T00:00:00",
            "2108-01-01T00:00:00",
            "2026-1-02T03:04:05",
            "2026-01-02 03:04:05",
            "2026-01-02T03:04:05Z",
            123,
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_archive_mtime_spec(value)

    def test_archive_mtime_spec_rejects_non_ascii_digits(self):
        with self.assertRaises(ValueError):
            validate_archive_mtime_spec("２０２６-01-02T03:04:05")

    def test_archive_mtime_spec_rejects_nonexistent_calendar_date(self):
        with self.assertRaisesRegex(ValueError, "invalid archive mtime timestamp"):
            validate_archive_mtime_spec("2026-02-30T00:00:00")

    def test_explicit_archive_mtime_is_floored_to_zip_two_second_grid(self):
        self.assertEqual(
            resolve_archive_mtime("2026-01-02T03:04:05"),
            datetime(2026, 1, 2, 3, 4, 4),
        )

    def test_now_is_sampled_once_and_floored(self):
        current = datetime(2026, 9, 21, 17, 35, 57, 900000)
        with patch("dirpluck._archive_mtime._current_local_time", return_value=current) as clock:
            resolved = resolve_archive_mtime("now")
        self.assertEqual(resolved, datetime(2026, 9, 21, 17, 35, 56))
        clock.assert_called_once_with()

    def test_fixed_archive_mtime_applies_to_generated_and_source_entries(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            source.write_text("source\n", encoding="utf-8")
            os.utime(source, (946684800, 946684800))
            plan = ArchivePlan(
                entries={"data/source.txt": source},
                readme="# Archive contents\n",
                empty_directories=("empty",),
            )
            timestamp = datetime(2026, 1, 2, 3, 4, 56)
            output = _write_archive(
                plan,
                root / "out.zip",
                False,
                archive_mtime=timestamp,
            )

            with zipfile.ZipFile(output) as archive:
                self.assertEqual(
                    {info.filename: info.date_time for info in archive.infolist()},
                    {
                        "README.md": (2026, 1, 2, 3, 4, 56),
                        "empty/": (2026, 1, 2, 3, 4, 56),
                        "data/source.txt": (2026, 1, 2, 3, 4, 56),
                    },
                )

    def test_zip_epoch_produces_identical_bytes_when_source_mtime_changes(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            source.write_text("same bytes\n", encoding="utf-8")
            plan = ArchivePlan(
                entries={"source.txt": source},
                readme="# Archive contents\n",
            )
            timestamp = resolve_archive_mtime("zip-epoch")
            self.assertIsNotNone(timestamp)

            os.utime(source, (946684800, 946684800))
            first = _write_archive(
                plan,
                root / "first.zip",
                False,
                archive_mtime=timestamp,
            ).read_bytes()

            os.utime(source, (1893456000, 1893456000))
            second = _write_archive(
                plan,
                root / "second.zip",
                False,
                archive_mtime=timestamp,
            ).read_bytes()

            self.assertEqual(first, second)

    @unittest.skipUnless(os.name == "posix", "requires POSIX permission bits")
    def test_zip_epoch_does_not_normalize_source_permission_bits(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            source.write_text("same bytes\n", encoding="utf-8")
            plan = ArchivePlan(
                entries={"source.txt": source},
                readme="# Archive contents\n",
            )
            timestamp = resolve_archive_mtime("zip-epoch")
            self.assertIsNotNone(timestamp)

            source.chmod(0o644)
            first_path = _write_archive(
                plan,
                root / "first-mode.zip",
                False,
                archive_mtime=timestamp,
            )
            first = first_path.read_bytes()
            with zipfile.ZipFile(first_path) as archive:
                first_mode = (archive.getinfo("source.txt").external_attr >> 16) & 0o777

            source.chmod(0o755)
            second_path = _write_archive(
                plan,
                root / "second-mode.zip",
                False,
                archive_mtime=timestamp,
            )
            second = second_path.read_bytes()
            with zipfile.ZipFile(second_path) as archive:
                second_mode = (archive.getinfo("source.txt").external_attr >> 16) & 0o777

            self.assertEqual(first_mode, 0o644)
            self.assertEqual(second_mode, 0o755)
            self.assertNotEqual(first, second)

    def test_public_run_uses_zip_epoch_for_every_entry(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                """\n[pluck]\nmust = ["src/"]\n\n[output]\npath = "result.zip"\noverwrite = true\n""",
                encoding="utf-8",
            )

            result = dirpluck.run("./app/", archive_mtime="zip-epoch", cwd=root)
            self.assertIsNotNone(result.output_path)
            assert result.output_path is not None
            with zipfile.ZipFile(result.output_path) as archive:
                self.assertEqual(
                    {info.date_time for info in archive.infolist()},
                    {(1980, 1, 1, 0, 0, 0)},
                )

    def test_now_is_sampled_once_for_a_public_run_and_applied_to_all_entries(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                """
[pluck]
must = ["src/"]

[output]
path = "result.zip"
overwrite = true
""",
                encoding="utf-8",
            )
            current = datetime(2026, 9, 21, 17, 35, 57, 900000)
            with patch(
                "dirpluck._archive_mtime._current_local_time",
                return_value=current,
            ) as clock:
                result = dirpluck.run("./app/", archive_mtime="now", cwd=root)

            clock.assert_called_once_with()
            self.assertIsNotNone(result.output_path)
            assert result.output_path is not None
            with zipfile.ZipFile(result.output_path) as archive:
                self.assertEqual(
                    {info.date_time for info in archive.infolist()},
                    {(2026, 9, 21, 17, 35, 56)},
                )

    def test_cli_archive_mtime_option_reaches_archive_writer(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                """
[pluck]
must = ["src/"]

[output]
path = "result.zip"
overwrite = true
""",
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with redirect_stdout(StringIO()):
                    code = main(["./app/", "--archive-mtime", "zip-epoch"])
            finally:
                os.chdir(previous)
            self.assertEqual(code, 0)
            with zipfile.ZipFile(root / "result.zip") as archive:
                self.assertEqual(
                    {info.date_time for info in archive.infolist()},
                    {(1980, 1, 1, 0, 0, 0)},
                )

    def test_invocation_archive_mtime_is_used_when_not_overridden(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                """\n[pluck]\nmust = ["src/"]\n\n[output]\npath = "result.zip"\noverwrite = true\n""",
                encoding="utf-8",
            )
            (root / "release.dirpluck-inv").write_text(
                """\n[invocation]\ntargets = ["./app/"]\narchive_mtime = "zip-epoch"\n""",
                encoding="utf-8",
            )

            result = dirpluck.run(invocation="release", cwd=root)
            self.assertIsNotNone(result.output_path)
            assert result.output_path is not None
            with zipfile.ZipFile(result.output_path) as archive:
                self.assertEqual(
                    {info.date_time for info in archive.infolist()},
                    {(1980, 1, 1, 0, 0, 0)},
                )

    def test_cli_style_archive_mtime_overrides_invocation_value(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "app" / "src").mkdir(parents=True)
            (root / "app" / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
            (root / "default.dirpluck").write_text(
                """\n[pluck]\nmust = ["src/"]\n\n[output]\npath = "result.zip"\noverwrite = true\n""",
                encoding="utf-8",
            )
            (root / "release.dirpluck-inv").write_text(
                """\n[invocation]\ntargets = ["./app/"]\narchive_mtime = "zip-epoch"\n""",
                encoding="utf-8",
            )

            result = dirpluck.run(
                invocation="release",
                archive_mtime="2026-01-02T03:04:05",
                cwd=root,
            )
            self.assertIsNotNone(result.output_path)
            assert result.output_path is not None
            with zipfile.ZipFile(result.output_path) as archive:
                self.assertEqual(
                    {info.date_time for info in archive.infolist()},
                    {(2026, 1, 2, 3, 4, 4)},
                )


if __name__ == "__main__":
    unittest.main()
