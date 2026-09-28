from pathlib import Path
import os
import subprocess
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from _temp import resolved_temporary_directory
from _builder_support import BuilderTestCase

import dirpluck._filesystem as filesystem_module
from dirpluck._archive import plan_archive, render_archive_tree
from dirpluck._builder_common import _is_link_like
from dirpluck._builder_models import BuildRequest
from dirpluck._effective import resolve_sources
from dirpluck.builder import build_archive
from dirpluck.config import load_config
from dirpluck.errors import SelectionError


class SelectionTests(BuilderTestCase):
    def test_match_selects_full_root_relative_file_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            for branch in ("core", "ui", "old"):
                dist = project / "packages" / branch / "dist"
                dist.mkdir(parents=True)
                (dist / f"pkg-{branch}.whl").write_text(branch, encoding="utf-8")
                (dist / f"pkg-{branch}.txt").write_text(branch, encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = [{ match = 'packages/(core|ui)/dist/.*\.whl' }]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/packages/core/dist/pkg-core.whl", names)
            self.assertIn("application/packages/ui/dist/pkg-ui.whl", names)
            self.assertNotIn("application/packages/old/dist/pkg-old.whl", names)
            self.assertFalse(any(name.endswith(".txt") for name in names))

    def test_match_directory_path_uses_trailing_slash_and_selects_subtree(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application" / "plugins"
            for name in ("plugin-core", "plugin-ui", "plugin-old"):
                directory = project / name
                directory.mkdir(parents=True)
                (directory / "inside.txt").write_text(name, encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = [{ match = 'plugins/plugin-(core|ui)/' }]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/plugins/plugin-core/inside.txt", names)
            self.assertIn("application/plugins/plugin-ui/inside.txt", names)
            self.assertNotIn("application/plugins/plugin-old/inside.txt", names)

    def test_match_without_trailing_slash_does_not_match_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            directory = root / "application" / "cache"
            directory.mkdir(parents=True)
            (directory / "inside.txt").write_text("x", encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = [{ match = 'cache' }]
            """)
            with self.assertRaisesRegex(SelectionError, "no matches"):
                build_archive(config, BuildRequest.create("./application/"))

    def test_match_may_allows_zero_matches(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            project.mkdir()
            (project / "README.md").write_text("readme", encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = ["README.md"]
                may = [{ match = 'docs/.*\.md' }]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                self.assertIn("application/README.md", archive.namelist())

    def test_match_and_ordinary_patterns_deduplicate_selected_files(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "application" / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("main", encoding="utf-8")
            (src / "helper.py").write_text("helper", encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = [
                    "src/main.py",
                    { match = 'src/.*\.py' },
                ]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
            self.assertEqual(names.count("application/src/main.py"), 1)
            self.assertEqual(names.count("application/src/helper.py"), 1)

    def test_match_ignore_excludes_files_and_directory_subtrees(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "application" / "src"
            src.mkdir(parents=True)
            (src / "keep.py").write_text("keep", encoding="utf-8")
            (src / "skip.tmp").write_text("skip", encoding="utf-8")
            generated = src / "generated"
            generated.mkdir()
            (generated / "inside.py").write_text("generated", encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = ["src/"]
                ignore = [
                    { match = 'src/.*\.tmp' },
                    { match = 'src/generated/' },
                ]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/keep.py", names)
            self.assertNotIn("application/src/skip.tmp", names)
            self.assertNotIn("application/src/generated/inside.py", names)

    def test_match_ignore_overrides_required_match(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "application" / "src"
            src.mkdir(parents=True)
            (src / "secret.py").write_text("x", encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = [{ match = 'src/secret\.py' }]
                ignore = [{ match = 'src/secret\.py' }]
            """)
            with self.assertRaisesRegex(SelectionError, "no matches"):
                build_archive(config, BuildRequest.create("./application/"))

    def test_match_is_available_to_always_sources(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "documents"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            (docs / "notes.txt").write_text("notes", encoding="utf-8")
            config = self._config(root, r"""
                [always.documents]
                path = "documents"
                must = [{ match = '.*\.md' }]
            """)
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("documents/guide.md", names)
            self.assertNotIn("documents/notes.txt", names)

    def test_match_shared_reference_materializes_and_selects(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            src = root / "application" / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("x", encoding="utf-8")
            (src / "main.txt").write_text("x", encoding="utf-8")
            config = self._config(root, r"""
                [shared.must]
                python = [{ match = 'src/.*\.py' }]

                [pluck]
                must = [["python"]]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/main.py", names)
            self.assertNotIn("application/src/main.txt", names)

    def test_match_is_available_in_pluck_cases(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            src = project / "src"
            src.mkdir(parents=True)
            (project / "README.md").write_text("readme", encoding="utf-8")
            (src / "main.py").write_text("python", encoding="utf-8")
            (src / "main.txt").write_text("text", encoding="utf-8")
            config = self._config(root, r"""
                [pluck]
                must = ["README.md"]

                [pluck.case.review]
                must = [{ match = 'src/.*\.py' }]
            """)
            output = build_archive(
                config, BuildRequest.create("./application/", case="review")
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/main.py", names)
            self.assertNotIn("application/src/main.txt", names)
            self.assertNotIn("application/README.md", names)

    def test_required_symlink_entry_is_not_selectable(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
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
                [always.references]
                path = {source.as_posix()!r}
                description = "References."
                must = ["escape.txt"]
            ''')
            with self.assertRaisesRegex(SelectionError, r"matched only symbolic links or Windows junctions"):
                plan_archive(config, BuildRequest.create())

    def test_optional_symlink_entry_is_reported_missing_without_error(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            source = root / "references"
            source.mkdir()
            external = Path(other) / "external.txt"
            external.write_text("secret", encoding="utf-8")
            link = source / "optional.txt"
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, """
                [always.references]
                path = "references"
                description = "References."
                may = ["optional.txt"]
                allow_empty = true
            """)
            plan = plan_archive(config, BuildRequest.create())
            self.assertEqual(plan.optional_missing, ("references/optional.txt",))
            self.assertEqual(plan.skipped_link_count, 1)
            self.assertNotIn("references/optional.txt", plan.entries)

    def test_ignored_symlink_is_not_counted_as_skipped_link(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "application"
            src = project / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            secret = Path(other) / "secret.pem"
            secret.write_text("secret", encoding="utf-8")
            link = src / "secret.pem"
            try:
                link.symlink_to(secret)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["src/"]
                ignore = ["*.pem"]
            """)
            plan = plan_archive(config, BuildRequest.create("./application/"))
            self.assertEqual(plan.skipped_link_count, 0)
            self.assertIn("application/src/main.py", plan.entries)
            self.assertNotIn("application/src/secret.pem", plan.entries)

    def test_ignored_symlink_does_not_produce_link_only_must_error(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            source = root / "references"
            source.mkdir()
            secret = Path(other) / "secret.pem"
            secret.write_text("secret", encoding="utf-8")
            link = source / "secret.pem"
            try:
                link.symlink_to(secret)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, """
                [always.references]
                path = "references"
                description = "References."
                must = ["secret.pem"]
                ignore = ["*.pem"]
            """)
            with self.assertRaisesRegex(SelectionError, r"must pattern\(s\) with no matches") as raised:
                plan_archive(config, BuildRequest.create())
            self.assertNotIn("matched only symbolic links", str(raised.exception))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable on this platform")
    def test_optional_wildcard_silently_ignores_special_filesystem_entry(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "data"
            source.mkdir()
            (source / "regular.txt").write_text("regular\n", encoding="utf-8")
            os.mkfifo(source / "pipe")
            config = self._config(root, """
                [always.data]
                path = "data"
                description = "Data."
                may = ["*", "*/"]
            """)
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("data/regular.txt", plan.entries)
            self.assertNotIn("data/pipe", plan.entries)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable on this platform")
    def test_optional_special_filesystem_entry_is_reported_missing_without_error(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "data"
            source.mkdir()
            os.mkfifo(source / "pipe")
            config = self._config(root, """
                [always.data]
                path = "data"
                description = "Data."
                may = ["pipe"]
                allow_empty = true
            """)
            plan = plan_archive(config, BuildRequest.create())
            self.assertEqual(plan.optional_missing, ("data/pipe",))
            self.assertNotIn("data/pipe", plan.entries)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable on this platform")
    def test_recursive_directory_selection_silently_ignores_special_filesystem_entry(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "data"
            nested = source / "nested"
            nested.mkdir(parents=True)
            (nested / "regular.txt").write_text("regular\n", encoding="utf-8")
            os.mkfifo(nested / "pipe")
            config = self._config(root, """
                [always.data]
                path = "data"
                description = "Data."
                must = ["nested/"]
            """)
            plan = plan_archive(config, BuildRequest.create())
            self.assertIn("data/nested/regular.txt", plan.entries)
            self.assertNotIn("data/nested/pipe", plan.entries)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable on this platform")
    def test_required_special_filesystem_entry_has_reasoned_error(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "data"
            source.mkdir()
            os.mkfifo(source / "pipe")
            config = self._config(root, """
                [always.data]
                path = "data"
                description = "Data."
                must = ["pipe"]
            """)
            with self.assertRaisesRegex(
                SelectionError,
                r"matched only unsupported special filesystem entries",
            ):
                plan_archive(config, BuildRequest.create())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable on this platform")
    def test_ignored_special_filesystem_entry_is_ordinary_missing_for_must(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "data"
            source.mkdir()
            os.mkfifo(source / "pipe")
            config = self._config(root, """
                [always.data]
                path = "data"
                description = "Data."
                must = ["pipe"]
                ignore = ["pipe"]
            """)
            with self.assertRaisesRegex(SelectionError, r"must pattern\(s\) with no matches") as raised:
                plan_archive(config, BuildRequest.create())
            self.assertNotIn("unsupported special filesystem entries", str(raised.exception))

    def test_windows_junction_detection_fails_closed_without_reparse_tag_constant(self):
        with resolved_temporary_directory() as temp:
            path = Path(temp) / "entry"
            path.mkdir()
            with (
                patch.object(filesystem_module.os, "name", "nt"),
                patch.object(
                    filesystem_module.stat,
                    "IO_REPARSE_TAG_MOUNT_POINT",
                    None,
                    create=True,
                ),
            ):
                with self.assertRaisesRegex(SelectionError, r"cannot safely inspect Windows junctions"):
                    _is_link_like(path)

    def test_windows_junction_detection_fails_closed_without_reparse_tag_metadata(self):
        with resolved_temporary_directory() as temp:
            path = Path(temp) / "entry"
            path.mkdir()
            with (
                patch.object(filesystem_module.os, "name", "nt"),
                patch.object(
                    filesystem_module.stat,
                    "IO_REPARSE_TAG_MOUNT_POINT",
                    0xA0000003,
                    create=True,
                ),
            ):
                with self.assertRaisesRegex(SelectionError, r"st_reparse_tag is unavailable"):
                    _is_link_like(path)

    def test_always_source_cannot_use_filesystem_root(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            filesystem_root = Path(root.anchor)
            config = self._config(root, f'''
                [always.root]
                path = {filesystem_root.as_posix()!r}
                description = "Filesystem root."
                may = ["*", "*/"]
                allow_empty = true
            ''')
            with self.assertRaisesRegex(SelectionError, "filesystem root"):
                resolve_sources(config, BuildRequest.create())

    def test_must_star_matches_files_and_directories_at_fixed_depth(self):
        with resolved_temporary_directory() as temp:
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
                [pluck]
                description = "Patterns."
                must = [
                    "dist/package-*.whl",
                    "packages/*/dist/pkg-*.whl",
                    "plugins/foo*bar/",
                ]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
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

    def test_literal_must_is_case_sensitive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            project.mkdir()
            (project / "readme.md").write_text("lowercase", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                description = "Literal case-sensitive."
                must = ["README.md"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("./application/"))

    def test_must_star_is_case_sensitive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            dist = root / "application" / "dist"
            dist.mkdir(parents=True)
            (dist / "pkg-one.whl").write_bytes(b"one")
            (dist / "PKG-two.whl").write_bytes(b"two")
            config = self._config(root, '''
                [pluck]
                description = "Case-sensitive."
                must = ["dist/pkg-*.whl"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ["README.md", "application/dist/pkg-one.whl"])

    def test_nested_must_preserves_intermediate_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            dist = root / "shikumi" / "dist"
            dist.mkdir(parents=True)
            (dist / "shikumi-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
            config = self._config(root, '''
                [pluck]
                description = "Wheel."
                must = ["dist/shikumi-0.1.0-py3-none-any.whl"]
            ''')
            output = build_archive(config, BuildRequest.create("./shikumi/"))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ["README.md", "shikumi/dist/shikumi-0.1.0-py3-none-any.whl"])

    def test_may_adds_existing_and_ignores_missing(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("x", encoding="utf-8")
            (project / "tests").mkdir()
            (project / "tests" / "test_main.py").write_text("x", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                description = "Optional extras."
                must = ["src/"]
                may = ["tests/", "docs/", "CHANGELOG.md"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/main.py", names)
            self.assertIn("application/tests/test_main.py", names)
            self.assertNotIn("application/docs", names)

    def test_optional_only_defaults_to_error_when_target_is_empty(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [pluck]
                description = "Optional."
                may = ["src/", "README.md"]
            ''')
            with self.assertRaises(SelectionError):
                build_archive(config, BuildRequest.create("./application/"))

    def test_allow_empty_preserves_empty_target_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [pluck]
                description = "Greenfield target."
                may = ["src/", "README.md"]
                allow_empty = true
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"README.md", "application/"})
                readme = archive.read("README.md").decode("utf-8")
            self.assertIn("## `application/`\n\nFiles: 0\n\nGreenfield target.", readme)
            self.assertNotIn("Empty result policy", readme)

    def test_preview_reports_allowed_empty_target(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [pluck]
                description = "Greenfield target."
                may = ["src/"]
                allow_empty = true
            ''')
            plan = plan_archive(config, BuildRequest.create("./application/"), allow_missing=True)
            self.assertIn("target (`application/`): empty, allowed", render_archive_tree(plan))


    def test_preview_renders_missing_match_expression_as_opaque_label(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, r'''
                [pluck]
                may = [{ match = 'src/.*\.py' }]
                allow_empty = true
            ''')
            plan = plan_archive(config, BuildRequest.create("./application/"), allow_missing=True)
            tree = render_archive_tree(plan)
            self.assertIn("Unmatched selection entries:", tree)
            self.assertIn("{ match = 'src/.*", tree.split("Unmatched selection entries:", 1)[1])
            self.assertIn("[optional missing]", tree.split("Unmatched selection entries:", 1)[1])
            self.assertNotIn("{ match = 'src/", tree.split("Unmatched selection entries:", 1)[0])

    def test_preview_distinguishes_required_and_optional_missing_patterns(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "application").mkdir()
            config = self._config(root, '''
                [pluck]
                description = "Dry run."
                must = ["src/"]
                may = ["tests/"]
            ''')
            plan = plan_archive(config, BuildRequest.create("./application/"), allow_missing=True)
            tree = render_archive_tree(plan)
            self.assertIn("src/ [missing]", tree)
            self.assertIn("tests/ [optional missing]", tree)
            self.assertIn("empty, would error", tree)

    def test_directory_must_is_recursive_and_name_ignores_apply(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "application", "app")
            config = self._config(root, '''
                [pluck]
                description = "Recursive directory."
                must = ["src/"]
                ignore = ["generated/", "__pycache__/", ".DS_Store", "*.pyc"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/module.py", names)
            self.assertIn("application/src/nested/helper.py", names)
            self.assertNotIn("application/src/generated/skip.py", names)
            self.assertNotIn("application/src/nested/cache.pyc", names)

    def test_ignore_supports_exact_prefix_suffix_and_contains(self):
        with resolved_temporary_directory() as temp:
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
                [pluck]
                description = "Filters."
                must = ["src/"]
                ignore = ["exact.tmp", "prefix-*", "*-suffix.py", "*draft*", "cache/", "temp*/", "*generated/", "*junk*/"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/keep.py", names)
            self.assertEqual([name for name in names if name.endswith("inside.py")], [])

    def test_recursive_directory_must_skips_external_directory_symlink(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
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
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["src/"]
            """)
            plan = plan_archive(config, BuildRequest.create("./application/"))
            self.assertEqual(plan.skipped_link_count, 1)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertNotIn("application/src/external-dir", names)
            self.assertNotIn("application/src/external-dir/secret.py", names)

    def test_recursive_directory_must_skips_internal_directory_symlink(self):
        with resolved_temporary_directory() as temp:
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
                [pluck]
                description = "Target."
                must = ["src/"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/real/inside.py", names)
            self.assertNotIn("application/src/internal-link/inside.py", names)

    def test_file_symlink_is_skipped_without_reading_target(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "application"
            (project / "src").mkdir(parents=True)
            (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            external = Path(other) / "external.py"
            external.write_text("SECRET = 1\n", encoding="utf-8")
            link = project / "src" / "external.py"
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["src/"]
            """)
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/main.py", names)
            self.assertNotIn("application/src/external.py", names)

    def test_ignore_prunes_directory_before_traversal(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            src = project / "src"
            ignored = src / "node_modules"
            ignored.mkdir(parents=True)
            (ignored / "deep.txt").write_text("ignored", encoding="utf-8")
            (src / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["src/"]
                ignore = ["node_modules/"]
            """)
            original_iterdir = Path.iterdir

            def guarded_iterdir(path):
                if path == ignored:
                    raise AssertionError("ignored directory was traversed")
                return original_iterdir(path)

            with patch.object(Path, "iterdir", new=guarded_iterdir):
                output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/src/main.py", names)
            self.assertNotIn("application/src/node_modules/deep.txt", names)

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics are Windows-specific")
    def test_windows_directory_junction_is_skipped_without_traversal(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "application"
            src = project / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
            outside = Path(other) / "outside"
            outside.mkdir()
            (outside / "secret.py").write_text("SECRET = 1\n", encoding="utf-8")
            junction = src / "junction"
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                self.fail(f"could not create Windows directory junction: {created.stderr or created.stdout}")

            config = self._config(root, """
                [pluck]
                description = "Target."
                must = ["src/"]
            """)
            plan = plan_archive(config, BuildRequest.create("./application/"))
            self.assertEqual(plan.skipped_link_count, 1)
            self.assertIn("application/src/main.py", plan.entries)
            self.assertNotIn("application/src/junction/secret.py", plan.entries)

    def test_explicit_target_symlink_is_not_selectable(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            real = root / "real"
            real.mkdir()
            link = root / "linked"
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, """
                [pluck]
                description = "Project."
                may = ["src/"]
                allow_empty = true
            """)
            with self.assertRaisesRegex(SelectionError, "symbolic link"):
                resolve_sources(config, BuildRequest.create("./linked/"))

class IgnorePathReferenceSelectionTests(BuilderTestCase):
    def test_file_path_reference_excludes_only_the_exact_selection_relative_file(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "tests" / "fixtures").mkdir(parents=True)
            (project / "other").mkdir()
            (project / "tests" / "fixtures" / "big.bin").write_text("drop", encoding="utf-8")
            (project / "other" / "big.bin").write_text("keep", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["tests/", "other/"]
                ignore = [["./tests/fixtures/big.bin"]]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertNotIn("application/tests/fixtures/big.bin", names)
            self.assertIn("application/other/big.bin", names)

    def test_directory_path_reference_prunes_subtree_and_overlap_is_order_independent(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            fixtures = project / "tests" / "fixtures"
            fixtures.mkdir(parents=True)
            (fixtures / "big.bin").write_text("drop", encoding="utf-8")
            (fixtures / "small.txt").write_text("drop", encoding="utf-8")
            (project / "tests" / "keep.txt").write_text("keep", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["tests/"]
                ignore = [
                    ["./tests/fixtures/big.bin"],
                    "big.bin",
                    ["./tests/fixtures/"],
                ]
            ''')
            original_iterdir = Path.iterdir

            def guarded_iterdir(path):
                if path == fixtures:
                    raise AssertionError("path-ignored directory was traversed")
                return original_iterdir(path)

            with patch.object(Path, "iterdir", new=guarded_iterdir):
                output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/tests/keep.txt", names)
            self.assertNotIn("application/tests/fixtures/big.bin", names)
            self.assertNotIn("application/tests/fixtures/small.txt", names)

    def test_path_reference_without_trailing_slash_broadly_excludes_file_or_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            fixtures = project / "tests" / "fixtures"
            fixtures.mkdir(parents=True)
            (fixtures / "drop.txt").write_text("drop", encoding="utf-8")
            (project / "tests" / "keep.txt").write_text("keep", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["tests/"]
                ignore = [["./tests/fixtures"]]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/tests/keep.txt", names)
            self.assertNotIn("application/tests/fixtures/drop.txt", names)

    def test_name_ignore_without_trailing_slash_broadly_excludes_files_and_directories(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "a").mkdir(parents=True)
            (project / "a" / "noise").write_text("drop", encoding="utf-8")
            (project / "b" / "noise").mkdir(parents=True)
            (project / "b" / "noise" / "drop.txt").write_text("drop", encoding="utf-8")
            (project / "a" / "keep.txt").write_text("keep", encoding="utf-8")
            (project / "b" / "keep.txt").write_text("keep", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["a/", "b/"]
                ignore = ["noise"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/a/keep.txt", names)
            self.assertIn("application/b/keep.txt", names)
            self.assertNotIn("application/a/noise", names)
            self.assertNotIn("application/b/noise/drop.txt", names)

    def test_name_ignore_with_trailing_slash_is_directory_only(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            (project / "a").mkdir(parents=True)
            (project / "a" / "noise").write_text("keep", encoding="utf-8")
            (project / "b" / "noise").mkdir(parents=True)
            (project / "b" / "noise" / "drop.txt").write_text("drop", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["a/", "b/"]
                ignore = ["noise/"]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/a/noise", names)
            self.assertNotIn("application/b/noise/drop.txt", names)


    def test_directory_path_reference_does_not_exclude_same_path_when_it_is_a_file(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            tests = project / "tests"
            tests.mkdir(parents=True)
            (tests / "noise").write_text("keep", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["tests/"]
                ignore = [["./tests/noise/"]]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("application/tests/noise", names)

    def test_path_reference_ignore_suppresses_link_like_diagnostic(self):
        with resolved_temporary_directory() as temp, resolved_temporary_directory() as other:
            root = Path(temp)
            project = root / "application"
            src = project / "src"
            src.mkdir(parents=True)
            (src / "main.py").write_text("keep", encoding="utf-8")
            external = Path(other) / "external.py"
            external.write_text("drop", encoding="utf-8")
            link = src / "external.py"
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            config = self._config(root, '''
                [pluck]
                must = ["src/"]
                ignore = [["./src/external.py"]]
            ''')
            plan = plan_archive(config, BuildRequest.create("./application/"))
            self.assertEqual(plan.skipped_link_count, 0)
            self.assertIn("application/src/main.py", plan.entries)
            self.assertNotIn("application/src/external.py", plan.entries)

    def test_always_path_reference_is_relative_to_always_source_root(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "application"
            project.mkdir()
            (project / "README.md").write_text("project", encoding="utf-8")
            assets = root / "assets"
            (assets / "nested").mkdir(parents=True)
            (assets / "nested" / "secret.txt").write_text("drop", encoding="utf-8")
            (assets / "nested" / "keep.txt").write_text("keep", encoding="utf-8")
            config = self._config(root, '''
                [pluck]
                must = ["README.md"]

                [always.assets]
                path = "assets"
                must = ["nested/"]
                ignore = [["./nested/secret.txt"]]
            ''')
            output = build_archive(config, BuildRequest.create("./application/"))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("assets/nested/keep.txt", names)
            self.assertNotIn("assets/nested/secret.txt", names)


if __name__ == "__main__":
    unittest.main()
