from pathlib import Path
import os
import unittest
from unittest.mock import patch
import zipfile

from tests._temp import resolved_temporary_directory
from tests._builder_support import BuilderTestCase

from dirpluck._builder_models import BuildRequest
from dirpluck._effective import resolve_sources
from dirpluck.builder import build_archive
from dirpluck.errors import SelectionError


class ArchiveTests(BuilderTestCase):
    def test_build_archive_clamps_pre_1980_source_timestamp(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "input.txt"
            source.write_text("payload\n", encoding="utf-8")
            os.utime(source, (0, 0))
            config = self._config(
                root,
                """
                [always.input]
                path = "."
                description = "Input."
                must = ["input.txt"]
            """,
            )

            output = build_archive(config, BuildRequest.create())

            with zipfile.ZipFile(output) as archive:
                entry = next(name for name in archive.namelist() if name.endswith("/input.txt"))
                info = archive.getinfo(entry)
                self.assertEqual(info.date_time[:3], (1980, 1, 1))
                self.assertEqual(archive.read(entry), b"payload\n")

    def test_build_archive_wraps_source_write_oserror_and_removes_temporary_file(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "input.txt"
            source.write_text("payload\n", encoding="utf-8")
            config = self._config(
                root,
                """
                [always.input]
                path = "."
                description = "Input."
                must = ["input.txt"]
            """,
            )

            with patch.object(zipfile.ZipFile, "write", side_effect=PermissionError("denied")):
                with self.assertRaisesRegex(SelectionError, "cannot add selected file to archive"):
                    build_archive(config, BuildRequest.create())

            self.assertFalse((root / "out.zip").exists())
            self.assertEqual(list(root.glob(".out.zip.*.tmp")), [])

    def test_archive_readme_includes_effective_about_description(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "application"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [about]
                description = "Materials prepared for an authentication review."

                [pluck]
                description = "Application sources."
                must = ["file.txt"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertTrue(
                readme.startswith(
                    "# Archive contents\n\n"
                    + "Materials prepared for an authentication review.\n\n"
                    + "## `application/`\n\n"
                    + "Files: 1\n\n"
                    + "Application sources.\n"
                )
            )

    def test_duplicate_archive_roots_from_target_and_always_are_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "src").mkdir(parents=True)
            (project / "dist").mkdir()
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            (project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
            config = self._config(
                root,
                """
                [pluck]
                description = "The project currently being changed."
                must = ["src/"]
                [always.devdoc]
                path = "shikumi-devdoc"
                description = "The current built distribution used as a reference."
                must = ["dist/shikumi_devdoc-*.whl"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "distinct archive roots"):
                resolve_sources(config, BuildRequest.create("./shikumi-devdoc/"))

    def test_namespace_keeps_colliding_source_roots_distinct_and_is_explained_in_readme(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "src").mkdir(parents=True)
            (project / "dist").mkdir()
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            (project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
            config = self._config(
                root,
                """
                [namespace.reference]

                [pluck]
                description = "The project currently being changed."
                must = ["src/"]

                [always.devdoc]
                path = "shikumi-devdoc"
                namespace = "reference"
                description = "The current built distribution used as a reference."
                must = ["dist/shikumi_devdoc-*.whl"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./shikumi-devdoc/"))
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("shikumi-devdoc/src/main.py", names)
            self.assertIn(
                "reference/shikumi-devdoc/dist/shikumi_devdoc-0.1.0-py3-none-any.whl",
                names,
            )
            self.assertIn("## `reference/shikumi-devdoc/`", readme)
            self.assertNotIn("Namespace:", readme)
            self.assertNotIn("Source root:", readme)
            self.assertIn("The current built distribution used as a reference.", readme)
            self.assertIn(
                "## `shikumi-devdoc/`\n\nFiles: 1\n\n" + "The project currently being changed.",
                readme,
            )

    def test_different_physical_files_at_same_archive_path_are_still_rejected(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "dist").mkdir(parents=True)
            target_wheel = project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl"
            target_wheel.write_bytes(b"target wheel")

            external = Path(other) / "dist"
            external.mkdir()
            (external / target_wheel.name).write_bytes(b"always wheel")

            config = self._config(
                root,
                f"""
                [namespace.shikumi-devdoc]

                [pluck]
                may = ["*", "*/"]

                [always.devdoc]
                path = {external.as_posix()!r}
                namespace = "shikumi-devdoc"
                must = ["*.whl"]
            """,
            )

            with self.assertRaisesRegex(
                SelectionError, "multiple files resolve to the same archive path"
            ):
                build_archive(config, BuildRequest.create("./shikumi-devdoc/"))

    def test_target_and_always_may_include_same_physical_file_at_different_archive_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "src").mkdir(parents=True)
            (project / "dist").mkdir()
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            wheel = project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl"
            wheel.write_bytes(b"wheel")
            config = self._config(
                root,
                """
                [namespace.devdoc]

                [pluck]
                description = "The project currently being changed."
                may = ["*", "*/"]

                [always.devdoc]
                path = "shikumi-devdoc/dist"
                namespace = "devdoc"
                description = "The built distribution used as a development tool."
                must = ["*.whl"]
            """,
            )

            output = build_archive(config, BuildRequest.create("./shikumi-devdoc/"))

            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("shikumi-devdoc/dist/shikumi_devdoc-0.1.0-py3-none-any.whl", names)
            self.assertIn(
                "devdoc/shikumi-devdoc/dist/shikumi_devdoc-0.1.0-py3-none-any.whl",
                names,
            )
            self.assertIn(
                "## `devdoc/shikumi-devdoc/dist/`\n\n"
                + "Files: 1\n"
                + "Target overlap: 1 selected file is also included under `shikumi-devdoc/`.\n\n"
                + "The built distribution used as a development tool.",
                readme,
            )

    def test_target_ignore_does_not_suppress_independent_always_selection(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "src").mkdir(parents=True)
            (project / "dist").mkdir()
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            wheel = project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl"
            wheel.write_bytes(b"wheel")
            config = self._config(
                root,
                """
                [namespace.devdoc]

                [pluck]
                may = ["*", "*/"]
                ignore = ["dist/"]

                [always.devdoc]
                path = "shikumi-devdoc/dist"
                namespace = "devdoc"
                description = "The built distribution used as a development tool."
                must = ["*.whl"]
            """,
            )

            output = build_archive(config, BuildRequest.create("./shikumi-devdoc/"))

            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                readme = archive.read("README.md").decode("utf-8")
            self.assertNotIn("shikumi-devdoc/dist/shikumi_devdoc-0.1.0-py3-none-any.whl", names)
            self.assertIn(
                "devdoc/shikumi-devdoc/dist/shikumi_devdoc-0.1.0-py3-none-any.whl",
                names,
            )
            self.assertNotIn("Target overlap:", readme)

    def test_archive_readme_hides_source_paths_by_default(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "application" / "src" / "main.py").write_text("x", encoding="utf-8")
            outside = Path(other) / "reference"
            outside.mkdir()
            (outside / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [pluck]
                description = "Application sources."
                must = ["src/"]

                [always.reference]
                path = {outside.as_posix()!r}
                description = "Reference material."
                must = ["guide.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `application/`", readme)
            self.assertIn("## `reference/`", readme)
            self.assertNotIn("Source:", readme)
            self.assertNotIn(root.as_posix(), readme)
            self.assertNotIn(outside.as_posix(), readme)

    def test_archive_readme_paths_option_includes_resolved_source_paths(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            target = root / "application"
            (target / "src").mkdir(parents=True)
            (target / "src" / "main.py").write_text("x", encoding="utf-8")
            outside = Path(other) / "reference"
            outside.mkdir()
            (outside / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [pluck]
                description = "Application sources."
                must = ["src/"]

                [always.reference]
                path = {outside.as_posix()!r}
                description = "Reference material."
                must = ["guide.md"]
            """,
            )
            output = build_archive(
                config,
                BuildRequest.create("./application/", paths=True),
            )
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn(f"Source: `{target.resolve().as_posix()}`", readme)
            self.assertIn(f"Source: `{outside.resolve().as_posix()}`", readme)
            self.assertNotIn("Configuration", readme)
            self.assertNotIn("Pluck", readme)
            self.assertNotIn("Always", readme)

    def test_archive_readme_omits_description_when_no_source_has_description(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "application"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["file.txt"]

                [always.docs]
                path = "docs"
                must = ["guide.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertEqual(
                readme,
                "# Archive contents\n\n"
                + "## `application/`\n\n"
                + "Files: 1\n\n"
                + "## `docs/`\n\n"
                + "Files: 1\n",
            )

    def test_archive_readme_preserves_multiline_source_description_as_section_body(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "application"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                r"""
                [pluck]
                description = "Primary review material.\n\nPay attention to compatibility | public API changes."
                must = ["file.txt"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn(
                "## `application/`\n\nFiles: 1\n\n"
                + "Primary review material.\n\n"
                + "Pay attention to compatibility | public API changes.",
                readme,
            )
            self.assertNotIn("| Path |", readme)

    def test_archive_readme_shows_description_only_for_sources_that_define_it(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "application"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["file.txt"]

                [always.docs]
                path = "docs"
                description = "Review guidance."
                must = ["guide.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `application/`\n\nFiles: 1", readme)
            self.assertIn("## `docs/`\n\nFiles: 1\n\nReview guidance.", readme)

    def test_archive_readme_namespaced_source_uses_final_archive_root_without_namespace_metadata(
        self,
    ):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [namespace.reference]

                [always.docs]
                path = "docs"
                namespace = "reference"
                must = ["guide.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `reference/docs/`", readme)
            self.assertIn("Files: 1", readme)
            self.assertNotIn("archive-only directory prefix", readme)
            self.assertNotIn("Namespace:", readme)
            self.assertNotIn("Source root:", readme)


if __name__ == "__main__":
    unittest.main()
