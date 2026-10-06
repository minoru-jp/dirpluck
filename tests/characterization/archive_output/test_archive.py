from pathlib import Path
import os
import unittest
from unittest.mock import patch
import zipfile

from tests._temp import resolved_temporary_directory
from tests._pipeline import build_archive, resolve_sources
from tests._builder_support import BuilderTestCase

from dirpluck._archive_payload import ArchivePayload
from dirpluck._output import write_archive
from dirpluck._request_models import BuildRequest
from dirpluck.errors import SelectionError


class ArchiveTests(BuilderTestCase):
    def test_write_archive_wraps_generated_readme_oserror_and_removes_temporary_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            output = root / "out.zip"
            payload = ArchivePayload(entries={}, readme="# Archive contents\n")

            with patch.object(
                zipfile.ZipFile,
                "writestr",
                side_effect=PermissionError("denied"),
            ):
                with self.assertRaisesRegex(
                    SelectionError,
                    r"cannot add generated entry to archive: README\.md",
                ):
                    write_archive(payload, output, False)

            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".out.zip.*")), [])

    def test_write_archive_wraps_empty_directory_oserror_and_removes_temporary_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            output = root / "out.zip"
            payload = ArchivePayload(
                entries={},
                readme="# Archive contents\n",
                empty_directories=("empty",),
            )

            with patch.object(
                zipfile.ZipFile,
                "writestr",
                side_effect=[None, PermissionError("denied")],
            ):
                with self.assertRaisesRegex(
                    SelectionError,
                    r"cannot add generated entry to archive: empty/",
                ):
                    write_archive(payload, output, False)

            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".out.zip.*")), [])

    def test_build_archive_clamps_pre_1980_source_timestamp(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "input.txt"
            source.write_bytes(b"payload\n")
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
                    + '`Scope: "..."` identifies only the selection range used to find Targets; '
                )
            )
            self.assertIn("#### Pluck\n\nApplication sources.", readme)
            self.assertIn("##### `application/`\n\nFiles: 1", readme)

    def test_target_and_always_must_not_share_exact_archive_root(self):
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
                [always.shikumi-devdoc]
                path = "shikumi-devdoc"
                description = "The current built distribution used as a reference."
                must = ["dist/shikumi_devdoc-*.whl"]
            """,
            )
            with self.assertRaisesRegex(
                SelectionError, "resolved sources must have distinct archive roots"
            ):
                resolve_sources(config, BuildRequest.create("./shikumi-devdoc/"))

    def test_target_and_always_roots_that_differ_only_by_case_are_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "App"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            always_root = root / "support"
            always_root.mkdir()
            (always_root / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [always.app]
                path = "support"
                must = ["guide.md"]
            """,
            )
            with self.assertRaisesRegex(
                SelectionError,
                "choose distinct archive roots",
            ):
                resolve_sources(config, BuildRequest.create("./App/"))

    def test_always_name_keeps_colliding_source_roots_distinct_and_is_explained_in_readme(self):
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

                [always.reference]
                path = "shikumi-devdoc"
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
                "reference/dist/shikumi_devdoc-0.1.0-py3-none-any.whl",
                names,
            )
            self.assertIn("## `reference/`", readme)
            self.assertNotIn("Namespace:", readme)
            self.assertNotIn("Source root:", readme)
            self.assertIn("The current built distribution used as a reference.", readme)
            self.assertIn("#### Pluck\n\nThe project currently being changed.", readme)
            self.assertIn("##### `shikumi-devdoc/`\n\nFiles: 1", readme)

    def test_shared_target_and_always_root_still_detects_entry_collision(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "dist").mkdir(parents=True)
            target_wheel = project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl"
            target_wheel.write_bytes(b"target wheel")

            external = Path(other) / "shikumi-devdoc"
            (external / "dist").mkdir(parents=True)
            (external / "dist" / target_wheel.name).write_bytes(b"always wheel")

            config = self._config(
                root,
                f"""
                [pluck]
                may = ["*", "*/"]

                [always.shikumi-devdoc]
                path = {external.as_posix()!r}
                must = ["dist/*.whl"]
            """,
            )

            with self.assertRaisesRegex(
                SelectionError,
                "resolved sources must have distinct archive roots",
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
                [pluck]
                description = "The project currently being changed."
                may = ["*", "*/"]

                [always.devdoc]
                path = "shikumi-devdoc/dist"
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
                "devdoc/shikumi_devdoc-0.1.0-py3-none-any.whl",
                names,
            )
            self.assertIn(
                "## `devdoc/`\n\n"
                + "The built distribution used as a development tool.\n\n"
                + "Files: 1\n"
                + "Target overlap: 1 selected file is also included under `shikumi-devdoc/`.",
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
                [pluck]
                may = ["*", "*/"]
                ignore = ["dist/"]

                [always.devdoc]
                path = "shikumi-devdoc/dist"
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
                "devdoc/shikumi_devdoc-0.1.0-py3-none-any.whl",
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
            self.assertIn("#### Pluck", readme)
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
                + '`Scope: "..."` identifies only the selection range used to find Targets; '
                + "it does not imply priority, importance, or hierarchy. Any additional meaning "
                + "is stated in that Scope's description.\n\n"
                + "## `docs/`\n\n"
                + "Files: 1\n\n"
                + "## Targets\n\n"
                + "### Scope: (unnamed)\n\n"
                + "#### Pluck\n\n"
                + "##### `application/`\n\n"
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
                "#### Pluck\n\n"
                + "Primary review material.\n\n"
                + "Pay attention to compatibility | public API changes.\n\n"
                + "##### `application/`\n\nFiles: 1",
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
            self.assertIn("##### `application/`\n\nFiles: 1", readme)
            self.assertIn("## `docs/`\n\nReview guidance.\n\nFiles: 1", readme)

    def test_archive_readme_uses_always_name_as_final_archive_root(
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
                [always.reference]
                path = "docs"
                must = ["guide.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `reference/`", readme)
            self.assertIn("Files: 1", readme)
            self.assertNotIn("archive-only directory prefix", readme)
            self.assertNotIn("Namespace:", readme)
            self.assertNotIn("Source root:", readme)

    def test_archive_readme_uses_source_presence_specific_about_descriptions(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [about]
                description = "Common description."
                description_no_targets = "There are no Targets."
                description_no_always = "There are no Always sources."
                description_empty = "There are no sources."

                [always.docs]
                path = "docs"
                must = ["guide.md"]
                """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Common description.", readme)
            self.assertIn("There are no Targets.", readme)
            self.assertNotIn("There are no Always sources.", readme)
            self.assertNotIn("There are no sources.", readme)

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "app"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [about]
                description = "Common description."
                description_no_targets = "There are no Targets."
                description_no_always = "There are no Always sources."
                description_empty = "There are no sources."

                [pluck]
                must = ["file.txt"]
                """,
            )
            output = build_archive(config, BuildRequest.create("./app/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Common description.", readme)
            self.assertIn("There are no Always sources.", readme)
            self.assertNotIn("There are no Targets.", readme)
            self.assertNotIn("There are no sources.", readme)

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = self._config(
                root,
                """
                [about]
                description = "Common description."
                description_no_targets = "There are no Targets."
                description_no_always = "There are no Always sources."
                description_empty = "There are no sources."
                """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Common description.", readme)
            self.assertIn("There are no sources.", readme)
            self.assertNotIn("There are no Targets.", readme)
            self.assertNotIn("There are no Always sources.", readme)
            self.assertIn("This Archive contains only `README.md`.", readme)

    def test_allow_empty_source_still_counts_for_conditional_description_presence(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            config = self._config(
                root,
                """
                [about]
                description_no_targets = "Always is present."
                description_empty = "No sources."

                [always.docs]
                path = "docs"
                may = ["*.md"]
                allow_empty = true
                """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Always is present.", readme)
            self.assertNotIn("No sources.", readme)

    def test_archive_readme_omits_conditional_description_when_both_roles_exist(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "app"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [about]
                description = "Common description."
                description_no_targets = "NO TARGETS"
                description_no_always = "NO ALWAYS"
                description_empty = "EMPTY"

                [pluck]
                must = ["file.txt"]

                [always.docs]
                path = "docs"
                must = ["guide.md"]
                """,
            )
            output = build_archive(config, BuildRequest.create("./app/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Common description.", readme)
            self.assertNotIn("NO TARGETS", readme)
            self.assertNotIn("NO ALWAYS", readme)
            self.assertNotIn("EMPTY", readme)

    def test_layouts_place_sources_under_declared_directories_and_describe_used_layouts(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            target = root / "app"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            dist = root / "dist"
            dist.mkdir()
            (dist / "tool.whl").write_bytes(b"wheel")
            config = self._config(
                root,
                """
                [about]
                always_layout = "dependencies"
                targets_layout = "development-targets"

                [layout.dependencies]
                description = "Install these dependencies first."

                [layout.development-targets]
                description = "These are the development Targets."

                [layout.unused]
                description = "This must not appear."

                [pluck]
                must = ["file.txt"]

                [always.wheels]
                path = "dist"
                must = ["*.whl"]
                """,
            )
            output = build_archive(config, BuildRequest.create("./app/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("dependencies/wheels/tool.whl", names)
            self.assertIn("development-targets/app/file.txt", names)
            self.assertIn("## Layouts", readme)
            self.assertIn("### `dependencies/`", readme)
            self.assertIn("Install these dependencies first.", readme)
            self.assertIn("### `development-targets/`", readme)
            self.assertIn("These are the development Targets.", readme)
            self.assertNotIn("This must not appear.", readme)
            self.assertIn("## `dependencies/wheels/`", readme)
            self.assertIn("##### `development-targets/app/`", readme)

    def test_layout_without_description_is_valid_and_unused_layout_creates_no_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [about]
                always_layout = "dependencies"

                [layout.dependencies]
                [layout.unused]

                [always.docs]
                path = "docs"
                must = ["guide.md"]
                """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("dependencies/docs/guide.md", names)
            self.assertFalse(any(name.startswith("unused/") for name in names))
            self.assertNotIn("## Layouts", readme)


if __name__ == "__main__":
    unittest.main()
