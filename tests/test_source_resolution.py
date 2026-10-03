from pathlib import Path
import os
import subprocess
import unittest
import zipfile

from tests._temp import resolved_temporary_directory
from tests._builder_support import BuilderTestCase

from dirpluck._archive import plan_archive
from dirpluck._builder_models import BuildRequest
from dirpluck._effective import resolve_sources
from dirpluck.builder import build_archive
from dirpluck.errors import SelectionError


class SourceResolutionTests(BuilderTestCase):
    def test_target_and_always_source_preserve_configuration_relative_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "common", "a")
            self._project(root, "b/common", "b")
            config = self._config(
                root,
                """
                [pluck]
                description = "Target."
                must = ["src/"]
                [always.other]
                path = "b/common"
                description = "Always source."
                must = ["src/"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./common/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("common/src/module.py", names)
            self.assertIn("b/common/src/module.py", names)

    def test_always_parent_path_outside_configuration_uses_resolved_directory_name(self):
        with resolved_temporary_directory() as temp:
            workspace = Path(temp)
            root = workspace / "project"
            external = workspace / "references"
            root.mkdir()
            external.mkdir()
            (external / "note.txt").write_text("reference", encoding="utf-8")
            config = self._config(
                root,
                """
                [always.references]
                path = "../references"
                description = "External references."
                must = ["note.txt"]
            """,
            )
            sources = resolve_sources(config, BuildRequest.create())
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, external.resolve())
            self.assertEqual(sources[0].archive_root, "references")
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("references/note.txt", plan.entries)

    def test_always_absolute_path_inside_configuration_preserves_relative_archive_root(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            companion = root / "nested" / "references"
            companion.mkdir(parents=True)
            (companion / "note.txt").write_text("reference", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [always.references]
                path = {companion.as_posix()!r}
                description = "References."
                must = ["note.txt"]
            """,
            )
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.archive_root, "nested/references")

    def test_always_absolute_path_outside_configuration_uses_resolved_directory_name(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            external = Path(other) / "references"
            external.mkdir()
            (external / "note.txt").write_text("reference", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [always.references]
                path = {external.as_posix()!r}
                description = "References."
                must = ["note.txt"]
            """,
            )
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.directory, external.resolve())
            self.assertEqual(source.archive_root, "references")
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("references/note.txt", plan.entries)

    def test_named_scope_root_may_be_a_directory_symlink(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            external = Path(other) / "workspace"
            project = external / "project"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            alias = root / "work"
            try:
                alias.symlink_to(external, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            config = self._config(
                root,
                """
                [pluck]
                description = "Project."
                must = ["src/"]

                [scope.work]
                path = "work"
            """,
            )
            sources = resolve_sources(config, BuildRequest.create("work/project/"))
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, project.resolve())
            self.assertEqual(sources[0].archive_root, "project")

    def test_always_source_root_may_be_a_directory_symlink(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            external = Path(other) / "review-guidelines"
            external.mkdir()
            (external / "rules.md").write_text("rules\n", encoding="utf-8")
            alias = root / "guidelines"
            try:
                alias.symlink_to(external, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            config = self._config(
                root,
                """
                [always.guidelines]
                path = "guidelines"
                description = "Guidelines."
                must = ["rules.md"]
            """,
            )
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.directory, external.resolve())
            self.assertEqual(source.archive_root, "guidelines")
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("guidelines/rules.md", plan.entries)

    def test_always_source_root_alias_does_not_enable_nested_link_traversal(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            external = Path(other) / "review-guidelines"
            external.mkdir()
            (external / "rules.md").write_text("rules\n", encoding="utf-8")
            outside = Path(other) / "outside"
            outside.mkdir()
            (outside / "secret.md").write_text("secret\n", encoding="utf-8")
            nested_link = external / "external"
            alias = root / "guidelines"
            try:
                nested_link.symlink_to(outside, target_is_directory=True)
                alias.symlink_to(external, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            config = self._config(
                root,
                """
                [always.guidelines]
                path = "guidelines"
                description = "Guidelines."
                must = ["rules.md"]
                may = ["external/"]
            """,
            )
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("guidelines/rules.md", plan.entries)
            self.assertNotIn("guidelines/external/secret.md", plan.entries)
            self.assertEqual(plan.skipped_link_count, 1)

    def test_multiple_runtime_targets_use_the_same_target_selection(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project-a", "a")
            self._project(root, "project-b", "b")
            config = self._config(
                root,
                """
                [pluck]
                description = "Projects selected for review."
                must = ["src/"]
            """,
            )
            output = build_archive(
                config,
                BuildRequest.create("./project-a/", "./project-b/"),
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("project-a/src/module.py", names)
            self.assertIn("project-b/src/module.py", names)
            self.assertIn("## `project-a/`\n\nFiles: 6\n\nProjects selected for review.", readme)
            self.assertIn("## `project-b/`\n\nFiles: 6\n\nProjects selected for review.", readme)
            self.assertNotIn("Source:", readme)

    def test_multiple_runtime_targets_use_the_same_named_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for name in ("project-a", "project-b"):
                project = root / name
                (project / "src").mkdir(parents=True)
                (project / "tests").mkdir()
                (project / "src" / "main.py").write_text("src", encoding="utf-8")
                (project / "tests" / "test_main.py").write_text("test", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                description = "Default projects."
                must = ["src/"]

                [pluck.case.review]
                description = "Projects prepared for review."
                must = ["tests/"]
            """,
            )
            output = build_archive(
                config,
                BuildRequest.create("./project-a/", "./project-b/", case="review"),
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("project-a/tests/test_main.py", names)
            self.assertIn("project-b/tests/test_main.py", names)
            self.assertNotIn("project-a/src/main.py", names)
            self.assertNotIn("project-b/src/main.py", names)

    def test_duplicate_runtime_targets_are_rejected_after_resolution(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project", "a")
            config = self._config(
                root,
                """
                [pluck]
                description = "Target."
                must = ["src/"]
            """,
            )
            with self.assertRaises(SelectionError):
                resolve_sources(
                    config,
                    BuildRequest.create("./project/", "project"),
                )

    def test_target_cannot_be_current_working_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            config = self._config(
                root,
                """
                [pluck]
                description = "Target cwd."
                must = ["src/"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "direct child"):
                resolve_sources(config, BuildRequest.create("."))

    def test_pluck_case_selects_only_named_case_without_inheritance(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "src").mkdir(parents=True)
            (project / "tests").mkdir()
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            (project / "tests" / "test_main.py").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                description = "Default source."
                must = ["src/"]
                [pluck.case.review]
                description = "Review tests only."
                must = ["tests/"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/", case="review"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("application/tests/test_main.py", names)
            self.assertNotIn("application/src/main.py", names)
            self.assertIn("## `application/`\n\nFiles: 1\n\nReview tests only.", readme)
            self.assertNotIn("Case:", readme)
            self.assertNotIn("[target", readme)

    def test_default_case_uses_pluck_table(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                description = "Default source."
                must = ["src/"]
                [pluck.case.review]
                description = "Review."
                must = ["tests/"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `application/`\n\nFiles: 1\n\nDefault source.", readme)
            self.assertNotIn("Case:", readme)
            self.assertNotIn("[pluck]", readme)

    def test_missing_default_requires_explicit_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(
                root,
                """
                [pluck.case.review]
                description = "Review."
                must = ["src/"]
            """,
            )
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("./application/"))

    def test_unknown_case_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [pluck.case.review]
                description = "Review."
                must = ["src/"]
            """,
            )
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("./application/", case="release"))

    def test_always_case_overrides_selection_and_other_always_falls_back(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "application" / "tests").mkdir()
            (root / "application" / "tests" / "test_app.py").write_text("x", encoding="utf-8")
            (root / "framework" / "src").mkdir(parents=True)
            (root / "framework" / "tests").mkdir()
            (root / "framework" / "src" / "core.py").write_text("x", encoding="utf-8")
            (root / "framework" / "tests" / "test_core.py").write_text("x", encoding="utf-8")
            (root / "guidelines").mkdir()
            (root / "guidelines" / "README.md").write_text("guide", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                description = "Default target."
                must = ["src/"]

                [pluck.case.review]
                description = "Review target."
                must = ["tests/"]

                [always.framework]
                path = "framework"
                description = "Default framework."
                must = ["src/"]

                [always.framework.case.review]
                description = "Framework review material."
                must = ["tests/"]

                [always.guidelines]
                path = "guidelines"
                description = "Guidelines always included."
                must = ["README.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create("./application/", case="review"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("application/tests/test_app.py", names)
            self.assertIn("framework/tests/test_core.py", names)
            self.assertNotIn("framework/src/core.py", names)
            self.assertIn("guidelines/README.md", names)
            self.assertIn("## `framework/`\n\nFiles: 1\n\nFramework review material.", readme)
            self.assertIn("## `guidelines/`\n\nFiles: 1\n\nGuidelines always included.", readme)
            self.assertNotIn("companion", readme.lower())

    def test_always_only_configuration_builds_without_target_reference(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "contracts").mkdir()
            (root / "notes").mkdir()
            (root / "contracts" / "a.pdf").write_bytes(b"pdf")
            (root / "notes" / "meeting.md").write_text("notes", encoding="utf-8")
            config = self._config(
                root,
                """
                [always.contracts]
                path = "contracts"
                description = "Contracts."
                must = ["*.pdf"]

                [always.notes]
                path = "notes"
                description = "Notes."
                must = ["*.md"]
            """,
            )
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertEqual(
                names,
                {"README.md", "contracts/a.pdf", "notes/meeting.md"},
            )

    def test_always_only_case_uses_override_and_default_fallback(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "documents" / "current").mkdir(parents=True)
            (root / "documents" / "history").mkdir()
            (root / "documents" / "current" / "now.md").write_text("now", encoding="utf-8")
            (root / "documents" / "history" / "old.md").write_text("old", encoding="utf-8")
            (root / "assets").mkdir()
            (root / "assets" / "figure.png").write_bytes(b"png")
            config = self._config(
                root,
                """
                [always.documents]
                path = "documents"
                description = "Current documents."
                must = ["current/"]

                [always.documents.case.archive]
                description = "Archive documents."
                must = ["current/", "history/"]

                [always.assets]
                path = "assets"
                description = "Assets."
                must = ["*.png"]
            """,
            )
            output = build_archive(config, BuildRequest.create(case="archive"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("documents/current/now.md", names)
            self.assertIn("documents/history/old.md", names)
            self.assertIn("assets/figure.png", names)
            self.assertIn("## `documents/`\n\nFiles: 2\n\nArchive documents.", readme)
            self.assertIn("## `assets/`\n\nFiles: 1\n\nAssets.", readme)
            self.assertNotIn("Case:", readme)
            self.assertNotIn("companion", readme.lower())

    def test_pluck_presence_and_target_reference_must_match(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            target_config = self._config(
                root,
                """
                [pluck]
                description = "Target."
                must = ["src/"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "TARGET is required"):
                resolve_sources(target_config, BuildRequest.create())

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            (root / "documents" / "a.txt").write_text("a", encoding="utf-8")
            companion_config = self._config(
                root,
                """
                [always.documents]
                path = "documents"
                description = "Documents."
                must = ["*.txt"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "must not be specified"):
                resolve_sources(companion_config, BuildRequest.create("./documents/"))

    def test_always_only_unknown_case_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            config = self._config(
                root,
                """
                [always.documents]
                path = "documents"
                description = "Documents."
                may = ["*.md"]
                allow_empty = true

                [always.documents.case.archive]
                description = "Archive documents."
                may = ["*.md"]
                allow_empty = true
            """,
            )
            with self.assertRaisesRegex(SelectionError, "case 'review' is not defined"):
                resolve_sources(config, BuildRequest.create(case="review"))

    def test_external_always_sources_with_same_archive_root_require_namespace(self):
        with (
            resolved_temporary_directory() as temp,
            resolved_temporary_directory() as a_temp,
            resolved_temporary_directory() as b_temp,
        ):
            root = Path(temp)
            a_docs = Path(a_temp) / "docs"
            b_docs = Path(b_temp) / "docs"
            a_docs.mkdir()
            b_docs.mkdir()
            (a_docs / "a.txt").write_text("a", encoding="utf-8")
            (b_docs / "b.txt").write_text("b", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [always.a]
                path = {a_docs.as_posix()!r}
                description = "A docs."
                must = ["a.txt"]

                [always.b]
                path = {b_docs.as_posix()!r}
                description = "B docs."
                must = ["b.txt"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "both resolve to 'docs'"):
                resolve_sources(config, BuildRequest.create())

    def test_source_root_cannot_collide_with_generated_archive_readme(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "README.md"
            source.mkdir()
            (source / "x.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [always.index]
                path = "README.md"
                description = "Reserved root."
                must = ["x.txt"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "reserved archive root 'README.md'"):
                resolve_sources(config, BuildRequest.create())

    def test_namespace_cannot_place_source_under_generated_archive_readme(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "docs"
            source.mkdir()
            (source / "x.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [namespace."readme.MD"]

                [always.docs]
                path = "docs"
                namespace = "readme.MD"
                description = "Docs."
                must = ["x.txt"]
            """,
            )
            with self.assertRaisesRegex(SelectionError, "reserved archive root 'readme.MD'"):
                resolve_sources(config, BuildRequest.create())

    def test_absolute_target_reference_is_rejected(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            outside = Path(other) / "outside"
            (outside / "src").mkdir(parents=True)
            config = self._config(
                root,
                """
                [pluck]
                description = "Target."
                must = ["src/"]
            """,
            )
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create(outside))

    def test_named_scope_resolves_direct_child_without_exposing_scope_name(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            projects = Path(other) / "projects"
            target = projects / "app"
            (target / "src").mkdir(parents=True)
            (target / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [pluck]
                description = "Application."
                must = ["src/"]

                [scope.work]
                path = {projects.as_posix()!r}
            """,
            )
            sources = resolve_sources(config, BuildRequest.create("work/app/"))
            target_source = next(source for source in sources if source.kind == "target")
            self.assertEqual(target_source.directory, target.resolve())
            self.assertEqual(target_source.archive_root, "app")
            plan = plan_archive(config, BuildRequest.create("work/app/"))
            self.assertIn("app/src/main.py", plan.entries)
            self.assertFalse(any(path.startswith("work/") for path in plan.entries))

    def test_dot_slash_target_reference_explicitly_addresses_default_scope(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "project" / "src").mkdir(parents=True)
            (root / "artifact.bin").write_bytes(b"x")
            config = self._config(
                root,
                """
                [pluck]
                description = "Application."
                must = ["src/"]

                [scope]
                target_kind = "both"
            """,
            )
            directory = resolve_sources(config, BuildRequest.create("./project/"))[0]
            file_source = resolve_sources(config, BuildRequest.create("./artifact.bin"))[0]
            self.assertEqual(
                (directory.source_root, directory.source_kind), ("project", "directory")
            )
            self.assertEqual(
                (file_source.source_root, file_source.source_kind), ("artifact.bin", "file")
            )

    def test_scope_expansion_selects_only_direct_child_directories(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            projects = Path(other) / "projects"
            for name in ("alpha", "beta"):
                (projects / name / "src").mkdir(parents=True)
                (projects / name / "src" / f"{name}.py").write_text(name, encoding="utf-8")
            (projects / "alpha" / "nested" / "src").mkdir(parents=True)
            (projects / "note.txt").write_text("not a target", encoding="utf-8")
            config = self._config(
                root,
                f"""
                [pluck]
                description = "Project."
                must = ["src/"]

                [scope.work]
                path = {projects.as_posix()!r}
            """,
            )
            sources = resolve_sources(config, BuildRequest.create("work/"))
            targets = [source for source in sources if source.kind == "target"]
            self.assertEqual([source.archive_root for source in targets], ["alpha", "beta"])
            plan = plan_archive(config, BuildRequest.create("work/"))
            self.assertIn("alpha/src/alpha.py", plan.entries)
            self.assertIn("beta/src/beta.py", plan.entries)
            self.assertFalse(any(path.startswith("alpha/nested/") for path in plan.entries))

    def test_scope_expansion_requires_defined_nonempty_scope(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            projects = Path(other) / "projects"
            projects.mkdir()
            config = self._config(
                root,
                f"""
                [pluck]
                description = "Project."
                may = ["src"]
                allow_empty = true

                [scope.work]
                path = {projects.as_posix()!r}
            """,
            )
            with self.assertRaisesRegex(SelectionError, "not defined"):
                resolve_sources(config, BuildRequest.create("other/"))
            with self.assertRaisesRegex(SelectionError, "no eligible direct child directories"):
                resolve_sources(config, BuildRequest.create("work/"))

    def test_scope_expansion_skips_directory_symlinks(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            projects = root / "projects"
            projects.mkdir()
            real = projects / "real"
            real.mkdir()
            outside = Path(other) / "outside"
            outside.mkdir()
            link = projects / "escape"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(
                root,
                """
                [pluck]
                description = "Project."
                may = ["src"]
                allow_empty = true

                [scope.work]
                path = "projects"
            """,
            )
            sources = resolve_sources(config, BuildRequest.create("work/"))
            self.assertEqual(tuple(source.archive_root for source in sources), ("real",))

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics are Windows-specific")
    def test_windows_directory_junction_may_be_an_explicit_always_root(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            external = Path(other) / "review-guidelines"
            external.mkdir()
            (external / "rules.md").write_text("rules\n", encoding="utf-8")
            junction = root / "guidelines"
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(external)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                self.fail(
                    f"could not create Windows directory junction: {created.stderr or created.stdout}"
                )

            config = self._config(
                root,
                """
                [always.guidelines]
                path = "guidelines"
                description = "Guidelines."
                must = ["rules.md"]
            """,
            )
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.directory, external.resolve())
            self.assertEqual(source.archive_root, "guidelines")
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("guidelines/rules.md", plan.entries)

    def test_file_target_scope_selects_atomic_files_without_pluck(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            first = returned / "repo-a.zip"
            second = returned / "repo-b.zip"
            first.write_bytes(b"a")
            second.write_bytes(b"b")
            (returned / "nested").mkdir()
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
                description = "Repositories returned from the previous editing cycle."
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("returned/"))
            self.assertEqual([source.source_kind for source in sources], ["file", "file"])
            self.assertEqual(
                [source.directory for source in sources], [first.resolve(), second.resolve()]
            )
            self.assertTrue(all(source.selection is None for source in sources))

            plan = plan_archive(config, BuildRequest.create("returned/"))
            self.assertEqual(set(plan.entries), {"repo-a.zip", "repo-b.zip"})
            self.assertEqual(plan.entries["repo-a.zip"], first.resolve())
            self.assertIn(
                "## `repo-a.zip`\n\nFiles: 1\n\nRepositories returned from the previous editing cycle.",
                plan.readme,
            )
            self.assertNotIn("## `repo-a.zip/`", plan.readme)

    def test_file_target_scope_namespace_places_files_under_existing_namespace(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            archive_file = returned / "repo.zip"
            archive_file.write_bytes(b"zip")
            config = self._config(
                root,
                """
                [namespace.returned]

                [scope.returned]
                path = "returned"
                target_kind = "file"
                namespace = "returned"
                description = "Returned repositories."
            """,
            )

            plan = plan_archive(config, BuildRequest.create("returned/repo.zip"))
            self.assertEqual(set(plan.entries), {"returned/repo.zip"})
            self.assertIn("## `returned/repo.zip`", plan.readme)
            self.assertNotIn("Namespace:", plan.readme)
            self.assertNotIn("Source root:", plan.readme)

    def test_file_target_scope_ignore_applies_to_file_names_and_directories_are_not_targets(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "keep.zip").write_bytes(b"keep")
            (returned / "skip.zip").write_bytes(b"skip")
            (returned / "directory.zip").mkdir()
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
                ignore = ["skip.zip"]
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("returned/"))
            self.assertEqual([source.source_root for source in sources], ["keep.zip"])
            with self.assertRaisesRegex(SelectionError, "ignored by"):
                resolve_sources(config, BuildRequest.create("returned/skip.zip"))
            with self.assertRaisesRegex(SelectionError, "not a regular file"):
                resolve_sources(config, BuildRequest.create("returned/directory.zip"))

    def test_file_target_scope_expansion_requires_eligible_files(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "only-directory").mkdir()
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )
            with self.assertRaisesRegex(SelectionError, "no eligible direct child files"):
                resolve_sources(config, BuildRequest.create("returned/"))

    def test_directory_scope_description_precedes_pluck_description(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "project"
            project.mkdir()
            (project / "file.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                description = "Files selected from the project directory."
                must = ["file.txt"]

                [scope]
                description = "Project supplied for review."
            """,
            )
            plan = plan_archive(config, BuildRequest.create("./project/"))
            self.assertIn(
                "## `project/`\n\nFiles: 1\n\n"
                + "Project supplied for review.\n\n"
                + "Files selected from the project directory.",
                plan.readme,
            )

    def test_file_target_does_not_use_pluck_description(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "repo.zip").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                description = "Directory-only selection description."
                must = ["src/"]

                [scope.returned]
                path = "returned"
                target_kind = "file"
                description = "Returned repository archive."
            """,
            )
            plan = plan_archive(config, BuildRequest.create("returned/repo.zip"))
            self.assertIn("Returned repository archive.", plan.readme)
            self.assertNotIn("Directory-only selection description.", plan.readme)

    def test_file_target_archive_path_cannot_be_parent_of_directory_source_entries(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "project"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            returned = root / "returned"
            returned.mkdir()
            (returned / "bundle").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [namespace.bundle]

                [pluck]
                must = ["src/"]

                [scope]
                namespace = "bundle"

                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            for targets in (("./project/", "returned/bundle"), ("returned/bundle", "./project/")):
                with self.subTest(targets=targets):
                    with self.assertRaisesRegex(
                        SelectionError, "archive file/directory path conflict"
                    ):
                        plan_archive(config, BuildRequest.create(*targets))

    def test_mixed_directory_and_file_scopes_use_pluck_only_for_directory_target(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "project"
            project.mkdir()
            (project / "src").mkdir()
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            returned = root / "returned"
            returned.mkdir()
            (returned / "repo.zip").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                description = "Directory contents."
                must = ["src/"]

                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )
            plan = plan_archive(config, BuildRequest.create("./project/", "returned/repo.zip"))
            self.assertEqual(set(plan.entries), {"project/src/main.py", "repo.zip"})

    def test_file_target_list_selector_selects_named_scope_files_in_declared_order(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            for name in ("repo-a.zip", "repo-b.zip", "repo-c.zip"):
                (returned / name).write_bytes(name.encode())
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            sources = resolve_sources(
                config,
                BuildRequest.create("returned:[repo-c.zip/repo-a.zip]"),
            )
            self.assertEqual(
                [source.source_root for source in sources],
                ["repo-c.zip", "repo-a.zip"],
            )

    def test_file_target_list_selector_uses_only_outer_brackets_as_syntax(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "[foo").write_bytes(b"a")
            (returned / "b]ar").write_bytes(b"b")
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("returned:[[foo/b]ar]"))
            self.assertEqual([source.source_root for source in sources], ["[foo", "b]ar"])

    def test_file_target_list_selector_supports_default_scope(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "a.zip").write_bytes(b"a")
            (root / "b.zip").write_bytes(b"b")
            config = self._config(
                root,
                """
                [scope]
                target_kind = "file"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create(":[b.zip/a.zip]"))
            self.assertEqual([source.source_root for source in sources], ["b.zip", "a.zip"])

    def test_file_target_regex_selector_uses_fullmatch_and_sorted_scope_candidates(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            for name in ("repo-10.zip", "repo-2.zip", "repo-a.zip", "notes.txt"):
                (returned / name).write_bytes(name.encode())
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            sources = resolve_sources(
                config,
                BuildRequest.create(r"returned:<repo-[0-9]+\.zip>"),
            )
            self.assertEqual(
                [source.source_root for source in sources],
                ["repo-10.zip", "repo-2.zip"],
            )
            with self.assertRaisesRegex(SelectionError, "matched no eligible file Targets"):
                resolve_sources(config, BuildRequest.create("returned:<zip>"))

    def test_file_target_regex_selector_supports_default_scope(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "repo-1.zip").write_bytes(b"1")
            (root / "repo-a.zip").write_bytes(b"a")
            config = self._config(
                root,
                """
                [scope]
                target_kind = "file"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create(r":<repo-[0-9]+\.zip>"))
            self.assertEqual([source.source_root for source in sources], ["repo-1.zip"])

    def test_file_target_regex_selector_applies_scope_ignore_before_matching(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "keep.zip").write_bytes(b"keep")
            (returned / "skip.zip").write_bytes(b"skip")
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
                ignore = ["skip.zip"]
            """,
            )

            sources = resolve_sources(config, BuildRequest.create(r"returned:<.*\.zip>"))
            self.assertEqual([source.source_root for source in sources], ["keep.zip"])

    def test_directory_target_selectors_select_directories_and_apply_pluck(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            work = root / "work"
            for name in ("project-a", "project-b"):
                project = work / name
                (project / "src").mkdir(parents=True)
                (project / "src" / "main.py").write_text(name, encoding="utf-8")
            (work / "project-a.zip").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.work]
                path = "work"
            """,
            )

            listed = resolve_sources(config, BuildRequest.create("work:[project-b//project-a/]"))
            self.assertEqual([source.source_root for source in listed], ["project-b", "project-a"])
            self.assertTrue(all(source.source_kind == "directory" for source in listed))

            matched = resolve_sources(config, BuildRequest.create(r"work:<project-[ab]/>"))
            self.assertEqual([source.source_root for source in matched], ["project-a", "project-b"])
            self.assertTrue(all(source.selection is not None for source in matched))

    def test_both_target_scope_expands_files_and_directories_and_applies_pluck_only_to_directories(
        self,
    ):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            project = mixed / "repo-a"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("a", encoding="utf-8")
            archive = mixed / "repo-b.zip"
            archive.write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                description = "Directory contents."
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("mixed/"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in sources],
                [("repo-a", "directory"), ("repo-b.zip", "file")],
            )
            self.assertIsNotNone(sources[0].selection)
            self.assertIsNone(sources[1].selection)

            plan = plan_archive(config, BuildRequest.create("mixed/"))
            self.assertEqual(set(plan.entries), {"repo-a/src/main.py", "repo-b.zip"})

    def test_both_target_scope_selectors_match_files_and_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            for name in ("repo-a", "other"):
                project = mixed / name
                (project / "src").mkdir(parents=True)
                (project / "src" / "main.py").write_text(name, encoding="utf-8")
            (mixed / "repo-b.zip").write_bytes(b"zip")
            (mixed / "notes.txt").write_text("notes", encoding="utf-8")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            listed = resolve_sources(config, BuildRequest.create("mixed:[repo-b.zip/repo-a/]"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in listed],
                [("repo-b.zip", "file"), ("repo-a", "directory")],
            )

            matched = resolve_sources(config, BuildRequest.create(r"mixed:<repo-.*/?>"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in matched],
                [("repo-a", "directory"), ("repo-b.zip", "file")],
            )

    def test_both_target_scope_without_pluck_allows_files_but_rejects_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            mixed.mkdir()
            (mixed / "repo.zip").write_bytes(b"zip")
            project = mixed / "project"
            project.mkdir()
            (project / "file.txt").write_text("x", encoding="utf-8")
            config = self._config(
                root,
                """
                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("mixed/repo.zip"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in sources],
                [("repo.zip", "file")],
            )
            with self.assertRaisesRegex(SelectionError, "does not define Pluck"):
                resolve_sources(config, BuildRequest.create("mixed/project/"))
            with self.assertRaisesRegex(SelectionError, "does not define Pluck"):
                resolve_sources(config, BuildRequest.create("mixed/"))

    def test_both_target_scope_case_applies_only_to_directory_targets(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            project = mixed / "project"
            project.mkdir(parents=True)
            (project / "default.txt").write_text("default", encoding="utf-8")
            (project / "review.txt").write_text("review", encoding="utf-8")
            (mixed / "repo.zip").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                must = ["default.txt"]

                [pluck.case.review]
                must = ["review.txt"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
            )

            plan = plan_archive(config, BuildRequest.create("mixed/", case="review"))
            self.assertEqual(set(plan.entries), {"project/review.txt", "repo.zip"})

    def test_both_target_scope_ignore_filters_files_and_directories_before_selectors(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            mixed = root / "mixed"
            for name in ("keep-dir", "skip-dir"):
                project = mixed / name
                (project / "src").mkdir(parents=True)
                (project / "src" / "main.py").write_text(name, encoding="utf-8")
            (mixed / "keep.zip").write_bytes(b"keep")
            (mixed / "skip.zip").write_bytes(b"skip")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope.mixed]
                path = "mixed"
                target_kind = "both"
                ignore = ["skip*"]
            """,
            )

            expanded = resolve_sources(config, BuildRequest.create("mixed/"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in expanded],
                [("keep-dir", "directory"), ("keep.zip", "file")],
            )
            matched = resolve_sources(config, BuildRequest.create(r"mixed:<.*/?>"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in matched],
                [("keep-dir", "directory"), ("keep.zip", "file")],
            )
            with self.assertRaisesRegex(SelectionError, "ignored by"):
                resolve_sources(config, BuildRequest.create("mixed:[skip-dir/]"))

    def test_default_scope_both_selector_can_mix_directory_and_file_targets(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "repo-dir"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            (root / "repo-file.zip").write_bytes(b"zip")
            config = self._config(
                root,
                """
                [pluck]
                must = ["src/"]

                [scope]
                target_kind = "both"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create(r":<repo-.*/?>"))
            self.assertEqual(
                [(source.source_root, source.source_kind) for source in sources],
                [("repo-dir", "directory"), ("repo-file.zip", "file")],
            )

    def test_file_target_list_selector_rejects_malformed_or_missing_items(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "a.zip").write_bytes(b"a")
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            cases = (
                ("returned:[a.zip", "must end with"),
                ("returned:[]", "must not be empty"),
                ("returned:[a.zip///b.zip]", "three or more"),
                ("returned:[missing.zip]", "does not exist"),
            )
            for reference, message in cases:
                with (
                    self.subTest(reference=reference),
                    self.assertRaisesRegex(SelectionError, message),
                ):
                    resolve_sources(config, BuildRequest.create(reference))

    def test_file_target_regex_selector_validates_pattern_boundary_and_syntax(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "a.zip").write_bytes(b"a")
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            cases = (
                (r"returned:<.*\.zip", "must end with"),
                ("returned:<>", "must not be empty"),
                ("returned:<foo/bar>", "matched no eligible"),
                ("returned:<(>", "invalid regular-expression selector"),
                ("returned:<" + "a" * 513 + ">", "512-character limit"),
            )
            for reference, message in cases:
                with (
                    self.subTest(reference=reference),
                    self.assertRaisesRegex(SelectionError, message),
                ):
                    resolve_sources(config, BuildRequest.create(reference))

    def test_file_target_selectors_deduplicate_overlapping_selector_results(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            (returned / "a.zip").write_bytes(b"a")
            (returned / "b.zip").write_bytes(b"b")
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            sources = resolve_sources(
                config,
                BuildRequest.create(
                    "returned/a.zip",
                    "returned:[a.zip/b.zip]",
                    r"returned:<.*\.zip>",
                ),
            )
            self.assertEqual([source.source_root for source in sources], ["a.zip", "b.zip"])

    def test_file_target_selector_with_unknown_named_scope_is_not_treated_as_a_literal_default_target(
        self,
    ):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            literal = root / "missing:[a.zip]"
            literal.write_bytes(b"x")
            config = self._config(
                root,
                """
                [scope]
                target_kind = "file"
            """,
            )

            with self.assertRaisesRegex(SelectionError, "Scope 'missing' is not defined"):
                resolve_sources(config, BuildRequest.create("missing:[a.zip]"))

    def test_selector_marker_inside_named_literal_target_name_remains_literal(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            returned = root / "returned"
            returned.mkdir()
            literal = returned / "repo:[x].zip"
            literal.write_bytes(b"x")
            config = self._config(
                root,
                """
                [scope.returned]
                path = "returned"
                target_kind = "file"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("returned/repo:[x].zip"))
            self.assertEqual([source.directory for source in sources], [literal.resolve()])

    def test_selector_shaped_literal_file_name_can_be_selected_through_list_selector(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            literal = root / "returned:[x]"
            literal.write_bytes(b"x")
            config = self._config(
                root,
                """
                [scope]
                target_kind = "file"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create(":[returned:[x]]"))
            self.assertEqual([source.directory for source in sources], [literal.resolve()])

    def test_non_selector_colon_remains_a_literal_default_file_target_name(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            literal = root / "foo:bar"
            literal.write_bytes(b"x")
            config = self._config(
                root,
                """
                [scope]
                target_kind = "file"
            """,
            )

            sources = resolve_sources(config, BuildRequest.create("foo:bar"))
            self.assertEqual([source.directory for source in sources], [literal.resolve()])


if __name__ == "__main__":
    unittest.main()
