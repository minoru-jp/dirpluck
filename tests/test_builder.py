from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from dirpluck.builder import BuildRequest, build_archive, plan_archive, render_archive_tree, resolve_sources
from dirpluck.config import load_config
from dirpluck.errors import SelectionError


CONFIG = '''
[target]
description = "The project currently being worked on."
include = ["src", "README.md"]
exclude = ["generated/", "__pycache__/", ".DS_Store", "*.pyc"]

[companion.framework]
path = "framework"
description = "A fixed framework needed with the target."
include = ["src", "README.md"]
exclude = ["generated/", "__pycache__/", ".DS_Store", "*.pyc"]
'''


class BuilderTests(unittest.TestCase):
    def _config(self, root: Path, text: str = CONFIG, *, output: str = "out.zip", if_exists: str = "error"):
        body = textwrap.dedent(text)
        if "[output]" not in body:
            body += f'\n[output]\npath = {output!r}\nif_exists = {if_exists!r}\n'
        manifest = root / "dirpluck.toml"
        manifest.write_text(body, encoding="utf-8")
        return load_config(manifest)

    def _project(self, root: Path, relative: str, marker: str) -> Path:
        project = root / relative
        (project / "src" / "generated").mkdir(parents=True)
        (project / "src" / "nested" / "__pycache__").mkdir(parents=True)
        (project / "src" / "module.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")
        (project / "src" / "nested" / "helper.py").write_text("HELPER = 1\n", encoding="utf-8")
        (project / "src" / "nested" / "cache.pyc").write_bytes(b"cache")
        (project / "src" / "nested" / "__pycache__" / "hidden.py").write_text("HIDDEN = 1\n", encoding="utf-8")
        (project / "src" / "generated" / "skip.py").write_text("SKIP = 1\n", encoding="utf-8")
        (project / "src" / ".DS_Store").write_text("metadata\n", encoding="utf-8")
        (project / "README.md").write_text(f"# {marker}\n", encoding="utf-8")
        (project / "notes.txt").write_text("not selected\n", encoding="utf-8")
        return project

    def test_target_and_companion_preserve_cwd_relative_filesystem_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._project(root, "a/common", "a")
            self._project(root, "b/common", "b")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
                [companion.other]
                path = "b/common"
                description = "Companion."
                include = ["src"]
            ''')
            output = build_archive(config, BuildRequest.create("a/common"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("a/common/src/module.py", names)
            self.assertIn("b/common/src/module.py", names)

    def test_multiple_runtime_targets_use_the_same_target_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._project(root, "project-a", "a")
            self._project(root, "project-b", "b")
            config = self._config(root, '''
                [target]
                description = "Projects selected for review."
                include = ["src"]
            ''')
            output = build_archive(
                config,
                BuildRequest.create("project-a", "project-b"),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("project-a/src/module.py", names)
            self.assertIn("project-b/src/module.py", names)
            self.assertIn("Directory source: CLI input #1", readme)
            self.assertIn("Directory source: CLI input #2", readme)

    def test_multiple_runtime_targets_use_the_same_named_case(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("project-a", "project-b"):
                project = root / name
                (project / "src").mkdir(parents=True)
                (project / "tests").mkdir()
                (project / "src" / "main.py").write_text("src", encoding="utf-8")
                (project / "tests" / "test_main.py").write_text("test", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Default projects."
                include = ["src"]

                [target.case.review]
                description = "Projects prepared for review."
                include = ["tests"]
            ''')
            output = build_archive(
                config,
                BuildRequest.create("project-a", "project-b", case="review"),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("project-a/tests/test_main.py", names)
            self.assertIn("project-b/tests/test_main.py", names)
            self.assertNotIn("project-a/src/main.py", names)
            self.assertNotIn("project-b/src/main.py", names)

    def test_duplicate_runtime_targets_are_rejected_after_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._project(root, "project", "a")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                resolve_sources(
                    config,
                    BuildRequest.create("project", "./project"),
                    cwd=root,
                )

    def test_target_may_be_current_working_directory_and_keeps_basename(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Target cwd."
                include = ["src"]
            ''')
            output = build_archive(config, BuildRequest.create("."), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertIn(f"{root.name}/src/main.py", archive.namelist())

    def test_include_star_matches_files_and_directories_at_fixed_depth(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "dist").mkdir(parents=True)
            (project / "dist" / "package-1.whl").write_bytes(b"one")
            (project / "dist" / "package-2.whl").write_bytes(b"two")
            (project / "dist" / "package-2.tar.gz").write_bytes(b"sdist")
            for name in ("alpha", "beta"):
                pkg = project / "packages" / name / "dist"
                pkg.mkdir(parents=True)
                (pkg / f"pkg-{name}.whl").write_bytes(name.encode())
            (project / "plugins" / "foo-middle-bar").mkdir(parents=True)
            (project / "plugins" / "foo-middle-bar" / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Patterns."
                include = [
                    "dist/package-*.whl",
                    "packages/*/dist/pkg-*.whl",
                    "plugins/foo*bar",
                ]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertEqual(names, {
                "README.md",
                "application/dist/package-1.whl",
                "application/dist/package-2.whl",
                "application/packages/alpha/dist/pkg-alpha.whl",
                "application/packages/beta/dist/pkg-beta.whl",
                "application/plugins/foo-middle-bar/main.py",
            })

    def test_literal_include_is_case_sensitive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application"
            project.mkdir()
            (project / "readme.md").write_text("lowercase", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Literal case-sensitive."
                include = ["README.md"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)

    def test_include_star_is_case_sensitive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dist = root / "application" / "dist"
            dist.mkdir(parents=True)
            (dist / "pkg-one.whl").write_bytes(b"one")
            (dist / "PKG-two.whl").write_bytes(b"two")
            config = self._config(root, '''
                [target]
                description = "Case-sensitive."
                include = ["dist/pkg-*.whl"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ["README.md", "application/dist/pkg-one.whl"])

    def test_nested_file_include_preserves_intermediate_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dist = root / "shikumi" / "dist"
            dist.mkdir(parents=True)
            (dist / "shikumi-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
            config = self._config(root, '''
                [target]
                description = "Wheel."
                include = ["dist/shikumi-0.1.0-py3-none-any.whl"]
            ''')
            output = build_archive(config, BuildRequest.create("shikumi"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ["README.md", "shikumi/dist/shikumi-0.1.0-py3-none-any.whl"])

    def test_include_if_exists_adds_existing_and_ignores_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            (project / "tests").mkdir()
            (project / "tests" / "test_main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Optional extras."
                include = ["src"]
                include_if_exists = ["tests", "docs", "CHANGELOG.md"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/main.py", names)
            self.assertIn("application/tests/test_main.py", names)
            self.assertNotIn("application/docs", names)

    def test_optional_only_defaults_to_error_when_target_is_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [target]
                description = "Optional."
                include_if_exists = ["src", "README.md"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)

    def test_if_empty_allow_preserves_empty_target_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [target]
                description = "Greenfield target."
                include_if_exists = ["src", "README.md"]
                if_empty = "allow"
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"README.md", "application/"})
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Selected files: 0", readme)
            self.assertIn("Empty result policy: `allow`", readme)

    def test_dry_run_reports_allowed_empty_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [target]
                description = "Greenfield target."
                include_if_exists = ["src"]
                if_empty = "allow"
            ''')
            plan = plan_archive(config, BuildRequest.create("application"), cwd=root, allow_missing=True)
            self.assertIn("target (`application/`): empty, allowed", render_archive_tree(plan))

    def test_dry_run_distinguishes_required_and_optional_missing_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [target]
                description = "Dry run."
                include = ["src"]
                include_if_exists = ["tests"]
            ''')
            plan = plan_archive(config, BuildRequest.create("application"), cwd=root, allow_missing=True)
            tree = render_archive_tree(plan)
            self.assertIn("src [missing]", tree)
            self.assertIn("tests [optional missing]", tree)
            self.assertIn("empty, would error", tree)

    def test_directory_include_is_recursive_and_name_excludes_apply(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._project(root, "application", "app")
            config = self._config(root, '''
                [target]
                description = "Recursive directory."
                include = ["src"]
                exclude = ["generated/", "__pycache__/", ".DS_Store", "*.pyc"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/module.py", names)
            self.assertIn("application/src/nested/helper.py", names)
            self.assertNotIn("application/src/generated/skip.py", names)
            self.assertNotIn("application/src/nested/cache.pyc", names)

    def test_exclude_supports_exact_prefix_suffix_and_contains(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            for name in ("keep.py", "exact.tmp", "prefix-one.py", "two-suffix.py", "has-draft-copy.py"):
                (project / name).write_text("x", encoding="utf-8")
            for dirname in ("cache", "temp-build", "old-generated", "has-junk-dir"):
                directory = project / dirname
                directory.mkdir()
                (directory / "inside.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Filters."
                include = ["src"]
                exclude = ["exact.tmp", "prefix-*", "*-suffix.py", "*draft*", "cache/", "temp*/", "*generated/", "*junk*/"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/keep.py", names)
            self.assertEqual([name for name in names if name.endswith("inside.py")], [])

    def test_target_case_selects_only_named_case_without_inheritance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "src").mkdir(parents=True)
            (project / "tests").mkdir()
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            (project / "tests" / "test_main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Default source."
                include = ["src"]
                [target.case.review]
                description = "Review tests only."
                include = ["tests"]
            ''')
            output = build_archive(config, BuildRequest.create("application", case="review"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("application/tests/test_main.py", names)
            self.assertNotIn("application/src/main.py", names)
            self.assertIn("Case: `review`", readme)
            self.assertIn("[target.case.review]", readme)

    def test_default_case_uses_target_table(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Default source."
                include = ["src"]
                [target.case.review]
                description = "Review."
                include = ["tests"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("Case: `default`", readme)
            self.assertIn("[target]", readme)

    def test_missing_default_requires_explicit_case(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(root, '''
                [target.case.review]
                description = "Review."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)

    def test_unknown_case_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [target.case.review]
                description = "Review."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application", case="release"), cwd=root)


    def test_companion_case_overrides_selection_and_other_companion_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
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
            config = self._config(root, '''
                [target]
                description = "Default target."
                include = ["src"]

                [target.case.review]
                description = "Review target."
                include = ["tests"]

                [companion.framework]
                path = "framework"
                description = "Default framework."
                include = ["src"]

                [companion.framework.case.review]
                description = "Framework review material."
                include = ["tests"]

                [companion.guidelines]
                path = "guidelines"
                description = "Guidelines always included."
                include = ["README.md"]
            ''')
            output = build_archive(
                config, BuildRequest.create("application", case="review"), cwd=root
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("application/tests/test_app.py", names)
            self.assertIn("framework/tests/test_core.py", names)
            self.assertNotIn("framework/src/core.py", names)
            self.assertIn("guidelines/README.md", names)
            self.assertIn("[companion.framework.case.review]", readme)
            self.assertIn("[companion.guidelines]", readme)

    def test_companion_only_configuration_builds_without_target_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "contracts").mkdir()
            (root / "notes").mkdir()
            (root / "contracts" / "a.pdf").write_bytes(b"pdf")
            (root / "notes" / "meeting.md").write_text("notes", encoding="utf-8")
            config = self._config(root, '''
                [companion.contracts]
                path = "contracts"
                description = "Contracts."
                include = ["*.pdf"]

                [companion.notes]
                path = "notes"
                description = "Notes."
                include = ["*.md"]
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertEqual(
                names,
                {"README.md", "contracts/a.pdf", "notes/meeting.md"},
            )

    def test_companion_only_case_uses_override_and_base_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "documents" / "current").mkdir(parents=True)
            (root / "documents" / "history").mkdir()
            (root / "documents" / "current" / "now.md").write_text("now", encoding="utf-8")
            (root / "documents" / "history" / "old.md").write_text("old", encoding="utf-8")
            (root / "assets").mkdir()
            (root / "assets" / "figure.png").write_bytes(b"png")
            config = self._config(root, '''
                [companion.documents]
                path = "documents"
                description = "Current documents."
                include = ["current"]

                [companion.documents.case.archive]
                description = "Archive documents."
                include = ["current", "history"]

                [companion.assets]
                path = "assets"
                description = "Assets."
                include = ["*.png"]
            ''')
            output = build_archive(config, BuildRequest.create(case="archive"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("documents/current/now.md", names)
            self.assertIn("documents/history/old.md", names)
            self.assertIn("assets/figure.png", names)
            self.assertIn("Case: `archive`", readme)
            self.assertIn("[companion.documents.case.archive]", readme)
            self.assertIn("[companion.assets]", readme)

    def test_target_presence_and_directory_argument_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            target_config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''')
            with self.assertRaisesRegex(SelectionError, "DIRECTORY is required"):
                resolve_sources(target_config, BuildRequest.create(), cwd=root)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            (root / "documents" / "a.txt").write_text("a", encoding="utf-8")
            companion_config = self._config(root, '''
                [companion.documents]
                path = "documents"
                description = "Documents."
                include = ["*.txt"]
            ''')
            with self.assertRaisesRegex(SelectionError, "must not be specified"):
                resolve_sources(companion_config, BuildRequest.create("documents"), cwd=root)

    def test_companion_only_unknown_case_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "documents").mkdir()
            config = self._config(root, '''
                [companion.documents]
                path = "documents"
                description = "Documents."
                include_if_exists = ["*.md"]
                if_empty = "allow"

                [companion.documents.case.archive]
                description = "Archive documents."
                include_if_exists = ["*.md"]
                if_empty = "allow"
            ''')
            with self.assertRaisesRegex(SelectionError, "case 'review' is not defined"):
                resolve_sources(config, BuildRequest.create(case="review"), cwd=root)

    def test_resolve_sources_contains_target_then_all_companions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("application", "one", "two"):
                (root / name / "src").mkdir(parents=True)
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
                [companion.one]
                path = "one"
                description = "One."
                include = ["src"]
                [companion.two]
                path = "two"
                description = "Two."
                include = ["src"]
            ''')
            sources = resolve_sources(config, BuildRequest.create("application"), cwd=root)
            self.assertEqual([source.key for source in sources], ["target", "companion:one", "companion:two"])

    def test_archive_readme_groups_target_and_companion_for_same_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "shikumi-devdoc"
            (project / "src").mkdir(parents=True)
            (project / "dist").mkdir()
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            (project / "dist" / "shikumi_devdoc-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
            config = self._config(root, '''
                [target]
                description = "The project currently being changed."
                include = ["src"]
                [companion.devdoc]
                path = "shikumi-devdoc"
                description = "The current built distribution used as a reference."
                include = ["dist/shikumi_devdoc-*.whl"]
            ''')
            output = build_archive(config, BuildRequest.create("shikumi-devdoc"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("shikumi-devdoc/src/main.py", names)
            self.assertIn("shikumi-devdoc/dist/shikumi_devdoc-0.1.0-py3-none-any.whl", names)
            self.assertEqual(readme.count("### `shikumi-devdoc/`"), 1)
            self.assertIn("#### Target", readme)
            self.assertIn("#### Companion `devdoc`", readme)
            self.assertNotIn("multiple declared purposes", readme)
            self.assertNotIn("dirpluck", readme.lower())
            self.assertNotIn("llm", readme.lower())

    def test_target_outside_cwd_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            outside = Path(other) / "outside"
            (outside / "src").mkdir(parents=True)
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create(outside), cwd=root)

    def test_companion_outside_cwd_through_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            outside = Path(other) / "framework"
            (outside / "src").mkdir(parents=True)
            link = root / "framework"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
                [companion.framework]
                path = "framework"
                description = "Framework."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                resolve_sources(config, BuildRequest.create("application"), cwd=root)

    def test_recursive_directory_include_rejects_external_directory_symlink(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            project = self._project(root, "application", "app")
            outside = Path(other) / "outside-dir"
            outside.mkdir()
            (outside / "secret.py").write_text("SECRET = 1\n", encoding="utf-8")
            link = project / "src" / "external-dir"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)

    def test_recursive_directory_include_ignores_internal_directory_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real = root / "application" / "src" / "real"
            real.mkdir(parents=True)
            (real / "inside.py").write_text("VALUE = 1\n", encoding="utf-8")
            link = root / "application" / "src" / "internal-link"
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/real/inside.py", names)
            self.assertNotIn("application/src/internal-link/inside.py", names)

    def test_file_symlink_cannot_escape_target_directory(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            project = root / "application"
            (project / "src").mkdir(parents=True)
            external = Path(other) / "external.py"
            external.write_text("SECRET = 1\n", encoding="utf-8")
            link = project / "src" / "external.py"
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)

    def test_output_parent_directories_are_created(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''', output="artifacts/context.zip")
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            self.assertEqual(output, root / "artifacts" / "context.zip")
            self.assertTrue(output.is_file())

    def test_output_error_policy_rejects_existing_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "out.zip").write_bytes(b"old")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''', if_exists="error")
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)
            self.assertEqual((root / "out.zip").read_bytes(), b"old")

    def test_output_overwrite_policy_replaces_existing_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            (root / "out.zip").write_bytes(b"old")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''', if_exists="overwrite")
            build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(root / "out.zip") as archive:
                self.assertIn("application/src/main.py", archive.namelist())

    def test_generated_output_uses_timestamp_prefix_suffix_and_sequence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, """
                [target]
                description = "Target."
                include = ["src"]
                [output]
                directory = "snapshots"
                prefix = "project"
                timestamp = true
                suffix = "review"
            """)
            with patch("dirpluck.builder._current_output_timestamp", return_value="20260916-011623"):
                output = build_archive(
                    config,
                    BuildRequest.create("application", sequence=3),
                    cwd=root,
                )
            self.assertEqual(
                output,
                root / "snapshots" / "project-20260916-011623-3-review.zip",
            )
            self.assertTrue(output.is_file())

    def test_generated_output_without_sequence_omits_sequence_segment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            config = self._config(root, """
                [target]
                description = "Target."
                include = ["src"]
                [output]
                directory = "."
                timestamp = true
            """)
            with patch("dirpluck.builder._current_output_timestamp", return_value="20260916-011623"):
                output = build_archive(config, BuildRequest.create("application"), cwd=root)
            self.assertEqual(output, root / "20260916-011623.zip")

    def test_generated_output_rejects_existing_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            (root / "snapshots").mkdir()
            existing = root / "snapshots" / "snapshot-20260916-011623-2.zip"
            existing.write_bytes(b"old")
            config = self._config(root, """
                [target]
                description = "Target."
                include = ["src"]
                [output]
                directory = "snapshots"
                prefix = "snapshot"
                timestamp = true
            """)
            with patch("dirpluck.builder._current_output_timestamp", return_value="20260916-011623"):
                with self.assertRaises(SelectionError):
                    build_archive(
                        config,
                        BuildRequest.create("application", sequence=2),
                        cwd=root,
                    )
            self.assertEqual(existing.read_bytes(), b"old")

    def test_sequence_is_rejected_for_fixed_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(root, """
                [target]
                description = "Target."
                include = ["src"]
            """)
            with self.assertRaises(SelectionError):
                build_archive(
                    config,
                    BuildRequest.create("application", sequence=1),
                    cwd=root,
                )

    def test_sequence_must_be_positive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            config = self._config(root, """
                [target]
                description = "Target."
                include = ["src"]
                [output]
                directory = "snapshots"
                timestamp = true
            """)
            with self.assertRaises(SelectionError):
                plan_archive(
                    config,
                    BuildRequest.create("application", sequence=0),
                    cwd=root,
                )

    def test_output_path_cannot_escape_cwd_through_parent_symlink(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            link = root / "artifacts"
            try:
                link.symlink_to(Path(other), target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
            ''', output="artifacts/out.zip")
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("application"), cwd=root)


if __name__ == "__main__":
    unittest.main()
