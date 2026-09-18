from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from dirpluck.builder import (
    BuildRequest,
    _load_imported_config,
    build_archive,
    plan_archive,
    render_archive_tree,
    resolve_sources,
)
from dirpluck.config import ConfigurationImport, load_config
from dirpluck.errors import ConfigurationError, SelectionError


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


    def test_all_case_can_reuse_shared_exclude_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "src" / "__pycache__").mkdir(parents=True)
            (project / ".git").mkdir()
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            (project / "src" / "__pycache__" / "main.pyc").write_bytes(b"cache")
            (project / ".git" / "config").write_text("git", encoding="utf-8")
            (project / "notes.txt").write_text("notes", encoding="utf-8")

            config = self._config(root, '''
                [shared.exclude_patterns]
                python-dev = [".git/", "__pycache__/", "*.pyc"]

                [target]
                description = "Default selection."
                include = ["src"]
                exclude_pattern_refs = ["python-dev"]

                [target.case.all]
                description = "Everything except shared development artifacts."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["python-dev"]
                if_empty = "allow"
            ''')

            output = build_archive(
                config,
                BuildRequest.create("application", case="all"),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())

            self.assertIn("application/src/main.py", names)
            self.assertIn("application/notes.txt", names)
            self.assertNotIn("application/.git/config", names)
            self.assertNotIn("application/src/__pycache__/main.pyc", names)

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


    def test_import_uses_only_external_companions_with_independent_case(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "dirpluck"
            root.mkdir()
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "main.py").write_text("root", encoding="utf-8")
            (root / "tests" / "test_main.py").write_text("review", encoding="utf-8")

            shikumi = workspace / "shikumi"
            (shikumi / "dist").mkdir(parents=True)
            (shikumi / "dist" / "shikumi-0.3.0.whl").write_bytes(b"shikumi")
            (shikumi / "base.txt").write_text("base", encoding="utf-8")
            (shikumi / "dirpluck.toml").write_text(textwrap.dedent('''
                [target]
                description = "Base shikumi source."
                include = ["base.txt"]

                [target.case.distribution]
                description = "Built shikumi distribution."
                include = ["dist/shikumi-*.whl"]

                [companion.devdoc]
                path = "shikumi-devdoc"
                description = "Base devdoc distribution."
                include = ["dist/base-*.whl"]

                [companion.devdoc.case.distribution]
                description = "Built devdoc distribution."
                include = ["dist/shikumi_devdoc-*.whl"]

                [output]
                path = "imported-output.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            (workspace / "imported-output.zip").write_bytes(b"existing imported output")

            devdoc = workspace / "shikumi-devdoc" / "dist"
            devdoc.mkdir(parents=True)
            (devdoc / "base-0.1.0.whl").write_bytes(b"base")
            (devdoc / "shikumi_devdoc-0.1.0.whl").write_bytes(b"devdoc")

            config = self._config(root, '''
                [target]
                description = "Root project."
                include = ["src"]

                [target.case.review]
                description = "Root review selection."
                include = ["tests"]

                [import.shikumi-stack]
                root = ".."
                configuration = "shikumi/dirpluck.toml"
                case = "distribution"
            ''')
            output = build_archive(
                config,
                BuildRequest.create(".", case="review"),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")

            self.assertIn(f"{root.name}/tests/test_main.py", names)
            self.assertNotIn(f"{root.name}/src/main.py", names)
            self.assertNotIn("shikumi/dist/shikumi-0.3.0.whl", names)
            self.assertNotIn("shikumi/base.txt", names)
            self.assertIn("shikumi-devdoc/dist/shikumi_devdoc-0.1.0.whl", names)
            self.assertNotIn("shikumi-devdoc/dist/base-0.1.0.whl", names)
            self.assertEqual(
                (workspace / "imported-output.zip").read_bytes(),
                b"existing imported output",
            )
            self.assertIn("## Configuration imports", readme)
            self.assertIn("### `shikumi-stack`", readme)
            self.assertIn("- Execution root: `..`", readme)
            self.assertIn("- Case: `distribution`", readme)
            self.assertNotIn("- Targets:", readme)

    def test_root_configuration_may_build_from_imports_only(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            (external / "data").mkdir()
            (external / "data" / "artifact.txt").write_text("x", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Imported data."
                include = ["artifact.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("data/artifact.txt", archive.namelist())

    def test_import_root_is_relative_to_root_configuration_file_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            cwd = workspace / "project"
            config_dir = cwd / "dirpluck"
            config_dir.mkdir(parents=True)
            external = workspace / "external"
            (external / "data").mkdir(parents=True)
            (external / "data" / "artifact.txt").write_text("x", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Imported data."
                include = ["artifact.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            manifest = config_dir / "context.toml"
            manifest.write_text(textwrap.dedent('''
                [import.external]
                root = "../../external"
                configuration = "config.toml"

                [output]
                path = "out.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = load_config(manifest)

            output = build_archive(config, BuildRequest.create(), cwd=cwd)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("data/artifact.txt", archive.namelist())

    def test_import_requires_companion_and_ignores_imported_target(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            (external / "target.txt").write_text("target", encoding="utf-8")
            (external / "target-only.toml").write_text(textwrap.dedent('''
                [target]
                description = "Imported target."
                include = ["target.txt"]
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "target-only.toml"
            ''')
            with self.assertRaises(ConfigurationError):
                plan_archive(config, BuildRequest.create(), cwd=root)

            (external / "data").mkdir()
            (external / "data" / "artifact.txt").write_text("companion", encoding="utf-8")
            (external / "with-companion.toml").write_text(textwrap.dedent('''
                [target]
                description = "Ignored imported target."
                include = ["target.txt"]

                [companion.data]
                path = "data"
                description = "Imported companion."
                include = ["artifact.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "with-companion.toml"
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("data/artifact.txt", names)
            self.assertNotIn("target.txt", names)

    def test_import_case_must_be_defined_by_an_imported_companion(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            (external / "data").mkdir()
            (external / "data" / "artifact.txt").write_text("x", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [target]
                description = "Target."
                include_if_exists = ["anything"]
                if_empty = "allow"

                [target.case.release]
                description = "Target release."
                include_if_exists = ["anything"]
                if_empty = "allow"

                [companion.data]
                path = "data"
                description = "Data."
                include = ["artifact.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"
                case = "release"
            ''')
            with self.assertRaises(SelectionError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_import_loader_rejects_recursive_configuration_import_directly(self):
        with tempfile.TemporaryDirectory() as temp:
            external = Path(temp)
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Data."
                include_if_exists = ["file.txt"]
                if_empty = "allow"

                [import.nested]
                root = "."
                configuration = "nested.toml"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            spec = ConfigurationImport(
                name="external",
                root=".",
                configuration="config.toml",
                case=None,
                companions={},
            )

            with self.assertRaisesRegex(
                ConfigurationError,
                r"must not declare \[import\.<name>\] in 0\.4\.0",
            ):
                _load_imported_config(spec, external)

    def test_recursive_configuration_import_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Data."
                include_if_exists = ["file.txt"]
                if_empty = "allow"

                [import.nested]
                root = "."
                configuration = "nested.toml"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            with self.assertRaises(ConfigurationError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_imported_configuration_symlink_cannot_escape_import_root(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside_temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            outside = Path(outside_temp)
            actual = outside / "outside.toml"
            actual.write_text(textwrap.dedent('''
                [companion.data]
                path = "."
                description = "Data."
                include_if_exists = ["x"]
                if_empty = "allow"
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            link = external / "config.toml"
            try:
                link.symlink_to(actual)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            with self.assertRaises(ConfigurationError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_different_real_files_cannot_share_one_archive_path_across_imports(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "a"
            imported_root = workspace / "b"
            for base, value in ((root, "a"), (imported_root, "b")):
                (base / "shared").mkdir(parents=True)
                (base / "shared" / "x.txt").write_text(value, encoding="utf-8")
            (imported_root / "config.toml").write_text(textwrap.dedent('''
                [companion.shared]
                path = "shared"
                description = "Imported shared data."
                include = ["x.txt"]
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [companion.shared]
                path = "shared"
                description = "Root shared data."
                include = ["x.txt"]

                [import.other]
                root = "../b"
                configuration = "config.toml"
            ''')
            with self.assertRaises(SelectionError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_same_real_file_cannot_resolve_to_different_archive_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            sub = project / "sub"
            sub.mkdir(parents=True)
            (sub / "x.txt").write_text("x", encoding="utf-8")
            (project / "config.toml").write_text(textwrap.dedent('''
                [companion.imported]
                path = "sub"
                description = "Imported."
                include = ["x.txt"]
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [companion.local]
                path = "project/sub"
                description = "Root."
                include = ["x.txt"]

                [import.project]
                root = "project"
                configuration = "config.toml"
            ''')
            with self.assertRaises(SelectionError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_same_real_file_same_archive_path_is_deduplicated_across_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            project.mkdir()
            (project / "x.txt").write_text("x", encoding="utf-8")
            (project / "config.toml").write_text(textwrap.dedent('''
                [companion.imported]
                path = "project"
                description = "Imported."
                include = ["x.txt"]
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [companion.local]
                path = "project"
                description = "Root."
                include = ["x.txt"]

                [import.project]
                root = "."
                configuration = "project/config.toml"
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist().count("project/x.txt"), 1)

    def test_imported_companion_cannot_escape_import_root_through_symlink(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside_temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            outside = Path(outside_temp)
            (outside / "file.txt").write_text("outside", encoding="utf-8")
            link = external / "linked"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.linked]
                path = "linked"
                description = "Imported companion."
                include = ["file.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            with self.assertRaises(SelectionError):
                plan_archive(config, BuildRequest.create(), cwd=root)


    def test_import_added_companion_can_use_import_root_itself(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            external.mkdir()
            (external / "artifact.txt").write_text("artifact", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [target]
                description = "Ignored imported target."
                include = ["missing-required.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [import.external.companion.project]
                path = "."
                description = "External project."
                include = ["artifact.txt"]
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual([source.name for source in sources], ["external.project"])
            self.assertEqual(sources[0].config_location, "[import.external.companion.project]")

            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("external/artifact.txt", names)
            self.assertIn("#### Companion `external.project`", readme)
            self.assertNotIn("missing-required.txt", names)

    def test_import_added_companion_name_must_not_duplicate_imported_companion(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            (external / "data").mkdir(parents=True)
            (external / "data" / "x.txt").write_text("x", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Imported data."
                include = ["x.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [import.external.companion.data]
                path = "data"
                description = "Root-added data."
                include = ["x.txt"]
            ''')
            with self.assertRaises(ConfigurationError) as caught:
                plan_archive(config, BuildRequest.create(), cwd=root)
            self.assertIn("external.data", str(caught.exception))

    def test_import_added_and_imported_companions_use_separate_shared_pattern_namespaces(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            imported_dir = external / "imported"
            added_dir = external / "added"
            imported_dir.mkdir(parents=True)
            added_dir.mkdir(parents=True)
            for directory in (imported_dir, added_dir):
                for name in ("keep.txt", "root-hidden.txt", "import-hidden.txt"):
                    (directory / name).write_text(name, encoding="utf-8")

            (external / "config.toml").write_text(textwrap.dedent('''
                [shared.exclude_patterns]
                policy = ["import-hidden.txt"]

                [companion.original]
                path = "imported"
                description = "Imported companion."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["policy"]
                if_empty = "allow"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [shared.exclude_patterns]
                policy = ["root-hidden.txt"]

                [import.external]
                root = "../external"
                configuration = "config.toml"

                [import.external.companion.added]
                path = "added"
                description = "Root-added companion."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["policy"]
                if_empty = "allow"
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())

            self.assertIn("imported/root-hidden.txt", names)
            self.assertNotIn("imported/import-hidden.txt", names)
            self.assertIn("added/import-hidden.txt", names)
            self.assertNotIn("added/root-hidden.txt", names)

    def test_import_case_may_be_defined_only_by_root_added_companion(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            data = external / "data"
            data.mkdir(parents=True)
            (data / "base.txt").write_text("base", encoding="utf-8")
            (data / "release.txt").write_text("release", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [target]
                description = "Ignored target."
                include_if_exists = ["anything"]
                if_empty = "allow"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"
                case = "release"

                [import.external.companion.data]
                path = "data"
                description = "Base data."
                include = ["base.txt"]

                [import.external.companion.data.case.release]
                description = "Release data."
                include = ["release.txt"]
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("data/release.txt", names)
            self.assertNotIn("data/base.txt", names)

    def test_root_target_can_use_imported_shared_patterns_by_qualified_name(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            project = root / "project"
            project.mkdir(parents=True)
            (project / "keep.txt").write_text("keep", encoding="utf-8")
            (project / "skip.txt").write_text("skip", encoding="utf-8")

            external = workspace / "external"
            anchor = external / "anchor"
            anchor.mkdir(parents=True)
            (anchor / "anchor.txt").write_text("anchor", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [shared.exclude_patterns]
                python-dev = ["skip.txt"]

                [companion.anchor]
                path = "anchor"
                description = "Anchor."
                include = ["anchor.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [target]
                description = "Root target."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["external.python-dev"]
                if_empty = "allow"
            ''')
            output = build_archive(config, BuildRequest.create("project"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())

            self.assertIn("project/keep.txt", names)
            self.assertNotIn("project/skip.txt", names)
            self.assertIn("anchor/anchor.txt", names)

    def test_root_and_import_added_companions_can_use_imported_include_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            local = root / "local"
            local.mkdir(parents=True)
            (local / "keep.txt").write_text("keep", encoding="utf-8")
            (local / "other.txt").write_text("other", encoding="utf-8")

            external = workspace / "external"
            anchor = external / "anchor"
            added = external / "added"
            anchor.mkdir(parents=True)
            added.mkdir(parents=True)
            (anchor / "anchor.txt").write_text("anchor", encoding="utf-8")
            (added / "keep.txt").write_text("keep", encoding="utf-8")
            (added / "other.txt").write_text("other", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [shared.include_patterns]
                core = ["keep.txt"]

                [companion.anchor]
                path = "anchor"
                description = "Anchor."
                include = ["anchor.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [companion.local]
                path = "local"
                description = "Root local."
                include_pattern_refs = ["external.core"]

                [import.external]
                root = "../external"
                configuration = "config.toml"

                [import.external.companion.added]
                path = "added"
                description = "Root-added external."
                include_pattern_refs = ["external.core"]
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())

            self.assertIn("local/keep.txt", names)
            self.assertNotIn("local/other.txt", names)
            self.assertIn("added/keep.txt", names)
            self.assertNotIn("added/other.txt", names)

    def test_qualified_imported_pattern_names_keep_include_and_exclude_namespaces_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            project = root / "project"
            project.mkdir(parents=True)
            (project / "keep.txt").write_text("keep", encoding="utf-8")
            (project / "skip.txt").write_text("skip", encoding="utf-8")

            external = workspace / "external"
            anchor = external / "anchor"
            anchor.mkdir(parents=True)
            (anchor / "anchor.txt").write_text("anchor", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [shared.include_patterns]
                policy = ["keep.txt", "skip.txt"]

                [shared.exclude_patterns]
                policy = ["skip.txt"]

                [companion.anchor]
                path = "anchor"
                description = "Anchor."
                include = ["anchor.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [target]
                description = "Root target."
                include_pattern_refs = ["external.policy"]
                exclude_pattern_refs = ["external.policy"]
            ''')
            output = build_archive(config, BuildRequest.create("project"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())

            self.assertIn("project/keep.txt", names)
            self.assertNotIn("project/skip.txt", names)

    def test_root_local_name_conflicting_with_imported_qualified_shared_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            anchor = external / "anchor"
            anchor.mkdir(parents=True)
            (anchor / "anchor.txt").write_text("anchor", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [shared.exclude_patterns]
                policy = ["*.tmp"]

                [companion.anchor]
                path = "anchor"
                description = "Anchor."
                include = ["anchor.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [shared.exclude_patterns]
                "external.policy" = ["*.cache"]

                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            with self.assertRaises(ConfigurationError) as caught:
                plan_archive(config, BuildRequest.create(), cwd=root)
            self.assertIn("external.policy", str(caught.exception))

    def test_unknown_imported_shared_pattern_is_rejected_when_import_is_resolved(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            project = root / "project"
            project.mkdir(parents=True)
            (project / "keep.txt").write_text("keep", encoding="utf-8")
            external = workspace / "external"
            anchor = external / "anchor"
            anchor.mkdir(parents=True)
            (anchor / "anchor.txt").write_text("anchor", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.anchor]
                path = "anchor"
                description = "Anchor."
                include = ["anchor.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [target]
                description = "Root target."
                include = ["keep.txt"]
                exclude_pattern_refs = ["external.missing"]
            ''')
            with self.assertRaises(ConfigurationError) as caught:
                plan_archive(config, BuildRequest.create("project"), cwd=root)
            self.assertIn("external.missing", str(caught.exception))

    def test_root_case_can_use_imported_optional_include_pattern(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            project = root / "project"
            project.mkdir(parents=True)
            (project / "docs.txt").write_text("docs", encoding="utf-8")

            external = workspace / "external"
            anchor = external / "anchor"
            anchor.mkdir(parents=True)
            (anchor / "anchor.txt").write_text("anchor", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [shared.include_patterns]
                docs = ["docs.txt"]

                [companion.anchor]
                path = "anchor"
                description = "Anchor."
                include = ["anchor.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "config.toml"

                [target.case.review]
                description = "Review target."
                include_if_exists_pattern_refs = ["external.docs"]
                if_empty = "allow"
            ''')
            output = build_archive(
                config,
                BuildRequest.create("project", case="review"),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("project/docs.txt", names)


    def test_root_and_import_companions_may_share_local_name_because_logical_names_differ(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root_data = root / "root-data"
            root_data.mkdir(parents=True)
            (root_data / "root.txt").write_text("root", encoding="utf-8")

            external = workspace / "external"
            external_data = external / "external-data"
            external_data.mkdir(parents=True)
            (external_data / "external.txt").write_text("external", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "external-data"
                description = "External data."
                include = ["external.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [companion.data]
                path = "root-data"
                description = "Root data."
                include = ["root.txt"]

                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual(
                {source.name for source in sources},
                {"data", "external.data"},
            )


if __name__ == "__main__":
    unittest.main()
