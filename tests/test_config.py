from pathlib import Path
import tempfile
import textwrap
from types import MappingProxyType
import unittest

from dirpluck.config import load_config
from dirpluck.errors import ConfigurationError


OUTPUT = '''
[output]
path = "out.zip"
if_exists = "error"
'''


class ConfigTests(unittest.TestCase):
    def _write(self, root: Path, text: str, *, add_output: bool = True) -> Path:
        body = textwrap.dedent(text)
        if add_output and "[output]" not in body:
            body += textwrap.dedent(OUTPUT)
        path = root / "dirpluck.toml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_loads_default_target_cases_companions_and_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default development target."
                include_if_exists = ["src", "tests"]
                exclude = ["__pycache__/", "*.pyc"]
                if_empty = "allow"

                [target.case.review]
                description = "Review target."
                include = ["src", "README.md"]

                [companion.shikumi]
                path = "shikumi"
                description = "Foundation wheel."
                include = ["dist/shikumi-*.whl"]
            '''))
            self.assertEqual(config.target.default.description, "Default development target.")
            self.assertEqual(config.target.default.include_if_exists, ("src", "tests"))
            self.assertEqual(config.target.default.if_empty, "allow")
            self.assertEqual(config.target.cases["review"].include, ("src", "README.md"))
            self.assertEqual(config.companions["shikumi"].path, "shikumi")
            self.assertEqual(
                config.companions["shikumi"].selection.include,
                ("dist/shikumi-*.whl",),
            )
            self.assertEqual(dict(config.companions["shikumi"].cases), {})
            self.assertEqual(config.output.path, "out.zip")
            self.assertEqual(config.output.if_exists, "error")


    def test_shared_patterns_expand_into_target_case_and_companion_selections(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [shared.include_patterns]
                core = ["src", "README.md"]
                optional = ["docs", "examples"]

                [shared.exclude_patterns]
                python-dev = ["__pycache__/", "*.pyc"]

                [target]
                description = "Default."
                include_pattern_refs = ["core"]
                exclude_pattern_refs = ["python-dev"]

                [target.case.all]
                description = "All."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["python-dev"]
                if_empty = "allow"

                [companion.framework]
                path = "framework"
                description = "Framework."
                include_if_exists_pattern_refs = ["optional"]
                exclude_pattern_refs = ["python-dev"]
                if_empty = "allow"
            '''))
            self.assertEqual(config.shared.include["core"], ("src", "README.md"))
            self.assertEqual(
                tuple(pattern.raw for pattern in config.shared.exclude["python-dev"]),
                ("__pycache__/", "*.pyc"),
            )
            self.assertEqual(config.target.default.include, ("src", "README.md"))
            self.assertEqual(
                tuple(pattern.raw for pattern in config.target.default.exclude),
                ("__pycache__/", "*.pyc"),
            )
            self.assertEqual(config.target.cases["all"].include_if_exists, ("*",))
            self.assertEqual(
                config.companions["framework"].selection.include_if_exists,
                ("docs", "examples"),
            )

    def test_shared_include_patterns_can_be_required_or_optional_per_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [shared.include_patterns]
                common = ["src", "README.md"]

                [target]
                description = "Required."
                include_pattern_refs = ["common"]

                [target.case.optional]
                description = "Optional."
                include_if_exists_pattern_refs = ["common"]
                if_empty = "allow"
            '''))
            self.assertEqual(config.target.default.include, ("src", "README.md"))
            self.assertEqual(
                config.target.cases["optional"].include_if_exists,
                ("src", "README.md"),
            )

    def test_shared_and_local_patterns_are_combined_in_declared_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [shared.include_patterns]
                first = ["src"]
                second = ["tests"]

                [shared.exclude_patterns]
                cache = ["__pycache__/"]
                compiled = ["*.pyc"]

                [target]
                description = "Combined."
                include_pattern_refs = ["first", "second"]
                include = ["README.md"]
                exclude_pattern_refs = ["cache", "compiled"]
                exclude = [".DS_Store"]
            '''))
            self.assertEqual(config.target.default.include, ("src", "tests", "README.md"))
            self.assertEqual(
                tuple(pattern.raw for pattern in config.target.default.exclude),
                ("__pycache__/", "*.pyc", ".DS_Store"),
            )

    def test_shared_pattern_references_are_not_inherited_by_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [shared.exclude_patterns]
                python-dev = ["__pycache__/", "*.pyc"]

                [target]
                description = "Default."
                include = ["src"]
                exclude_pattern_refs = ["python-dev"]

                [target.case.review]
                description = "Review."
                include = ["tests"]
            '''))
            self.assertEqual(
                tuple(pattern.raw for pattern in config.target.default.exclude),
                ("__pycache__/", "*.pyc"),
            )
            self.assertEqual(config.target.cases["review"].exclude, ())

    def test_shared_pattern_reference_may_be_resolved_by_an_outer_layer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, """
                [target]
                description = "Default."
                include_pattern_refs = ["provided-later"]
            """))
            self.assertEqual(
                config.target.default.include_pattern_refs,
                ("provided-later",),
            )
            self.assertEqual(config.target.default.include, ())

    def test_shared_include_and_exclude_patterns_use_their_own_grammars(self):
        invalid = (
            ("include_patterns", "bad", "src/**/x.py"),
            ("exclude_patterns", "bad", "src/generated/"),
        )
        for table, name, pattern in invalid:
            with self.subTest(table=table), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [shared.{table}]
                    {name} = [{pattern!r}]

                    [target]
                    description = "Default."
                    include = ["src"]
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_shared_pattern_sets_must_be_non_empty_arrays(self):
        for table in ("include_patterns", "exclude_patterns"):
            with self.subTest(table=table), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [shared.{table}]
                    empty = []

                    [target]
                    description = "Default."
                    include = ["src"]
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_shared_and_direct_duplicate_checks_are_deferred_to_effective_resolution(self):
        cases = (
            """
                [shared.include_patterns]
                common = ["src"]
                [target]
                description = "Default."
                include_pattern_refs = ["common"]
                include = ["src"]
            """,
            """
                [shared.exclude_patterns]
                common = ["*.pyc"]
                [target]
                description = "Default."
                include = ["src"]
                exclude_pattern_refs = ["common"]
                exclude = ["*.pyc"]
            """,
        )
        for body in cases:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                config = load_config(self._write(root, body))
                self.assertIsNotNone(config.target)

    def test_if_empty_allow_rejects_required_shared_include_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [shared.include_patterns]
                required = ["src"]

                [target]
                description = "Default."
                include_pattern_refs = ["required"]
                if_empty = "allow"
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_unknown_shared_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [shared]
                filters = ["python"]

                [target]
                description = "Default."
                include = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_target_only_default_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
            '''))
            self.assertIsNotNone(config.target.default)
            self.assertEqual(dict(config.target.cases), {})

    def test_target_may_define_only_named_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target.case.review]
                description = "Review."
                include = ["src"]
            '''))
            self.assertIsNone(config.target.default)
            self.assertIn("review", config.target.cases)

    def test_case_name_may_equal_target_field_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target.case.description]
                description = "A case literally named description."
                include = ["src"]
            '''))
            self.assertIn("description", config.target.cases)

    def test_default_and_named_case_do_not_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                exclude = ["*.tmp"]

                [target.case.review]
                description = "Review."
                include = ["tests"]
            '''))
            self.assertEqual(config.target.default.include, ("src",))
            self.assertEqual(config.target.cases["review"].include, ("tests",))
            self.assertEqual(config.target.cases["review"].exclude, ())

    def test_source_less_configuration_parses_for_chain_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, "", add_output=True))
            self.assertIsNone(config.target)
            self.assertEqual(dict(config.companions), {})

    def test_companion_only_configuration_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [companion.documents]
                path = "documents"
                description = "Documents."
                include = ["*.pdf"]
            '''))
            self.assertIsNone(config.target)
            self.assertEqual(config.companions["documents"].path, "documents")

    def test_target_must_define_default_or_case(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root, "[target]\n"))

    def test_unknown_top_level_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root, '''
                    [target]
                    description = "Default."
                    include = ["src"]
                    [bundle.review]
                    description = "Old model"
                '''))

    def test_unknown_target_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root, '''
                    [target]
                    description = "Default."
                    include = ["src"]
                    path = "app"
                '''))

    def test_unknown_companion_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root, '''
                    [target]
                    description = "Default."
                    include = ["src"]
                    [companion.framework]
                    path = "framework"
                    description = "Framework."
                    include = ["src"]
                    case = "review"
                '''))

    def test_include_may_name_nested_concrete_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["dist/package.whl"]
            '''))
            self.assertEqual(config.target.default.include, ("dist/package.whl",))

    def test_include_allows_one_star_per_path_element(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["packages/*/dist/pkg-*.whl", "plugins/foo*bar"]
            '''))
            self.assertEqual(
                config.target.default.include,
                ("packages/*/dist/pkg-*.whl", "plugins/foo*bar"),
            )

    def test_include_rejects_recursive_or_richer_pattern_syntax(self):
        invalid = ["src/**/x.py", "foo*bar*baz", "src/?.py", "src/[ab].py", "!src"]
        for pattern in invalid:
            with self.subTest(pattern=pattern), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    include = [{pattern!r}]
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_include_if_exists_uses_include_pattern_syntax(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include_if_exists = ["packages/*/README.md"]
                if_empty = "allow"
            '''))
            self.assertEqual(
                config.target.default.include_if_exists,
                ("packages/*/README.md",),
            )

    def test_include_fields_reject_empty_arrays_when_specified(self):
        for field in ("include", "include_if_exists"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    {field} = []
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_include_if_exists_cannot_duplicate_required_include(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                include_if_exists = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_selection_requires_include_or_include_if_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                exclude = ["*.pyc"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_if_empty_allow_requires_optional_only_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include_if_exists = ["src"]
                if_empty = "allow"
            '''))
            self.assertEqual(config.target.default.if_empty, "allow")

    def test_if_empty_allow_rejects_required_include(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                if_empty = "allow"
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_if_empty_rejects_unknown_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include_if_exists = ["src"]
                if_empty = "ignore"
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_exclude_may_be_explicitly_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                exclude = []
            '''))
            self.assertEqual(config.target.default.exclude, ())

    def test_bare_target_case_table_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [target.case]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_exclude_must_be_an_array(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                exclude = "*.pyc"
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_exclude_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                exclude = ["src/generated/"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_exclude_middle_wildcard_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                exclude = ["foo*bar"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_exclude_unsupported_pattern_syntax_is_rejected(self):
        for pattern in ("**", "?.py", "[ab].py", "!keep.py"):
            with self.subTest(pattern=pattern), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    include = ["src"]
                    exclude = [{pattern!r}]
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_exclude_star_alone_is_rejected(self):
        for pattern in ("*", "*/"):
            with self.subTest(pattern=pattern), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    include = ["src"]
                    exclude = [{pattern!r}]
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_companion_path_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [companion.framework]
                description = "Framework."
                include = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_companion_fixed_path_cannot_escape_cwd(self):
        for path in ("..", "../framework", ".", "/tmp/framework"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    include = ["src"]
                    [companion.framework]
                    path = {path!r}
                    description = "Framework."
                    include = ["src"]
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_companion_fixed_path_must_be_concrete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [companion.framework]
                path = "framework*"
                description = "Framework."
                include = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_companion_owns_exactly_one_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [companion.framework]
                path = "framework"
                description = "Framework."
                include = ["src"]
                include_if_exists = ["README.md"]
            '''))
            selection = config.companions["framework"].selection
            self.assertEqual(selection.include, ("src",))
            self.assertEqual(selection.include_if_exists, ("README.md",))


    def test_companion_may_define_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]

                [target.case.review]
                description = "Review target."
                include = ["tests"]

                [companion.framework]
                path = "framework"
                description = "Default framework."
                include = ["src"]

                [companion.framework.case.review]
                description = "Framework for review."
                include = ["src", "tests"]
            '''))
            companion = config.companions["framework"]
            self.assertEqual(companion.selection.include, ("src",))
            self.assertEqual(companion.cases["review"].include, ("src", "tests"))

    def test_companion_case_compatibility_is_deferred_to_effective_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, """
                [target]
                description = "Default."
                include = ["src"]

                [target.case.review]
                description = "Review."
                include = ["tests"]

                [companion.framework]
                path = "framework"
                description = "Framework."
                include = ["src"]

                [companion.framework.case.release]
                description = "Release framework."
                include = ["dist"]
            """))
            self.assertIn("release", config.companions["framework"].cases)

    def test_companion_only_configuration_may_define_its_own_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [companion.documents]
                path = "documents"
                description = "Current documents."
                include = ["current"]

                [companion.documents.case.archive]
                description = "Archive documents."
                include = ["current", "history"]
            '''))
            self.assertIsNone(config.target)
            self.assertIn("archive", config.companions["documents"].cases)

    def test_case_hierarchy_is_rejected(self):
        for table in ("target.case.review.extra", "companion.framework.case.review.extra"):
            with self.subTest(table=table), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                if table.startswith("target"):
                    text = f"""
                        [{table}]
                        description = "Nested."
                        include = ["src"]
                    """
                else:
                    text = f"""
                        [companion.framework]
                        path = "framework"
                        description = "Framework."
                        include = ["src"]
                        [{table}]
                        description = "Nested."
                        include = ["tests"]
                    """
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(root, text))

    def test_companion_description_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [companion.framework]
                path = "framework"
                include = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_target_description_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                include = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_case_description_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target.case.review]
                include = ["src"]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_output_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
            ''', add_output=False)
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_output_requires_path_and_if_exists(self):
        for body in (
            '''
            [output]
            if_exists = "error"
            ''',
            '''
            [output]
            path = "out.zip"
            ''',
        ):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    include = ["src"]
                    {textwrap.dedent(body)}
                ''', add_output=False)
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_output_if_exists_is_limited(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [target]
                description = "Default."
                include = ["src"]
                [output]
                path = "out.zip"
                if_exists = "rename"
            ''', add_output=False)
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_generated_output_loads_timestamp_naming_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, """
                [target]
                description = "Default."
                include = ["src"]
                [output]
                directory = "snapshots"
                prefix = "project"
                timestamp = true
                suffix = "review"
            """, add_output=False))
            self.assertTrue(config.output.generated)
            self.assertIsNone(config.output.path)
            self.assertIsNone(config.output.if_exists)
            self.assertEqual(config.output.directory, "snapshots")
            self.assertEqual(config.output.prefix, "project")
            self.assertTrue(config.output.timestamp)
            self.assertEqual(config.output.suffix, "review")

    def test_fixed_and_generated_output_fields_cannot_be_combined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, """
                [target]
                description = "Default."
                include = ["src"]
                [output]
                path = "out.zip"
                if_exists = "error"
                directory = "snapshots"
                timestamp = true
            """, add_output=False)
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_generated_output_rejects_if_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, """
                [target]
                description = "Default."
                include = ["src"]
                [output]
                directory = "snapshots"
                timestamp = true
                if_exists = "error"
            """, add_output=False)
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_generated_output_requires_directory_and_timestamp_true(self):
        bodies = (
            """
            [output]
            timestamp = true
            """,
            """
            [output]
            directory = "snapshots"
            """,
            """
            [output]
            directory = "snapshots"
            timestamp = false
            """,
        )
        for body in bodies:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f"""
                    [target]
                    description = "Default."
                    include = ["src"]
                    {textwrap.dedent(body)}
                """, add_output=False)
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_generated_output_directory_and_fragments_are_concrete(self):
        bad_values = (
            ('directory', '../snapshots'),
            ('directory', '/tmp/snapshots'),
            ('directory', 'snap*shots'),
            ('prefix', 'group/name'),
            ('suffix', 'review?'),
            ('prefix', 'bad\nname'),
        )
        for field, value in bad_values:
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                extra = f'{field} = {value!r}\n'
                if field != 'directory':
                    extra = 'directory = "snapshots"\n' + extra
                manifest = self._write(root, f"""
                    [target]
                    description = "Default."
                    include = ["src"]
                    [output]
                    {extra}
                    timestamp = true
                """, add_output=False)
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_output_path_must_stay_below_cwd_and_be_concrete(self):
        for path in ("../out.zip", "/tmp/out.zip", "*.zip", "."):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [target]
                    description = "Default."
                    include = ["src"]
                    [output]
                    path = {path!r}
                    if_exists = "error"
                ''', add_output=False)
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)


    def test_root_configuration_may_contain_only_one_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, """
                [import.shikumi-stack]
                root = ".."
                configuration = "shikumi/dirpluck.toml"
            """))
            self.assertIsNone(config.target)
            self.assertEqual(dict(config.companions), {})
            imported = config.imports["shikumi-stack"]
            self.assertEqual(imported.root, "..")
            self.assertEqual(imported.configuration, "shikumi/dirpluck.toml")

    def test_configuration_may_not_declare_multiple_imports(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, """
                [import.first]
                root = "../first"
                configuration = "dirpluck.toml"

                [import.second]
                root = "../second"
                configuration = "dirpluck.toml"
            """)
            with self.assertRaisesRegex(ConfigurationError, "at most one"):
                load_config(manifest)

    def test_import_case_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, """
                [import.other]
                root = ".."
                configuration = "other/dirpluck.toml"
                case = "release"
            """)
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_import_fields_are_strictly_validated(self):
        invalid = (
            ('root = "/tmp"\nconfiguration = "a.toml"', "absolute root"),
            ('root = "C:/projects/shikumi"\nconfiguration = "a.toml"', "Windows absolute root"),
            ("root = 'C:\\projects\\shikumi'\nconfiguration = \"a.toml\"", "Windows backslash absolute root"),
            ('root = "C:projects/shikumi"\nconfiguration = "a.toml"', "Windows drive-relative root"),
            ("root = '//server/share'\nconfiguration = \"a.toml\"", "UNC root"),
            ('root = "../*"\nconfiguration = "a.toml"', "glob root"),
            ('root = ".."\nconfiguration = "../a.toml"', "configuration traversal"),
            ('root = ".."\nconfiguration = "./a.toml"', "configuration dot traversal"),
            ('root = ".."\nconfiguration = "C:/a.toml"', "Windows absolute configuration"),
            ('root = ".."\nconfiguration = "a.txt"', "configuration extension"),
        )
        for body, label in invalid:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [import.other]
                    {body}
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_import_targets_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [import.other]
                root = ".."
                configuration = "other/dirpluck.toml"
                targets = ["."]
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_unknown_import_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._write(root, '''
                [import.other]
                root = ".."
                configuration = "other/dirpluck.toml"
                inherit = true
            ''')
            with self.assertRaises(ConfigurationError):
                load_config(manifest)


    def test_import_may_define_root_owned_companions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, '''
                [shared.exclude_patterns]
                local-policy = ["*.tmp"]

                [import.external]
                root = "../external"
                configuration = "dirpluck.toml"

                [import.external.companion.project]
                path = "."
                description = "External project as a companion."
                include_if_exists = ["*"]
                exclude_pattern_refs = ["local-policy"]
                if_empty = "allow"
            '''))
            imported = config.imports["external"]
            companion = imported.companions["project"]
            self.assertEqual(companion.path, ".")
            self.assertEqual(companion.selection.description, "External project as a companion.")
            self.assertEqual([pattern.raw for pattern in companion.selection.exclude], ["*.tmp"])

    def test_import_added_companion_path_cannot_escape_import_root(self):
        invalid_paths = ("..", "../other", "/tmp/other", "C:/other")
        for path in invalid_paths:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self._write(root, f'''
                    [import.external]
                    root = "../external"
                    configuration = "dirpluck.toml"

                    [import.external.companion.project]
                    path = {path!r}
                    description = "External project."
                    include_if_exists = ["*"]
                    if_empty = "allow"
                ''')
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)


if __name__ == "__main__":
    unittest.main()
