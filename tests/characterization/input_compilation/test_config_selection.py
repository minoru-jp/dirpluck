from pathlib import Path
from collections.abc import Iterable
from typing import cast

from tests._config_support import ConfigTestCase
from tests._temp import resolved_temporary_directory
from tests._pipeline import resolve_sources

from dirpluck._selection_models import (
    ExclusionPattern,
    IncludePattern,
    MatchPattern,
    PathExclusion,
)
from dirpluck._request_models import BuildRequest
from dirpluck._config_models import SharedReference
from dirpluck._config_parser import load_config
from dirpluck.errors import ConfigurationError


def _raws(items: Iterable[object]) -> tuple[str, ...]:
    return tuple(
        cast(IncludePattern | ExclusionPattern | PathExclusion | MatchPattern, item).raw
        for item in items
    )


class ConfigSelectionTests(ConfigTestCase):
    def test_selection_accepts_structured_match_entries(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    r"""
                [pluck]
                must = [{ match = 'src/.*\.py' }]
                may = [{ match = 'docs/.*\.md' }]
                ignore = [{ match = 'src/generated/' }]
            """,
                )
            )
            assert config.pluck is not None
            selection = config.pluck
            self.assertEqual(_raws(selection.must), (r"src/.*\.py",))
            self.assertEqual(_raws(selection.may), (r"docs/.*\.md",))
            self.assertEqual(_raws(selection.ignore), (r"src/generated/",))

    def test_selection_accepts_structured_shared_references(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    r"""
                [shared.must]
                required = ["src/"]

                [shared.may]
                optional = ["README.md"]

                [shared.ignore]
                noise = ["*.pyc"]

                [pluck]
                must = [{ shared = "required" }]
                may = [{ shared = "optional" }]
                ignore = [{ shared = "noise" }]
            """,
                )
            )
            assert config.pluck is not None
            selection = config.pluck
            self.assertEqual(selection.must, (SharedReference("required"),))
            self.assertEqual(selection.may, (SharedReference("optional"),))
            self.assertEqual(selection.ignore, (SharedReference("noise"),))

    def test_structured_shared_reference_requires_exact_schema(self):
        invalid_entries = (
            "{ shared = '' }",
            "{ shared = 1 }",
            "{ shared = 'required', extra = 'x' }",
            "{ shared = 'required', match = 'src/' }",
            "{ path = 'src/' }",
        )
        for entry in invalid_entries:
            with self.subTest(entry=entry), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    must = [{entry}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_shared_sets_accept_structured_match_entries(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    r"""
                [shared.must]
                python = [{ match = 'src/.*\.py' }]

                [shared.ignore]
                generated = [{ match = 'src/generated/' }]

                [pluck]
                must = [{ shared = "python" }]
                ignore = [{ shared = "generated" }]
            """,
                )
            )
            self.assertEqual(
                _raws(config.shared.must["python"]),
                (r"src/.*\.py",),
            )
            self.assertEqual(
                _raws(config.shared.ignore["generated"]),
                (r"src/generated/",),
            )

    def test_structured_match_requires_exact_schema_and_valid_regex(self):
        invalid_entries = (
            "{}",
            "{ match = 1 }",
            "{ match = '' }",
            "{ match = '[', extra = 'x' }",
            "{ match = '[' }",
        )
        for entry in invalid_entries:
            with self.subTest(entry=entry), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    must = [{entry}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_structured_match_has_bounded_length(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            pattern = "a" * 513
            manifest = self._write(
                root,
                f"""
                [pluck]
                must = [{{ match = {pattern!r} }}]
            """,
            )
            with self.assertRaisesRegex(ConfigurationError, "512-character limit"):
                load_config(manifest)

    def test_duplicate_structured_match_entries_are_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                r"""
                [pluck]
                must = [
                    { match = 'src/.*\.py' },
                    { match = 'src/.*\.py' },
                ]
            """,
            )
            config = load_config(manifest)
            (root / "application").mkdir()
            with self.assertRaisesRegex(ConfigurationError, "duplicate effective pattern"):
                resolve_sources(config, BuildRequest.create("./application/"))

    def test_same_structured_match_must_and_may_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                r"""
                [pluck]
                must = [{ match = 'src/.*\.py' }]
                may = [{ match = 'src/.*\.py' }]
            """,
            )
            config = load_config(manifest)
            (root / "application").mkdir()
            with self.assertRaisesRegex(ConfigurationError, "must and may"):
                resolve_sources(config, BuildRequest.create("./application/"))

    def test_shared_must_and_ignore_patterns_use_their_own_grammars(self):
        invalid = (
            ("must", "bad", "src/**/x.py"),
            ("ignore", "bad", "src/generated/"),
        )
        for table, name, pattern in invalid:
            with self.subTest(table=table), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [shared.{table}]
                    {name} = [{pattern!r}]

                    [pluck]
                    description = "Default."
                    must = ["src/"]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_shared_pattern_sets_must_be_non_empty_arrays(self):
        for table in ("must", "may", "ignore"):
            with self.subTest(table=table), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [shared.{table}]
                    empty = []

                    [pluck]
                    description = "Default."
                    must = ["src/"]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_allow_empty_true_rejects_required_shared_reference(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [shared.must]
                required = ["src"]

                [pluck]
                description = "Default."
                must = [{ shared = "required" }]
                allow_empty = true
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_unknown_shared_key_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [shared]
                filters = ["python"]

                [pluck]
                description = "Default."
                must = ["src/"]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_pluck_default_is_valid(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["src/"]
            """,
                )
            )
            assert config.pluck is not None
            self.assertIsNotNone(config.pluck)
            self.assertEqual(dict(config.pluck_cases), {})

    def test_pluck_may_define_only_named_cases(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [case.pluck.review]
                description = "Review."
                must = ["src/"]
            """,
                )
            )
            self.assertIsNone(config.pluck)
            self.assertIn("review", config.pluck_cases)

    def test_case_name_may_equal_pluck_field_name(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [case.pluck.description]
                description = "A case literally named description."
                must = ["src/"]
            """,
                )
            )
            self.assertIsNone(config.pluck)
            self.assertIn("description", config.pluck_cases)

    def test_default_and_named_case_do_not_merge(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["src/"]
                ignore = ["*.tmp"]

                [case.pluck.review]
                description = "Review."
                must = ["tests/"]
            """,
                )
            )
            assert config.pluck is not None
            self.assertEqual(_raws(config.pluck.must), ("src/",))
            self.assertEqual(
                _raws(config.pluck_cases["review"].must),
                ("tests/",),
            )
            self.assertEqual(config.pluck_cases["review"].ignore, ())

    def test_pluck_must_define_default_or_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(self._write(root, "[pluck]\n"))

    def test_unknown_pluck_key_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaises(ConfigurationError):
                load_config(
                    self._write(
                        root,
                        """
                    [pluck]
                    description = "Default."
                    must = ["src/"]
                    path = "app"
                """,
                    )
                )

    def test_must_may_name_nested_concrete_path(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["dist/package.whl"]
            """,
                )
            )
            assert config.pluck is not None
            self.assertEqual(_raws(config.pluck.must), ("dist/package.whl",))

    def test_must_allows_one_star_per_path_element(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["packages/*/dist/pkg-*.whl", "plugins/foo*bar"]
            """,
                )
            )
            assert config.pluck is not None
            self.assertEqual(
                _raws(config.pluck.must),
                ("packages/*/dist/pkg-*.whl", "plugins/foo*bar"),
            )

    def test_must_rejects_recursive_or_richer_pattern_syntax(self):
        invalid = ["src/**/x.py", "foo*bar*baz", "src/?.py", "src/[ab].py", "!src"]
        for pattern in invalid:
            with self.subTest(pattern=pattern), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    must = [{pattern!r}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_may_uses_must_pattern_syntax(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                may = ["packages/*/README.md"]
                allow_empty = true
            """,
                )
            )
            assert config.pluck is not None
            self.assertEqual(
                _raws(config.pluck.may),
                ("packages/*/README.md",),
            )

    def test_legacy_include_fields_are_rejected(self):
        for field in ("include", "include_if_exists"):
            with self.subTest(field=field), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    {field} = []
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_selection_requires_must_or_may(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                ignore = ["*.pyc"]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_allow_empty_true_rejects_must(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                allow_empty = true
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_legacy_if_empty_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                may = ["src"]
                if_empty = "ignore"
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_ignore_may_be_explicitly_empty(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["src/"]
                ignore = []
            """,
                )
            )
            assert config.pluck is not None
            self.assertEqual(config.pluck.ignore, ())

    def test_legacy_target_case_table_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [target.case]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_ignore_must_be_an_array(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                ignore = "*.pyc"
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_ignore_path_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                ignore = ["src/generated/"]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_ignore_middle_wildcard_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                ignore = ["foo*bar"]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_ignore_unsupported_pattern_syntax_is_rejected(self):
        for pattern in ("**", "?.py", "[ab].py", "!keep.py"):
            with self.subTest(pattern=pattern), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    must = ["src/"]
                    ignore = [{pattern!r}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_ignore_star_alone_is_rejected(self):
        for pattern in ("*", "*/"):
            with self.subTest(pattern=pattern), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    must = ["src/"]
                    ignore = [{pattern!r}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_must_pattern_rejects_backslash_separator(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                r"""
                [pluck]
                description = "Default."
                must = ['src\package']
            """,
            )
            with self.assertRaisesRegex(ConfigurationError, "backslashes"):
                load_config(manifest)

    def test_always_owns_exactly_one_selection(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["src/"]
                [always.framework]
                path = "framework"
                description = "Framework."
                must = ["src/"]
                may = ["README.md"]
            """,
                )
            )
            selection = config.always["framework"].selection
            self.assertEqual(_raws(selection.must), ("src/",))
            self.assertEqual(_raws(selection.may), ("README.md",))

    def test_always_cases_filter_named_sources(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [always.framework]
                path = "framework"
                description = "Framework."
                must = ["src/"]

                [always.docs]
                path = "docs"
                description = "Docs."
                must = ["README.md"]

                [case.always.review]
                description = "Framework only."
                include = ["framework"]
            """,
                )
            )
            case = config.always_cases["review"]
            self.assertEqual(case.description, "Framework only.")
            self.assertEqual(case.include, ("framework",))
            self.assertIsNone(case.exclude)

    def test_always_case_reference_validation_is_deferred_to_effective_configuration(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [always.framework]
                path = "framework"
                must = ["src/"]

                [case.always.release]
                include = ["missing"]
            """,
                )
            )
            self.assertIn("release", config.always_cases)
            with self.assertRaisesRegex(ConfigurationError, "undefined Always source"):
                resolve_sources(config, BuildRequest.create())

    def test_always_only_configuration_may_define_its_own_cases(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [always.documents]
                path = "documents"
                description = "Current documents."
                must = ["current/"]

                [case.always.archive]
                description = "Documents only."
                include = ["documents"]
            """,
                )
            )
            self.assertIsNone(config.pluck)
            self.assertIn("archive", config.always_cases)
            self.assertEqual(config.always_cases["archive"].include, ("documents",))

    def test_always_case_include_and_exclude_empty_have_distinct_meanings(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [always.case]
                path = "case-files"
                must = ["README.md"]

                [case.always.none]
                include = []

                [case.always.all]
                exclude = []
            """,
                )
            )
            self.assertIn("case", config.always)
            self.assertEqual(config.always_cases["none"].include, ())
            self.assertIsNone(config.always_cases["none"].exclude)
            self.assertIsNone(config.always_cases["all"].include)
            self.assertEqual(config.always_cases["all"].exclude, ())

    def test_always_case_include_and_exclude_are_mutually_exclusive(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ConfigurationError, "mutually exclusive"):
                load_config(
                    self._write(
                        root,
                        """
                    [case.always.invalid]
                    include = []
                    exclude = []
                """,
                    )
                )

    def test_case_hierarchy_is_rejected(self):
        for table in ("case.pluck.review.extra", "case.always.review.extra"):
            with self.subTest(table=table), resolved_temporary_directory() as temp:
                root = Path(temp)
                if table.startswith("case.pluck"):
                    text = f"""
                        [{table}]
                        description = "Nested."
                        must = ["src/"]
                    """
                else:
                    text = f"""
                        [always.framework]
                        path = "framework"
                        description = "Framework."
                        must = ["src/"]
                        [{table}]
                        description = "Nested."
                        must = ["tests/"]
                    """
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(root, text))

    def test_always_description_is_optional(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                must = ["src/"]
                [always.framework]
                path = "framework"
                must = ["src/"]
            """,
            )
            config = load_config(manifest)
            self.assertIsNone(config.always["framework"].selection.description)

    def test_pluck_description_is_optional(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                must = ["src/"]
            """,
            )
            config = load_config(manifest)
            assert config.pluck is not None
            self.assertIsNone(config.pluck.description)

    def test_case_description_is_optional(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [case.pluck.review]
                must = ["src/"]
            """,
            )
            config = load_config(manifest)
            self.assertIsNone(config.pluck)
            self.assertIsNone(config.pluck_cases["review"].description)

    def test_selection_description_is_optional_for_pluck_and_always(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                must = ["src/"]

                [always.docs]
                path = "docs"
                may = ["*.md"]
                allow_empty = true
            """,
                )
            )
            self.assertIsNotNone(config.pluck)
            assert config.pluck is not None
            self.assertIsNone(config.pluck.description)
            self.assertIsNone(config.always["docs"].selection.description)

    def test_selection_description_rejects_blank_value_when_present(self):
        bodies = (
            """
            [pluck]
            description = "   "
            must = ["src/"]
            """,
            """
            [always.docs]
            path = "docs"
            description = "   "
            must = ["*.md"]
            """,
        )
        for body in bodies:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaisesRegex(ConfigurationError, "expected a non-empty string"):
                    load_config(self._write(root, body))


class IgnoreStructuredPathConfigTests(ConfigTestCase):
    def test_ignore_accepts_structured_relative_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                must = ["src/"]
                ignore = [
                    { path = "tests/fixtures/big.bin" },
                    { path = "./src/generated/" },
                    { path = "src/./cache/" },
                ]
            """,
                )
            )
            assert config.pluck is not None
            ignore = config.pluck.ignore
            path_ignore = tuple(cast(PathExclusion, item) for item in ignore)
            self.assertEqual(
                [(item.raw, item.path, item.directory) for item in path_ignore],
                [
                    ("./tests/fixtures/big.bin", "tests/fixtures/big.bin", False),
                    ("./src/generated/", "src/generated", True),
                    ("./src/cache/", "src/cache", True),
                ],
            )

    def test_ignore_structured_path_must_be_relative_concrete_and_inside_root(self):
        invalid = (
            "",
            ".",
            "./",
            "../outside.txt",
            "./../outside.txt",
            "/absolute.txt",
            "C:/absolute.txt",
            "tests/*.bin",
            "tests\\big.bin",
        )
        for reference in invalid:
            with self.subTest(reference=reference), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    must = ["src/"]
                    ignore = [{{ path = {reference!r} }}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_ignore_path_normalization_makes_dot_slash_duplicate(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                must = ["src/"]
                ignore = [
                    { path = "src/generated/" },
                    { path = "./src/generated/" },
                ]
            """,
            )
            config = load_config(manifest)
            (root / "application").mkdir()
            with self.assertRaisesRegex(ConfigurationError, "duplicate effective pattern"):
                resolve_sources(config, BuildRequest.create("./application/"))

    def test_ignore_path_structured_entry_requires_exact_schema(self):
        invalid_entries = (
            "{ path = 1 }",
            "{ path = 'src/', extra = 'x' }",
            "{ path = 'src/', shared = 'noise' }",
        )
        for entry in invalid_entries:
            with self.subTest(entry=entry), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    must = ["src/"]
                    ignore = [{entry}]
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)


class IgnorePathReferenceConfigTests(ConfigTestCase):
    def test_ignore_accepts_selection_relative_file_and_directory_references(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                must = ["src/"]
                ignore = [
                    { path = "tests/fixtures/big.bin" },
                    { path = "src/generated/" },
                ]
            """,
                )
            )
            assert config.pluck is not None
            ignore = config.pluck.ignore
            path_ignore = tuple(cast(PathExclusion, item) for item in ignore)
            self.assertEqual(
                [(item.raw, item.path, item.directory) for item in path_ignore],
                [
                    ("./tests/fixtures/big.bin", "tests/fixtures/big.bin", False),
                    ("./src/generated/", "src/generated", True),
                ],
            )

    def test_direct_ignore_string_remains_name_based_and_rejects_paths(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                must = ["src/"]
                ignore = ["tests/fixtures/big.bin"]
            """,
            )
            with self.assertRaisesRegex(ConfigurationError, "entity names, not paths"):
                load_config(manifest)
