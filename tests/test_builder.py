from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from dirpluck.builder import (
    BuildRequest,
    build_archive,
    plan_archive,
    render_archive_tree,
    resolve_sources,
)
from dirpluck.config import load_config
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

    def test_companion_parent_path_outside_base_uses_resolved_directory_name(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "project"
            external = workspace / "references"
            root.mkdir()
            external.mkdir()
            (external / "note.txt").write_text("reference", encoding="utf-8")
            config = self._config(root, '''
                [companion.references]
                path = "../references"
                description = "External references."
                include = ["note.txt"]
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, external.resolve())
            self.assertEqual(sources[0].archive_root, "references")
            plan = plan_archive(config, BuildRequest.create(), cwd=root)
            self.assertIn("references/note.txt", plan.entries)

    def test_companion_absolute_path_inside_base_preserves_base_relative_archive_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            companion = root / "nested" / "references"
            companion.mkdir(parents=True)
            (companion / "note.txt").write_text("reference", encoding="utf-8")
            config = self._config(root, f'''
                [companion.references]
                path = {companion.as_posix()!r}
                description = "References."
                include = ["note.txt"]
            ''')
            source = resolve_sources(config, BuildRequest.create(), cwd=root)[0]
            self.assertEqual(source.archive_root, "nested/references")

    def test_companion_absolute_path_outside_base_uses_resolved_directory_name(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            external = Path(other) / "references"
            external.mkdir()
            (external / "note.txt").write_text("reference", encoding="utf-8")
            config = self._config(root, f'''
                [companion.references]
                path = {external.as_posix()!r}
                description = "References."
                include = ["note.txt"]
            ''')
            source = resolve_sources(config, BuildRequest.create(), cwd=root)[0]
            self.assertEqual(source.directory, external.resolve())
            self.assertEqual(source.archive_root, "references")
            plan = plan_archive(config, BuildRequest.create(), cwd=root)
            self.assertIn("references/note.txt", plan.entries)

    def test_external_companion_selection_cannot_escape_its_source_boundary(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            external_root = Path(other)
            source = external_root / "references"
            source.mkdir()
            secret = external_root / "secret.txt"
            secret.write_text("secret", encoding="utf-8")
            link = source / "escape.txt"
            try:
                link.symlink_to(secret)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, f'''
                [companion.references]
                path = {source.as_posix()!r}
                description = "References."
                include = ["escape.txt"]
            ''')
            with self.assertRaises(SelectionError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_companion_cannot_use_filesystem_root_as_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            filesystem_root = Path(root.anchor)
            config = self._config(root, f'''
                [companion.root]
                path = {filesystem_root.as_posix()!r}
                description = "Filesystem root."
                include_if_exists = ["*"]
                if_empty = "allow"
            ''')
            with self.assertRaisesRegex(SelectionError, "filesystem root"):
                resolve_sources(config, BuildRequest.create(), cwd=root)

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
            self.assertIn("| project-a/ | Projects selected for review. | 6 |", readme)
            self.assertIn("| project-b/ | Projects selected for review. | 6 |", readme)
            self.assertNotIn("Source", readme.splitlines()[2])


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
            self.assertIn("| application/ | Greenfield target. | 0 |", readme)
            self.assertNotIn("Empty result policy", readme)

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
            self.assertIn("| application/ | Review tests only. | 1 |", readme)
            self.assertNotIn("Case:", readme)
            self.assertNotIn("[target", readme)

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
            self.assertIn("| application/ | Default source. | 1 |", readme)
            self.assertNotIn("Case:", readme)
            self.assertNotIn("[target]", readme)

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
            self.assertIn("| framework/ | Framework review material. | 1 |", readme)
            self.assertIn("| guidelines/ | Guidelines always included. | 1 |", readme)
            self.assertNotIn("companion", readme.lower())

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
            self.assertIn("| documents/ | Archive documents. | 2 |", readme)
            self.assertIn("| assets/ | Assets. | 1 |", readme)
            self.assertNotIn("Case:", readme)
            self.assertNotIn("companion", readme.lower())

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


    def test_archive_readme_includes_effective_about_description(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "application"
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [about]
                description = "Materials prepared for an authentication review."

                [target]
                description = "Application sources."
                include = ["file.txt"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertTrue(
                readme.startswith(
                    "# Archive contents\n\n"
                    "Materials prepared for an authentication review.\n\n"
                    "| Path | Description | Files |\n"
                )
            )

    def test_about_description_resolves_from_outermost_definition_in_import_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            inner = workspace / "inner"
            data = inner / "data"
            root.mkdir()
            data.mkdir(parents=True)
            (data / "note.txt").write_text("note", encoding="utf-8")
            (inner / "dirpluck.toml").write_text(textwrap.dedent('''
                [about]
                description = "Imported materials."

                [companion.data]
                path = "data"
                description = "Reference data."
                include = ["note.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            inherited = self._config(root, '''
                [import.base]
                root = "../inner"
                configuration = "dirpluck.toml"
            ''')
            output = build_archive(inherited, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("\nImported materials.\n\n| Path |", readme)

            outer = self._config(root, '''
                [about]
                description = "Project-specific materials."

                [import.base]
                root = "../inner"
                configuration = "dirpluck.toml"
            ''', output="outer.zip")
            output = build_archive(outer, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("\nProject-specific materials.\n\n| Path |", readme)
            self.assertNotIn("Imported materials.", readme)

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
            self.assertEqual(readme.count("| shikumi-devdoc/ |"), 2)
            self.assertIn("The project currently being changed.", readme)
            self.assertIn("The current built distribution used as a reference.", readme)
            self.assertNotIn("Target", readme)
            self.assertNotIn("Companion", readme)
            self.assertNotIn("Configuration", readme)

    def test_archive_readme_hides_source_paths_by_default(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "application" / "src" / "main.py").write_text("x", encoding="utf-8")
            outside = Path(other) / "reference"
            outside.mkdir()
            (outside / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(root, f'''
                [target]
                description = "Application sources."
                include = ["src"]

                [companion.reference]
                path = {outside.as_posix()!r}
                description = "Reference material."
                include = ["guide.md"]
            ''')
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertEqual(readme.splitlines()[2], "| Path | Description | Files |")
            self.assertNotIn(root.as_posix(), readme)
            self.assertNotIn(outside.as_posix(), readme)

    def test_archive_readme_paths_option_includes_resolved_source_paths(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            target = root / "application"
            (target / "src").mkdir(parents=True)
            (target / "src" / "main.py").write_text("x", encoding="utf-8")
            outside = Path(other) / "reference"
            outside.mkdir()
            (outside / "guide.md").write_text("guide", encoding="utf-8")
            config = self._config(root, f'''
                [target]
                description = "Application sources."
                include = ["src"]

                [companion.reference]
                path = {outside.as_posix()!r}
                description = "Reference material."
                include = ["guide.md"]
            ''')
            output = build_archive(
                config,
                BuildRequest.create("application", paths=True),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                readme = archive.read("README.md").decode("utf-8")
            self.assertEqual(readme.splitlines()[2], "| Path | Description | Files | Source |")
            self.assertIn(target.resolve().as_posix(), readme)
            self.assertIn(outside.resolve().as_posix(), readme)
            self.assertNotIn("Configuration", readme)
            self.assertNotIn("Target", readme)
            self.assertNotIn("Companion", readme)

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

    def test_companion_outside_cwd_through_symlink_is_allowed_and_uses_resolved_name(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "application" / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            outside = Path(other) / "framework"
            (outside / "src").mkdir(parents=True)
            (outside / "src" / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
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
            sources = resolve_sources(config, BuildRequest.create("application"), cwd=root)
            companion = next(source for source in sources if source.kind == "companion")
            self.assertEqual(companion.directory, outside.resolve())
            self.assertEqual(companion.archive_root, "framework")
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("framework/src/helper.py", set(archive.namelist()))

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

    def test_fixed_output_may_use_parent_or_absolute_path(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "project"
            root.mkdir()
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")

            parent_config = self._config(root, '''
                [target]
                description = "Target."
                include = ["src"]
                [output]
                path = "../parent.zip"
                if_exists = "error"
            ''')
            parent_output = build_archive(
                parent_config,
                BuildRequest.create("application"),
                cwd=root,
            )
            self.assertEqual(parent_output, workspace / "parent.zip")
            self.assertTrue(parent_output.is_file())

            absolute = workspace / "absolute.zip"
            absolute_config = self._config(root, f'''
                [target]
                description = "Target."
                include = ["src"]
                [output]
                path = {absolute.as_posix()!r}
                if_exists = "error"
            ''')
            absolute_output = build_archive(
                absolute_config,
                BuildRequest.create("application"),
                cwd=root,
            )
            self.assertEqual(absolute_output, absolute)
            self.assertTrue(absolute_output.is_file())

    def test_generated_output_may_use_absolute_directory(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            project = root / "application" / "src"
            project.mkdir(parents=True)
            (project / "main.py").write_text("x", encoding="utf-8")
            destination = Path(other) / "snapshots"
            config = self._config(root, f'''
                [target]
                description = "Target."
                include = ["src"]
                [output]
                directory = {destination.as_posix()!r}
                timestamp = true
            ''')
            with patch("dirpluck.builder._current_output_timestamp", return_value="20260916-011623"):
                output = build_archive(config, BuildRequest.create("application"), cwd=root)
            self.assertEqual(output, destination / "20260916-011623.zip")
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

    def test_output_path_may_leave_cwd_through_parent_symlink(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            (root / "application" / "src").mkdir(parents=True)
            (root / "application" / "src" / "main.py").write_text("x", encoding="utf-8")
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
            output = build_archive(config, BuildRequest.create("application"), cwd=root)
            self.assertEqual(output, Path(other) / "out.zip")
            self.assertTrue((Path(other) / "out.zip").is_file())


    def test_imported_target_definition_binds_to_cli_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            target = root / "local"
            root.mkdir()
            (target / "src").mkdir(parents=True)
            (target / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            external.mkdir()
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [target]
                description = "Imported selection applied to CLI target."
                include = ["src"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")

            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            output = build_archive(config, BuildRequest.create("local"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("local/src/module.py", names)
            self.assertFalse((external / "unused.zip").exists())

    def test_imported_target_requires_cli_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            root.mkdir()
            external.mkdir()
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [target]
                description = "Imported selection."
                include_if_exists = ["*"]
                if_empty = "allow"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            with self.assertRaisesRegex(SelectionError, "DIRECTORY is required"):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_outer_target_shadows_inner_target_without_resolving_inner_project(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            local = root / "local"
            external = workspace / "external"
            local.mkdir(parents=True)
            external.mkdir()
            (local / "root.txt").write_text("root", encoding="utf-8")
            (external / "config.toml").write_text(textwrap.dedent('''
                [target]
                description = "Shadowed target."
                include = ["never-needed.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [target]
                description = "Root target."
                include = ["root.txt"]

                [import.external]
                root = "../external"
                configuration = "config.toml"
            ''')
            output = build_archive(config, BuildRequest.create("local"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("local/root.txt", names)

    def test_imported_target_does_not_depend_on_configuration_placement(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            target = root / "local"
            root.mkdir()
            target.mkdir()
            (target / "file.txt").write_text("x", encoding="utf-8")
            external.mkdir()
            (external / "custom.toml").write_text(textwrap.dedent('''
                [target]
                description = "Imported selection from an arbitrary config path."
                include = ["file.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "custom.toml"
            ''')
            output = build_archive(config, BuildRequest.create("local"), cwd=root)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("local/file.txt", set(archive.namelist()))

    def test_import_root_may_be_absolute(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            external = Path(other) / "external"
            data = external / "data"
            data.mkdir(parents=True)
            (data / "note.txt").write_text("note", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Imported data."
                include = ["note.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, f'''
                [import.external]
                root = {external.as_posix()!r}
                configuration = "dirpluck.toml"
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, data.resolve())

    def test_imported_target_keeps_imported_companions_on_import_execution_root(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "gp-cli-tools"
            target = root / "dirpluck"
            shikumi = workspace / "shikumi"
            devdoc = workspace / "shikumi-devdoc"
            (target / "src").mkdir(parents=True)
            (target / "src" / "cli.py").write_text("VALUE = 1\n", encoding="utf-8")
            (shikumi / "dist").mkdir(parents=True)
            (devdoc / "dist").mkdir(parents=True)
            (shikumi / "dist" / "shikumi-0.1.0.whl").write_text("wheel", encoding="utf-8")
            (devdoc / "dist" / "shikumi_devdoc-0.1.0.whl").write_text("wheel", encoding="utf-8")
            (shikumi / "dirpluck.toml").write_text(textwrap.dedent('''
                [target]
                description = "Reusable target selection."
                include = ["src"]

                [companion.shikumi]
                path = "shikumi"
                description = "Shikumi wheel."
                include = ["dist/shikumi-*.whl"]

                [companion.devdoc]
                path = "shikumi-devdoc"
                description = "Devdoc wheel."
                include = ["dist/shikumi_devdoc-*.whl"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.shikumi]
                root = ".."
                configuration = "shikumi/dirpluck.toml"
            ''')
            sources = resolve_sources(config, BuildRequest.create("dirpluck"), cwd=root)
            self.assertEqual(
                [(source.key, source.directory) for source in sources],
                [
                    ("target", target.resolve()),
                    ("companion:shikumi", shikumi.resolve()),
                    ("companion:devdoc", devdoc.resolve()),
                ],
            )

    def test_outer_companion_shadows_same_named_inner_companion(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            outer_data = root / "outer-data"
            inner_data = external / "inner-data"
            outer_data.mkdir(parents=True)
            inner_data.mkdir(parents=True)
            (outer_data / "outer.txt").write_text("outer", encoding="utf-8")
            (inner_data / "inner.txt").write_text("inner", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "inner-data"
                description = "Inner data."
                include = ["inner.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [companion.data]
                path = "outer-data"
                description = "Outer data."
                include = ["outer.txt"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual([source.name for source in sources], ["data"])
            self.assertEqual(sources[0].directory, outer_data.resolve())

    def test_distinct_companions_from_layers_coexist(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            (root / "outer").mkdir(parents=True)
            (external / "inner").mkdir(parents=True)
            (root / "outer" / "o.txt").write_text("o", encoding="utf-8")
            (external / "inner" / "i.txt").write_text("i", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.inner]
                path = "inner"
                description = "Inner."
                include = ["i.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [companion.outer]
                path = "outer"
                description = "Outer."
                include = ["o.txt"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual({source.name for source in sources}, {"inner", "outer"})

    def test_import_overlay_companion_shadows_directly_imported_companion(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            (external / "old").mkdir(parents=True)
            (external / "new").mkdir(parents=True)
            (external / "old" / "old.txt").write_text("old", encoding="utf-8")
            (external / "new" / "new.txt").write_text("new", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.project]
                path = "old"
                description = "Old."
                include = ["old.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"

                [import.external.companion.project]
                path = "new"
                description = "New."
                include = ["new.txt"]
            ''')
            sources = resolve_sources(config, BuildRequest.create(), cwd=root)
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].name, "project")
            self.assertEqual(sources[0].directory, (external / "new").resolve())

    def test_outer_shared_pattern_shadows_inner_and_rebinds_inner_source(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            data = external / "data"
            data.mkdir(parents=True)
            for name in ("keep.txt", "inner.tmp", "outer.tmp"):
                (data / name).write_text(name, encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [shared.exclude_patterns]
                policy = ["inner.tmp"]

                [companion.data]
                path = "data"
                description = "Data."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["policy"]
                if_empty = "allow"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [shared.exclude_patterns]
                policy = ["outer.tmp"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("data/inner.tmp", names)
            self.assertNotIn("data/outer.tmp", names)
            self.assertIn("data/keep.txt", names)

    def test_outer_layer_may_supply_missing_shared_pattern_to_inner_source(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            data = external / "data"
            data.mkdir(parents=True)
            (data / "keep.txt").write_text("keep", encoding="utf-8")
            (data / "skip.txt").write_text("skip", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Data."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["policy"]
                if_empty = "allow"

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [shared.exclude_patterns]
                policy = ["skip.txt"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("data/keep.txt", names)
            self.assertNotIn("data/skip.txt", names)

    def test_unresolved_shared_pattern_after_layering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            (external / "data").mkdir(parents=True)
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Data."
                include_pattern_refs = ["missing"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            with self.assertRaisesRegex(ConfigurationError, "missing"):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_linear_import_chain_has_no_depth_limit_in_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            names = ["a", "b", "c", "d", "e"]
            for index, name in enumerate(names):
                project = workspace / name
                data = project / f"data-{name}"
                data.mkdir(parents=True)
                (data / f"{name}.txt").write_text(name, encoding="utf-8")
                parts = [
                    f"[companion.{name}]",
                    f'path = "data-{name}"',
                    f'description = "{name}."',
                    f'include = ["{name}.txt"]',
                    "",
                ]
                if index + 1 < len(names):
                    next_name = names[index + 1]
                    parts += [
                        f"[import.{next_name}]",
                        f'root = "../{next_name}"',
                        'configuration = "dirpluck.toml"',
                        "",
                    ]
                parts += [
                    "[output]",
                    'path = "unused.zip"',
                    'if_exists = "error"',
                    "",
                ]
                (project / "dirpluck.toml").write_text("\n".join(parts), encoding="utf-8")

            root = workspace / "a"
            config = load_config(root / "dirpluck.toml")
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                zipped = set(archive.namelist())
            for name in names:
                self.assertIn(f"data-{name}/{name}.txt", zipped)

    def test_configuration_import_cycle_is_rejected_with_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            for name, next_name in (("a", "b"), ("b", "c"), ("c", "a")):
                project = workspace / name
                project.mkdir()
                (project / "dirpluck.toml").write_text(textwrap.dedent(f'''
                    [import.{next_name}]
                    root = "../{next_name}"
                    configuration = "dirpluck.toml"

                    [output]
                    path = "unused.zip"
                    if_exists = "error"
                '''), encoding="utf-8")
            root = workspace / "a"
            config = load_config(root / "dirpluck.toml")
            with self.assertRaisesRegex(ConfigurationError, "cycle") as caught:
                plan_archive(config, BuildRequest.create(), cwd=root)
            self.assertIn("a", str(caught.exception))
            self.assertIn("b", str(caught.exception))
            self.assertIn("c", str(caught.exception))

    def test_global_case_applies_after_layering(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            target_dir = root / "target"
            target_dir.mkdir(parents=True)
            (target_dir / "release.txt").write_text("release", encoding="utf-8")
            data = external / "data"
            data.mkdir(parents=True)
            (data / "base.txt").write_text("base", encoding="utf-8")
            (data / "release.txt").write_text("release", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Base data."
                include = ["base.txt"]

                [companion.data.case.release]
                description = "Release data."
                include = ["release.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [target.case.release]
                description = "Release target."
                include = ["release.txt"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            output = build_archive(
                config,
                BuildRequest.create("target", case="release"),
                cwd=root,
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("target/release.txt", names)
            self.assertIn("data/release.txt", names)
            self.assertNotIn("data/base.txt", names)

    def test_effective_companion_case_not_defined_by_effective_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "framework").mkdir()
            config = self._config(root, '''
                [target]
                description = "Default."
                include = ["x.txt"]

                [target.case.review]
                description = "Review."
                include = ["x.txt"]

                [companion.framework]
                path = "framework"
                description = "Framework."
                include_if_exists = ["*"]
                if_empty = "allow"

                [companion.framework.case.release]
                description = "Release."
                include_if_exists = ["*"]
                if_empty = "allow"
            ''')
            with self.assertRaisesRegex(ConfigurationError, "not defined by target"):
                plan_archive(config, BuildRequest.create("."), cwd=root)

    def test_source_less_effective_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self._config(root, "")
            with self.assertRaisesRegex(ConfigurationError, "no Target or Companion"):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_inner_output_is_validated_but_not_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            root.mkdir()
            external = workspace / "external"
            data = external / "data"
            data.mkdir(parents=True)
            (data / "x.txt").write_text("x", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.data]
                path = "data"
                description = "Data."
                include = ["x.txt"]

                [output]
                path = "inner.zip"
                if_exists = "overwrite"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''', output="outer.zip")
            output = build_archive(config, BuildRequest.create(), cwd=root)
            self.assertEqual(output, root / "outer.zip")
            self.assertFalse((external / "inner.zip").exists())

    def test_different_surviving_sources_still_collide_on_same_archive_path(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            for base, value in ((root, "root"), (external, "external")):
                (base / "shared").mkdir(parents=True)
                (base / "shared" / "x.txt").write_text(value, encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.inner]
                path = "shared"
                description = "Inner."
                include = ["x.txt"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, '''
                [companion.outer]
                path = "shared"
                description = "Outer."
                include = ["x.txt"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            ''')
            with self.assertRaises(SelectionError):
                plan_archive(config, BuildRequest.create(), cwd=root)

    def test_import_root_is_relative_to_declaring_configuration_at_each_depth(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            a = workspace / "projects" / "a"
            b = workspace / "projects" / "b"
            c = workspace / "vendor" / "c"
            a.mkdir(parents=True)
            b.mkdir(parents=True)
            (c / "data").mkdir(parents=True)
            (c / "data" / "c.txt").write_text("c", encoding="utf-8")
            (c / "dirpluck.toml").write_text(textwrap.dedent('''
                [companion.c]
                path = "data"
                description = "C."
                include = ["c.txt"]
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            (b / "dirpluck.toml").write_text(textwrap.dedent('''
                [import.c]
                root = "../../vendor/c"
                configuration = "dirpluck.toml"
                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            (a / "dirpluck.toml").write_text(textwrap.dedent('''
                [import.b]
                root = "../b"
                configuration = "dirpluck.toml"
                [output]
                path = "out.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = load_config(a / "dirpluck.toml")
            sources = resolve_sources(config, BuildRequest.create(), cwd=a)
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, (c / "data").resolve())
    def test_duplicate_effective_patterns_are_rejected_after_layering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            project.mkdir()
            (project / "src").mkdir()
            config = self._config(root, """
                [shared.include_patterns]
                common = ["src"]

                [target]
                description = "Target."
                include_pattern_refs = ["common"]
                include = ["src"]
            """)
            with self.assertRaisesRegex(ConfigurationError, "duplicate effective include"):
                plan_archive(config, BuildRequest.create("project"), cwd=root)

    def test_outer_shared_shadow_can_remove_inner_duplicate_before_effective_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "root"
            external = workspace / "external"
            root.mkdir()
            data = external / "data"
            (data / "src").mkdir(parents=True)
            (data / "docs").mkdir()
            (data / "src" / "a.txt").write_text("a", encoding="utf-8")
            (data / "docs" / "b.txt").write_text("b", encoding="utf-8")
            (external / "dirpluck.toml").write_text(textwrap.dedent('''
                [shared.include_patterns]
                common = ["src"]

                [companion.data]
                path = "data"
                description = "Data."
                include_pattern_refs = ["common"]
                include = ["src"]

                [output]
                path = "unused.zip"
                if_exists = "error"
            '''), encoding="utf-8")
            config = self._config(root, """
                [shared.include_patterns]
                common = ["docs"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"
            """)
            output = build_archive(config, BuildRequest.create(), cwd=root)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("data/src/a.txt", names)
            self.assertIn("data/docs/b.txt", names)



if __name__ == "__main__":
    unittest.main()
