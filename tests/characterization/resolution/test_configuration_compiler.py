from pathlib import Path
import textwrap
import unittest
from unittest.mock import patch

from tests._temp import resolved_temporary_directory
from tests._pipeline import build_archive, resolve_sources

from dirpluck.builder import plan_archive
from dirpluck._request_models import BuildRequest
from dirpluck._config_parser import load_config
from dirpluck.errors import ConfigurationError, SelectionError


class ConfigurationCompilerTests(unittest.TestCase):
    def _write(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def _project(self, root: Path, name: str, filename: str = "file.txt") -> Path:
        project = root / name
        project.mkdir(parents=True, exist_ok=True)
        (project / filename).write_text(name, encoding="utf-8")
        return project

    def test_outer_shared_namespace_can_supply_inner_reference(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            project = base / "project"
            project.mkdir(parents=True)
            (project / "outer.txt").write_text("outer", encoding="utf-8")
            self._write(
                base / "base.dirpluck",
                """
                [pluck]
                description = "P."
                must = [{ shared = "provided" }]
                [scope.base]
                path = "."
                [output]
                path = "base.zip"
            """,
            )
            config = load_config(
                self._write(
                    derived / "default.dirpluck",
                    """
                [about]
                base = "../base/base.dirpluck"
                [shared.must]
                provided = ["outer.txt"]
                [output]
                path = "derived.zip"
            """,
                )
            )
            plan = plan_archive(config, BuildRequest.create("base/project/"))
            self.assertEqual(tuple(plan.entries), ("project/outer.txt",))

    def test_unresolved_shared_reference_is_rejected_after_composition(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [pluck]
                description = "P."
                must = [{ shared = "missing" }]
                [scope]
                [output]
                path = "out.zip"
            """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "unknown Shared pattern set"):
                resolve_sources(config, BuildRequest.create("./project/"))

    def test_shared_expansion_rejects_duplicate_effective_patterns(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [shared.must]
                core = ["file.txt"]
                [pluck]
                description = "P."
                must = ["file.txt", { shared = "core" }]
                [scope]
                [output]
                path = "out.zip"
            """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "duplicate effective pattern"):
                resolve_sources(config, BuildRequest.create("./project/"))

    def test_only_four_target_reference_forms_are_accepted(self):
        invalid = ("./", "/project", "work/project/extra", "work//project", "C:/project")
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            work = root / "work"
            self._project(work, "project")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            """,
                )
            )
            for reference in invalid:
                with self.subTest(reference=reference), self.assertRaises(SelectionError):
                    resolve_sources(config, BuildRequest.create(reference))

    def test_scope_expansion_errors_when_every_candidate_is_ignored(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "tmp-one")
            self._project(root, "tmp-two")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope]
                ignore = ["tmp-*/"]
                [output]
                path = "out.zip"
            """,
                )
            )
            with self.assertRaisesRegex(SelectionError, "no eligible direct child directories"):
                resolve_sources(config, BuildRequest.create("/"))

    def test_namespace_reference_is_resolved_from_effective_base_chain(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            self._write(
                root / "base.dirpluck",
                """
                [namespace.base]
                [pluck]
                description = "P."
                must = ["file.txt"]
            """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                base = "base.dirpluck"
                [scope]
                namespace = "base"
                [output]
                path = "out.zip"
            """,
                )
            )
            source = resolve_sources(config, BuildRequest.create("./project/"))[0]
            self.assertEqual(source.archive_root, "base/project")
            self.assertEqual(source.directory.name, "project")
            self.assertEqual(source.archive_root, "base/project")

    def test_unknown_effective_namespace_reference_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "project")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope]
                namespace = "missing"
                [output]
                path = "out.zip"
            """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "unknown Namespace 'missing'"):
                resolve_sources(config, BuildRequest.create("./project/"))

    def test_namespace_names_must_be_unique_ignoring_case_after_composition(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._write(
                root / "base.dirpluck",
                """
                [namespace.Docs]
                """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"

                    [namespace.docs]

                    [always.content]
                    path = "."
                    may = ["*.md"]
                    allow_empty = true
                    """,
                )
            )
            with self.assertRaisesRegex(
                ConfigurationError,
                "effective Namespace names must be distinct ignoring case",
            ):
                resolve_sources(config, BuildRequest.create())

    def test_namespaces_keep_same_named_targets_from_different_scopes_distinct(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "docs")
            work = root / "work"
            self._project(work, "docs")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [namespace.local]
                [namespace.work]

                [pluck]
                description = "P."
                must = ["file.txt"]

                [scope]
                namespace = "local"

                [scope.work]
                path = "work"
                namespace = "work"

                [output]
                path = "out.zip"
            """,
                )
            )
            sources = resolve_sources(config, BuildRequest.create("./docs/", "work/docs/"))
            self.assertEqual(
                {source.archive_root for source in sources},
                {"local/docs", "work/docs"},
            )

    def test_same_named_targets_from_different_scopes_collide_without_namespace(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "docs")
            work = root / "work"
            self._project(work, "docs")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            """,
                )
            )
            with self.assertRaisesRegex(
                SelectionError,
                "resolved sources must have distinct archive roots",
            ):
                resolve_sources(config, BuildRequest.create("./docs/", "work/docs/"))

    def test_target_archive_roots_must_be_unique_ignoring_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._project(root, "Docs")
            work = root / "work"
            self._project(work, "docs")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [pluck]
                description = "P."
                must = ["file.txt"]
                [scope.work]
                path = "work"
                [output]
                path = "out.zip"
            """,
                )
            )
            with self.assertRaisesRegex(
                SelectionError,
                "resolved sources have archive roots that differ only by case",
            ):
                resolve_sources(config, BuildRequest.create("./Docs/", "work/docs/"))

    def test_fixed_output_rejects_dot_or_dotdot_as_final_component(self):
        invalid = ("..", "artifacts/..", "artifacts/.")
        for path in invalid:
            with self.subTest(path=path), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaisesRegex(ConfigurationError, "must name a file"):
                    load_config(
                        self._write(
                            root / "default.dirpluck",
                            f'''
                        [always.data]
                        path = "data"
                        description = "D."
                        may = ["x"]
                        [output]
                        path = "{path}"
                    ''',
                        )
                    )

    def test_timestamp_output_without_sequence_uses_plain_generated_name(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
                [output.timestamp]
                path = "snapshots/"
            """,
                )
            )
            with patch(
                "dirpluck._output._current_output_timestamp", return_value="20260920-120000"
            ):
                output = build_archive(config, BuildRequest.create())
            self.assertEqual(output, (root / "snapshots/20260920-120000.zip").resolve())

    def test_timestamp_output_does_not_overwrite_existing_generated_name(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            snapshots = root / "snapshots"
            snapshots.mkdir()
            existing = snapshots / "20260920-120000.zip"
            existing.write_bytes(b"existing")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [always.data]
                path = "data"
                description = "D."
                must = ["x"]
                [output.timestamp]
                path = "snapshots/"
            """,
                )
            )
            with patch(
                "dirpluck._output._current_output_timestamp", return_value="20260920-120000"
            ):
                with self.assertRaisesRegex(SelectionError, "already exists"):
                    build_archive(config, BuildRequest.create())

    def test_output_file_cannot_be_selected_as_input(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            data = root / "data"
            data.mkdir()
            (data / "result.zip").write_text("input", encoding="utf-8")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [always.data]
                path = "data"
                description = "D."
                must = ["result.zip"]
                [output]
                path = "data/result.zip"
                overwrite = true
            """,
                )
            )
            with self.assertRaisesRegex(SelectionError, "selected as an input file"):
                build_archive(config, BuildRequest.create())

    def test_base_configuration_allows_symbolic_link_and_uses_link_location(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            shared.mkdir()
            (root / "data").mkdir()
            (root / "data" / "x.txt").write_text("root", encoding="utf-8")
            (shared / "data").mkdir()
            (shared / "data" / "x.txt").write_text("shared", encoding="utf-8")
            real = self._write(
                shared / "base-real.dirpluck",
                """
                [always.data]
                path = "data"
                description = "D."
                must = ["x.txt"]
                [output]
                path = "shared.zip"
            """,
            )
            link = root / "base.dirpluck"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                base = "base.dirpluck"
                [output]
                path = "derived.zip"
            """,
                )
            )
            sources = resolve_sources(config, BuildRequest.create())
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].directory, (root / "data").resolve())

    def test_invalid_base_schema_is_rejected_when_chain_is_resolved(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._write(
                root / "base.dirpluck",
                """
                [always.data]
                path = "data"
                description = "D."
                may = ["x"]
                [output]
                path = "legacy.zip"
                prefix = "not-valid-for-fixed"
            """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                base = "base.dirpluck"
                [output]
                path = "derived.zip"
            """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "base Configuration is invalid"):
                resolve_sources(config, BuildRequest.create())

    def test_always_case_selection_is_shadowed_by_name_across_base_composition(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            (base / "a").mkdir(parents=True)
            (base / "a" / "a.txt").write_text("a", encoding="utf-8")
            (base / "b").mkdir()
            (base / "b" / "b.txt").write_text("b", encoding="utf-8")
            self._write(
                base / "base.dirpluck",
                """
                [always.a]
                path = "a"
                must = ["a.txt"]
                [always.b]
                path = "b"
                must = ["b.txt"]
                [case.always.pick]
                include = ["a"]
            """,
            )
            config = load_config(
                self._write(
                    derived / "default.dirpluck",
                    """
                [about]
                base = "../base/base.dirpluck"
                [case.always.pick]
                include = ["b"]
            """,
                )
            )
            sources = resolve_sources(config, BuildRequest.create(case=".pick"))
            self.assertEqual([source.archive_root for source in sources], ["b"])

    def test_case_selection_uses_effective_outer_pluck_after_base_composition(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            base = root / "base"
            derived = root / "derived"
            project = derived / "project"
            project.mkdir(parents=True)
            (project / "outer.txt").write_text("outer", encoding="utf-8")
            self._write(
                base / "base.dirpluck",
                """
                [case.pluck.audit]
                description = "Base audit."
                must = ["base.txt"]
                [scope]
                [output]
                path = "base.zip"
            """,
            )
            config = load_config(
                self._write(
                    derived / "default.dirpluck",
                    """
                [about]
                base = "../base/base.dirpluck"
                [case.pluck.audit]
                description = "Outer audit."
                must = ["outer.txt"]
                [scope]
                [output]
                path = "derived.zip"
            """,
                )
            )
            plan = plan_archive(config, BuildRequest.create("./project/", case="audit"))
            self.assertIn("project/outer.txt", plan.entries)
            self.assertIn("Outer audit.", plan.readme)

    def test_layout_reference_can_be_satisfied_by_base_configuration(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            self._write(
                root / "base.dirpluck",
                """
                [layout.dependencies]
                description = "Dependencies."
                """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                base = "base.dirpluck"
                always_layout = "dependencies"

                [always.docs]
                path = "docs"
                must = ["guide.md"]

                [output]
                path = "out.zip"
                """,
                )
            )
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.archive_root, "dependencies/docs")
            self.assertEqual(source.layout_name, "dependencies")

    def test_unknown_layout_references_are_rejected_after_composition(self):
        bodies = (
            """
            [about]
            always_layout = "missing"
            """,
            """
            [scope]
            layout = "missing"
            """,
            """
            [always.docs]
            path = "docs"
            layout = "missing"
            may = ["*.md"]
            allow_empty = true
            """,
        )
        for body in bodies:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                root = Path(temp)
                config = load_config(
                    self._write(
                        root / "default.dirpluck",
                        body + "\n[output]\npath = 'out.zip'\n",
                    )
                )
                with self.assertRaisesRegex(ConfigurationError, "unknown Layout 'missing'"):
                    resolve_sources(config, BuildRequest.create())

    def test_individual_layout_overrides_general_layout(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for directory in ("a", "b"):
                source = root / directory
                source.mkdir()
                (source / "file.txt").write_text(directory, encoding="utf-8")
            work = root / "work"
            self._project(work, "one")
            self._project(work, "two")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                always_layout = "dependencies"
                targets_layout = "targets"

                [layout.dependencies]
                [layout.targets]
                [layout.special]

                [pluck]
                must = ["file.txt"]

                [always.a]
                path = "a"
                must = ["file.txt"]
                layout = "special"

                [always.b]
                path = "b"
                must = ["file.txt"]

                [scope.work]
                path = "work"
                layout = "special"

                [output]
                path = "out.zip"
                """,
                )
            )
            sources = resolve_sources(config, BuildRequest.create("work/one/", "work/two/"))
            roots = {source.archive_root for source in sources}
            self.assertEqual(roots, {"special/one", "special/two", "special/a", "dependencies/b"})

    def test_layout_and_namespace_cannot_be_effective_on_the_same_scope(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                targets_layout = "targets"

                [layout.targets]
                [namespace.legacy]

                [scope]
                namespace = "legacy"

                [output]
                path = "out.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "cannot use both Namespace"):
                resolve_sources(config, BuildRequest.create())

    def test_always_layout_and_compatibility_namespace_cannot_be_effective_together(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                always_layout = "dependencies"

                [layout.dependencies]
                [namespace.legacy]

                [always.docs]
                path = "docs"
                namespace = "legacy"
                may = ["*.md"]
                allow_empty = true

                [output]
                path = "out.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "cannot use both Namespace"):
                resolve_sources(config, BuildRequest.create())

    def test_about_default_layout_is_inherited_field_by_field_from_base(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("guide", encoding="utf-8")
            self._write(
                root / "base.dirpluck",
                """
                [about]
                always_layout = "dependencies"

                [layout.dependencies]
                """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                base = "base.dirpluck"
                description = "Outer description."

                [always.docs]
                path = "docs"
                must = ["guide.md"]

                [output]
                path = "out.zip"
                """,
                )
            )
            source = resolve_sources(config, BuildRequest.create())[0]
            self.assertEqual(source.archive_root, "dependencies/docs")

    def test_layout_names_must_be_unique_ignoring_case_after_composition(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            self._write(
                root / "base.dirpluck",
                """
                [layout.Docs]
                """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                [about]
                base = "base.dirpluck"

                [layout.docs]

                [output]
                path = "out.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "effective Layout names"):
                resolve_sources(config, BuildRequest.create())


if __name__ == "__main__":
    unittest.main()
