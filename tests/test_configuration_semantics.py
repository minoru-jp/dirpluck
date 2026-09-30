from pathlib import Path
import os
import textwrap
import unittest
from unittest.mock import patch
import zipfile

from _temp import resolved_temporary_directory

from dirpluck._archive import plan_archive
from dirpluck._builder_models import BuildRequest
from dirpluck._effective import resolve_sources
from dirpluck.builder import build_archive
from dirpluck.config import load_config
from dirpluck.errors import ConfigurationError, SelectionError


class ConfigurationSemanticsTests(unittest.TestCase):
    def _write(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def test_about_may_define_base_without_description(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(self._write(root / "default.dirpluck", '''
                [about]
                base = "../common/base.dirpluck"

                [output]
                path = "out.zip"
            '''))
            self.assertIsNone(config.about_description)
            self.assertEqual(config.base, "../common/base.dirpluck")

    def test_empty_about_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root / "default.dirpluck", '''
                    [about]

                    [output]
                    path = "out.zip"
                '''))

    def test_legacy_configuration_vocabulary_is_rejected(self):
        bodies = (
            '''[target]\ndescription="x"\ninclude=["src"]\n[output]\npath="out.zip"''',
            '''[companion.x]\npath="x"\ndescription="x"\ninclude=["src"]\n[output]\npath="out.zip"''',
            '''[import.base]\nroot="."\nconfiguration="base.dirpluck"\n[output]\npath="out.zip"''',
        )
        for body in bodies:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(Path(temp) / "default.dirpluck", body))

    def test_selection_uses_inline_shared_references_by_namespace(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(self._write(root / "default.dirpluck", '''
                [shared.must]
                core = ["src", "pyproject.toml"]
                [shared.may]
                docs = ["README.md", "docs"]
                [shared.ignore]
                noise = ["__pycache__/", "*.pyc"]

                [pluck]
                description = "Project."
                must = ["LICENSE", { shared = "core" }]
                may = [{ shared = "docs" }]
                ignore = [".git/", { shared = "noise" }]

                [scope]

                [output]
                path = "out.zip"
            '''))
            (root / "project").mkdir()
            selection = resolve_sources(config, BuildRequest.create("./project/"))[0].selection
            self.assertEqual(selection.must, ("LICENSE", "src", "pyproject.toml"))
            self.assertEqual(selection.may, ("README.md", "docs"))
            self.assertEqual(
                tuple(item.raw for item in selection.ignore),
                (".git/", "__pycache__/", "*.pyc"),
            )

    def test_invalid_shared_reference_shapes_are_rejected(self):
        invalid = ("[]", '[["a", "b"]]', "[[123]]")
        for value in invalid:
            with self.subTest(value=value), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(root / "default.dirpluck", f'''
                        [pluck]
                        description = "Project."
                        must = {value}
                        [scope]
                        [output]
                        path = "out.zip"
                    '''))

    def test_allow_empty_defaults_false_and_rejects_must(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(self._write(root / "default.dirpluck", '''
                [always.x]
                path = "x"
                description = "X."
                may = ["optional.txt"]
                [output]
                path = "out.zip"
            '''))
            self.assertFalse(config.always["x"].selection.allow_empty)

            with self.assertRaises(ConfigurationError):
                load_config(self._write(root / "bad.dirpluck", '''
                    [always.x]
                    path = "x"
                    description = "X."
                    must = ["required.txt"]
                    allow_empty = true
                    [output]
                    path = "out.zip"
                '''))

    def test_fixed_output_overwrite_defaults_false(self):
        with resolved_temporary_directory() as temp:
            config = load_config(self._write(Path(temp) / "default.dirpluck", '''
                [always.x]
                path = "x"
                description = "X."
                may = ["a"]
                [output]
                path = "result.zip"
            '''))
            self.assertFalse(config.output.overwrite)
            self.assertFalse(config.output.timestamp)

    def test_timestamp_output_requires_directory_notation(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root / "default.dirpluck", '''
                    [always.x]
                    path = "x"
                    description = "X."
                    may = ["a"]
                    [output.timestamp]
                    path = "artifacts"
                '''))
            config = load_config(self._write(root / "ok.dirpluck", '''
                [always.x]
                path = "x"
                description = "X."
                may = ["a"]
                [output.timestamp]
                path = "artifacts/"
                prefix = "project"
                suffix = "review"
            '''))
            self.assertTrue(config.output.timestamp)
            self.assertEqual(config.output.path, "artifacts")

    def test_default_scope_always_exists_and_empty_scope_is_noop(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            explicit_empty = load_config(self._write(root / "with.dirpluck", '''
                [pluck]
                description = "P."
                may = ["x"]
                [scope]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            '''))
            named_only = load_config(self._write(root / "named.dirpluck", '''
                [pluck]
                description = "P."
                may = ["x"]
                [scope.work]
                path = "work"
                [output]
                path = "out2.zip"
            '''))
            no_scope_table = load_config(self._write(root / "none.dirpluck", '''
                [pluck]
                description = "P."
                may = ["x"]
                [output]
                path = "out3.zip"
            '''))
            for config in (explicit_empty, named_only, no_scope_table):
                self.assertIn(None, config.scopes)
                self.assertEqual(config.scopes[None].ignore, ())
            self.assertIn("work", named_only.scopes)

    def test_scope_text_inside_multiline_string_has_no_special_meaning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(self._write(root / "default.dirpluck", '''
                [about]
                description = """
                [scope]
                """
                [pluck]
                description = "P."
                may = ["x"]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            '''))
            self.assertIn(None, config.scopes)
            self.assertEqual(config.scopes[None].ignore, ())
            self.assertIn("work", config.scopes)


class NewBuilderSemanticsTests(unittest.TestCase):
    def _write(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def _project(self, root: Path, name: str, filename: str = "file.txt") -> Path:
        project = root / name
        project.mkdir(parents=True, exist_ok=True)
        (project / filename).write_text(name, encoding="utf-8")
        return project

    def test_target_reference_four_forms(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "one")
            self._project(root, "two")
            work = root / "work"
            self._project(work, "three")
            self._project(work, "four")
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            '''))
            self.assertEqual(resolve_sources(config, BuildRequest.create("./one/"))[0].archive_root, "one")
            self.assertEqual(resolve_sources(config, BuildRequest.create("work/three/"))[0].archive_root, "three")
            self.assertEqual({s.archive_root for s in resolve_sources(config, BuildRequest.create("/"))}, {"one", "two", "work"})
            self.assertEqual({s.archive_root for s in resolve_sources(config, BuildRequest.create("work/"))}, {"three", "four"})

    def test_scope_ignore_applies_to_single_and_expansion(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "keep")
            self._project(root, "archive")
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope]
                ignore = ["archive/"]
                [output]
                path = "out.zip"
            '''))
            with self.assertRaises(SelectionError):
                resolve_sources(config, BuildRequest.create("./archive/"))
            self.assertEqual([s.archive_root for s in resolve_sources(config, BuildRequest.create("/"))], ["keep"])

    def test_scope_name_is_not_part_of_archive_path(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            work = root / "work"
            self._project(work, "project")
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            '''))
            plan = plan_archive(config, BuildRequest.create("work/project/"))
            self.assertIn("project/file.txt", plan.entries)
            self.assertNotIn("work/project/file.txt", plan.entries)

    def test_scope_composition_shadows_by_name_and_does_not_rebase(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base_dir = root / "base"
            derived_dir = root / "derived"
            base_work = base_dir / "work"
            derived_work = derived_dir / "work"
            base_oss = base_dir / "oss"
            self._project(base_work, "base-target")
            self._project(derived_work, "derived-target")
            self._project(base_oss, "oss-target")
            self._write(base_dir / "base.dirpluck", '''
                [pluck]
                description = "Base pluck."
                must = ["file.txt"]
                [scope.work]
                path = "work"
                [scope.oss]
                path = "oss"
                [output]
                path = "base-out.zip"
            ''')
            config = load_config(self._write(derived_dir / "default.dirpluck", '''
                [about]
                base = "../base/base.dirpluck"
                [scope.work]
                path = "work"
                [output]
                path = "derived-out.zip"
            '''))
            self.assertEqual(resolve_sources(config, BuildRequest.create("work/derived-target/"))[0].directory, derived_work / "derived-target")
            self.assertEqual(resolve_sources(config, BuildRequest.create("oss/oss-target/"))[0].directory, base_oss / "oss-target")
            with self.assertRaises(SelectionError):
                resolve_sources(config, BuildRequest.create("work/base-target/"))

    def test_unused_missing_named_scope_does_not_fail_default_scope_run(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope.external]
                path = "missing-mount"
                [output]
                path = "out.zip"
            '''))
            source = resolve_sources(config, BuildRequest.create("./project/"))[0]
            self.assertEqual(source.directory, root / "project")
            with self.assertRaisesRegex(SelectionError, "Scope 'external' root does not exist"):
                resolve_sources(config, BuildRequest.create("external/project/"))

    def test_default_scope_uses_configuration_directory_even_when_named_dot_dirpluck(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            dot_dir = root / ".dirpluck"
            self._project(dot_dir, "project")
            config = load_config(self._write(dot_dir / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [output]
                path = "out.zip"
            '''))
            source = resolve_sources(config, BuildRequest.create("./project/"))[0]
            self.assertEqual(source.directory, dot_dir / "project")

    def test_dot_dirpluck_name_has_no_special_scope_semantics(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            dot_dir = root / ".dirpluck"
            self._project(dot_dir, "default-project")
            self._project(dot_dir / "work", "named-project")
            config = load_config(self._write(dot_dir / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            '''))
            default_source = resolve_sources(config, BuildRequest.create("./default-project/"))[0]
            named_source = resolve_sources(config, BuildRequest.create("work/named-project/"))[0]
            self.assertEqual(default_source.directory, dot_dir / "default-project")
            self.assertEqual(named_source.directory, dot_dir / "work" / "named-project")

    def test_default_scope_belongs_to_root_configuration_and_does_not_inherit(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base_dir = root / "base"
            derived_dir = root / "derived"
            self._project(base_dir, "base-target")
            self._project(base_dir, "ignored")
            self._project(derived_dir, "derived-target")
            self._project(derived_dir, "ignored")
            base_path = self._write(base_dir / "base.dirpluck", """
                [namespace.base]
                [pluck]
                description = "Base."
                must = ["file.txt"]
                [scope]
                ignore = ["ignored"]
                namespace = "base"
                [output]
                path = "base.zip"
            """)
            base_config = load_config(base_path)
            base_source = resolve_sources(base_config, BuildRequest.create("./base-target/"))[0]
            self.assertEqual(base_source.archive_root, "base/base-target")

            config = load_config(self._write(derived_dir / "default.dirpluck", """
                [about]
                base = "../base/base.dirpluck"
                [output]
                path = "derived.zip"
            """))
            derived_source = resolve_sources(config, BuildRequest.create("./derived-target/"))[0]
            self.assertEqual(derived_source.directory, derived_dir / "derived-target")
            self.assertEqual(derived_source.archive_root, "derived-target")
            with self.assertRaises(SelectionError):
                resolve_sources(config, BuildRequest.create("./base-target/"))
            # Base [scope].ignore / namespace are root-local and do not move outward.
            ignored_source = resolve_sources(config, BuildRequest.create("./ignored/"))[0]
            self.assertEqual(ignored_source.directory, derived_dir / "ignored")
            self.assertEqual(ignored_source.archive_root, "ignored")

    def test_named_scope_cannot_duplicate_default_scope_root(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope.local]
                path = "."
                [output]
                path = "out.zip"
            '''))
            with self.assertRaisesRegex(ConfigurationError, "Scope roots must be distinct"):
                resolve_sources(config, BuildRequest.create("./project/"))

    def test_duplicate_effective_scope_roots_are_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "work").mkdir()
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                may = ["x"]
                [scope.local]
                path = "work"
                [scope.other]
                path = "./work"
                [output]
                path = "out.zip"
            '''))
            with self.assertRaisesRegex(ConfigurationError, "Scope roots must be distinct"):
                resolve_sources(config, BuildRequest.create("local/x/"))

    def test_outer_shared_definition_rebinds_inner_selection(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            project = base / "project"
            project.mkdir(parents=True)
            (project / "outer.txt").write_text("outer", encoding="utf-8")
            self._write(base / "base.dirpluck", '''
                [shared.must]
                chosen = ["inner.txt"]
                [pluck]
                description = "P."
                must = [{ shared = "chosen" }]
                [scope.base]
                path = "."
                [output]
                path = "base.zip"
            ''')
            config = load_config(self._write(derived / "default.dirpluck", '''
                [about]
                base = "../base/base.dirpluck"
                [shared.must]
                chosen = ["outer.txt"]
                [output]
                path = "derived.zip"
            '''))
            plan = plan_archive(config, BuildRequest.create("base/project/"))
            self.assertIn("project/outer.txt", plan.entries)

    def test_symlinked_root_configuration_uses_link_location_for_default_scope(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "project"
            shared = root / "shared"
            project.mkdir()
            shared.mkdir()
            target = project / "app"
            target.mkdir()
            (target / "file.txt").write_text("project", encoding="utf-8")
            real = self._write(shared / "root-real.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope]
                [output]
                path = "out.zip"
            ''')
            link = project / "default.dirpluck"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            config = load_config(link)
            self.assertEqual(config.manifest, link.absolute())
            sources = resolve_sources(config, BuildRequest.create("./app/"))
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, target.resolve())

    def test_base_cycle_detects_same_file_through_symbolic_link_aliases(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            shared.mkdir()
            real = self._write(shared / "real.dirpluck", '''
                [about]
                base = "again.dirpluck"
                [output]
                path = "real.zip"
            ''')
            first = root / "first.dirpluck"
            again = root / "again.dirpluck"
            try:
                first.symlink_to(real)
                again.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            config = load_config(first)
            with self.assertRaisesRegex(ConfigurationError, "base cycle"):
                plan_archive(config, BuildRequest.create())

    def test_base_cycle_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._write(root / "a.dirpluck", '''
                [about]
                base = "b.dirpluck"
                [output]
                path = "a.zip"
            ''')
            self._write(root / "b.dirpluck", '''
                [about]
                base = "a.dirpluck"
                [output]
                path = "b.zip"
            ''')
            config = load_config(root / "a.dirpluck")
            with self.assertRaisesRegex(ConfigurationError, "base cycle"):
                plan_archive(config, BuildRequest.create())

    def test_base_chain_has_no_fixed_depth_limit(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            depth = 12
            for i in range(depth):
                if i + 1 < depth:
                    body = f'''[about]\nbase = "{i+1}.dirpluck"\n\n[output]\npath = "out-{i}.zip"\n'''
                else:
                    body = f'''[always.data]\npath = "data"\ndescription = "Data."\nmust = ["x.txt"]\n\n[output]\npath = "out-{i}.zip"\n'''
                self._write(root / f"{i}.dirpluck", body)
            (root / "data").mkdir()
            (root / "data" / "x.txt").write_text("x", encoding="utf-8")
            sources = resolve_sources(load_config(root / "0.dirpluck"), BuildRequest.create())
            self.assertEqual(len(sources), 1)

    def test_relative_always_path_uses_declaring_configuration_directory(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            (base / "refs").mkdir(parents=True)
            (base / "refs" / "note.txt").write_text("base", encoding="utf-8")
            self._write(base / "base.dirpluck", '''
                [always.refs]
                path = "refs"
                description = "Refs."
                must = ["note.txt"]
                [output]
                path = "base.zip"
            ''')
            config = load_config(self._write(derived / "default.dirpluck", '''
                [about]
                base = "../base/base.dirpluck"
                [output]
                path = "derived.zip"
            '''))
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.directory, base / "refs")

    def test_output_fixed_paths_in_same_directory_do_not_conflict(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(root / "base.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
                [output]
                path = "out/base.zip"
            ''')
            config = load_config(self._write(root / "derived.dirpluck", '''
                [about]
                base = "base.dirpluck"
                [output]
                path = "out/derived.zip"
            '''))
            self.assertEqual(len(resolve_sources(config, BuildRequest.create())), 1)

    def test_output_same_fixed_file_conflicts_across_base_chain(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(root / "base.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
                [output]
                path = "out/result.zip"
            ''')
            config = load_config(self._write(root / "derived.dirpluck", '''
                [about]
                base = "base.dirpluck"
                [output]
                path = "out/result.zip"
            '''))
            with self.assertRaisesRegex(ConfigurationError, "write boundaries overlap"):
                resolve_sources(config, BuildRequest.create())

    def test_timestamp_boundary_conflicts_with_descendant_timestamp_and_fixed_file(self):
        cases = (
            '''[output.timestamp]\npath = "artifacts/release/"''',
            '''[output]\npath = "artifacts/result.zip"''',
        )
        for derived_output in cases:
            with self.subTest(derived_output=derived_output), resolved_temporary_directory() as temp:
                root = Path(temp)
                (root / "data").mkdir()
                (root / "data" / "x").write_text("x")
                self._write(root / "base.dirpluck", '''
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                    [output.timestamp]
                    path = "artifacts/"
                ''')
                config = load_config(self._write(root / "derived.dirpluck", f'''
                    [about]
                    base = "base.dirpluck"
                    {derived_output}
                '''))
                with self.assertRaisesRegex(ConfigurationError, "write boundaries overlap"):
                    resolve_sources(config, BuildRequest.create())

    def test_root_output_only_is_executed_and_is_anchored_to_root_configuration(self):
        with resolved_temporary_directory() as temp:
            workspace = Path(temp)
            base = workspace / "base"
            derived = workspace / "derived"
            elsewhere = workspace / "elsewhere"
            elsewhere.mkdir()
            (base / "data").mkdir(parents=True)
            (base / "data" / "x").write_text("x")
            self._write(base / "base.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
                [output]
                path = "base-output/base.zip"
            ''')
            config = load_config(self._write(derived / "default.dirpluck", '''
                [about]
                base = "../base/base.dirpluck"
                [output]
                path = "result/output.zip"
            '''))
            previous = Path.cwd()
            try:
                os.chdir(elsewhere)
                output = build_archive(config, BuildRequest.create())
            finally:
                os.chdir(previous)
            self.assertEqual(output, (derived / "result" / "output.zip").resolve())
            self.assertFalse((base / "base-output" / "base.zip").exists())

    def test_timestamp_output_uses_root_configuration_directory_and_sequence(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            config = load_config(self._write(root / "default.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
                [output.timestamp]
                path = "snapshots/"
                prefix = "project"
                suffix = "review"
            '''))
            with patch("dirpluck._output._current_output_timestamp", return_value="20260920-120000"):
                output = build_archive(config, BuildRequest.create(sequence=3))
            self.assertEqual(output, (root / "snapshots/project-20260920-120000-3-review.zip").resolve())

    def test_pluck_uses_default_scope_without_scope_table(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            config = load_config(self._write(root / "default.dirpluck", '''
                [pluck]
                description = "P."
                must = ["file.txt"]
                [output]
                path = "out.zip"
            '''))
            source = resolve_sources(config, BuildRequest.create("./project/"))[0]
            self.assertEqual(source.directory, root / "project")

    def test_source_less_effective_configuration_is_rejected(self):
        with resolved_temporary_directory() as temp:
            config = load_config(self._write(Path(temp) / "default.dirpluck", '''
                [output]
                path = "out.zip"
            '''))
            with self.assertRaisesRegex(ConfigurationError, "no Pluck or Always source"):
                resolve_sources(config, BuildRequest.create())

    def test_allow_empty_true_preserves_empty_source_directory_entry(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            config = load_config(self._write(root / "default.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                may = ["missing.txt"]
                allow_empty = true
                [output]
                path = "out.zip"
            '''))
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                self.assertIn("data/", archive.namelist())

    def test_base_configuration_may_omit_output(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(root / "base.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
            ''')
            config = load_config(self._write(root / "default.dirpluck", '''
                [about]
                base = "base.dirpluck"

                [output]
                path = "out.zip"
            '''))
            output = build_archive(config, BuildRequest.create())
            with zipfile.ZipFile(output) as archive:
                self.assertIn("data/x", archive.namelist())

    def test_root_configuration_without_output_can_be_planned_but_not_built(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(root / "base.dirpluck", """
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]

                [output]
                path = "base.zip"
            """)
            config = load_config(self._write(root / "default.dirpluck", """
                [about]
                base = "base.dirpluck"
            """))
            self.assertIsNone(config.output)
            plan = plan_archive(config, BuildRequest.create())
            self.assertEqual(tuple(plan.entries), ("data/x",))
            with self.assertRaisesRegex(ConfigurationError, "root Configuration must define"):
                build_archive(config, BuildRequest.create())
            self.assertFalse((root / "base.zip").exists())

    def test_outputless_base_does_not_create_a_write_boundary(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(root / "base.dirpluck", '''
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
            ''')
            config = load_config(self._write(root / "default.dirpluck", '''
                [about]
                base = "base.dirpluck"

                [output.timestamp]
                path = "artifacts/"
            '''))
            with patch("dirpluck._output._current_output_timestamp", return_value="20260920-120000"):
                output = build_archive(config, BuildRequest.create())
            self.assertEqual(output, (root / "artifacts/20260920-120000.zip").resolve())


if __name__ == "__main__":
    unittest.main()
