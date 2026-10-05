from pathlib import Path
import textwrap

from tests._config_support import ConfigTestCase
from tests._temp import resolved_temporary_directory

from dirpluck._config_parser import load_config
from dirpluck.errors import ConfigurationError


class ConfigSchemaTests(ConfigTestCase):
    def test_about_description_is_optional_and_parsed_when_present(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            without_about = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["src/"]
            """,
                )
            )
            self.assertIsNone(without_about.about_description)

            with_about = load_config(
                self._write(
                    root,
                    """
                [about]
                description = "Materials for reviewing the authentication redesign."

                [pluck]
                description = "Default."
                must = ["src/"]
            """,
                )
            )
            self.assertEqual(
                with_about.about_description,
                "Materials for reviewing the authentication redesign.",
            )

    def test_about_rejects_empty_table_blank_description_and_unknown_fields(self):
        bodies = (
            """
            [about]
            [pluck]
            description = "Default."
            must = ["src/"]
            """,
            """
            [about]
            description = "   "
            [pluck]
            description = "Default."
            must = ["src/"]
            """,
            """
            [about]
            description = "Summary."
            title = "Not supported"
            [pluck]
            description = "Default."
            must = ["src/"]
            """,
        )
        for body in bodies:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(root, body))

    def test_namespace_definitions_are_empty_named_tables(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [namespace.work]
                [namespace.external]

                [pluck]
                description = "Default."
                must = ["src/"]

                [scope]
                namespace = "work"
            """,
                )
            )
            self.assertEqual(set(config.namespaces), {"work", "external"})
            self.assertEqual(config.scopes[None].namespace, "work")

    def test_always_names_must_be_single_archive_directory_components(self):
        invalid_names = (".", "..", "a/b", "a\\b")
        for name in invalid_names:
            with self.subTest(name=name), resolved_temporary_directory() as temp:
                root = Path(temp)
                body = f"""
                [always.{name!r}]
                path = "docs"
                may = ["*.md"]
                allow_empty = true
                """
                with self.assertRaisesRegex(ConfigurationError, "one Archive directory component"):
                    load_config(self._write(root, body))

    def test_always_names_reject_control_characters(self):
        escaped_names = (
            r"docs\u0000evil",
            r"line\u000Afeed",
            r"tab\u0009name",
            r"del\u007Fname",
            r"readme.md\u0000x",
        )
        for escaped_name in escaped_names:
            with self.subTest(name=escaped_name), resolved_temporary_directory() as temp:
                root = Path(temp)
                body = f"""
                [always."{escaped_name}"]
                path = "docs"
                may = ["*.md"]
                allow_empty = true
                """
                with self.assertRaisesRegex(ConfigurationError, "control characters"):
                    load_config(self._write(root, body))

    def test_always_names_do_not_apply_host_os_reserved_name_rules(self):
        accepted_names = ("CON", "docs.", "a:b")
        for name in accepted_names:
            with self.subTest(name=name), resolved_temporary_directory() as temp:
                root = Path(temp)
                config = load_config(
                    self._write(
                        root,
                        f"""
                        [always.'{name}']
                        path = "docs"
                        may = ["*.md"]
                        allow_empty = true
                        """,
                    )
                )
                self.assertIn(name, config.always)

    def test_always_names_must_be_distinct_ignoring_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            body = """
            [always.Docs]
            path = "docs-a"
            may = ["*.md"]
            allow_empty = true

            [always.docs]
            path = "docs-b"
            may = ["*.md"]
            allow_empty = true
            """
            with self.assertRaisesRegex(ConfigurationError, "distinct ignoring case"):
                load_config(self._write(root, body))

    def test_namespace_names_do_not_apply_host_os_reserved_name_rules(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                    [namespace.CON]
                    [namespace."docs."]
                    """,
                )
            )
            self.assertEqual(set(config.namespaces), {"CON", "docs."})

    def test_namespace_names_reject_path_separators_and_control_characters(self):
        invalid_bodies = (
            """
            [namespace.'a\\b']
            """,
            r"""
            [namespace."docs\u0000evil"]
            """,
        )
        for body in invalid_bodies:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                with self.assertRaisesRegex(
                    ConfigurationError, "path separators or control characters"
                ):
                    load_config(self._write(Path(temp), body))

    def test_namespace_names_must_be_distinct_ignoring_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            body = """
            [namespace.Docs]
            [namespace.docs]
            """
            with self.assertRaisesRegex(ConfigurationError, "distinct ignoring case"):
                load_config(self._write(root, body))

    def test_bare_namespace_parent_does_not_define_a_namespace(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ConfigurationError, "define at least one"):
                load_config(
                    self._write(
                        root,
                        """
                    [namespace]

                    [pluck]
                    description = "Default."
                    must = ["src/"]
                """,
                    )
                )

    def test_namespace_definition_rejects_attributes_and_invalid_component_names(self):
        invalid = (
            """
            [namespace.work]
            directory = "work"
            [pluck]
            description = "Default."
            must = ["src/"]
            """,
            """
            [namespace."bad/name"]
            [pluck]
            description = "Default."
            must = ["src/"]
            """,
        )
        for body in invalid:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(Path(temp), body))

    def test_source_less_configuration_parses_for_chain_resolution(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(self._write(root, "", add_output=True))
            self.assertIsNone(config.pluck)
            self.assertEqual(dict(config.always), {})

    def test_always_only_configuration_is_valid(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [always.documents]
                path = "documents"
                description = "Documents."
                must = ["*.pdf"]
            """,
                )
            )
            self.assertIsNone(config.pluck)
            self.assertEqual(config.always["documents"].path, "documents")

    def test_unknown_top_level_key_is_rejected(self):
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
                    [bundle.review]
                    description = "Old model"
                """,
                    )
                )

    def test_unknown_always_key_is_rejected(self):
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
                    [always.framework]
                    path = "framework"
                    description = "Framework."
                    must = ["src/"]
                    case = "review"
                """,
                    )
                )

    def test_always_path_is_required(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [always.framework]
                description = "Framework."
                must = ["src/"]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_always_path_accepts_dot_parent_and_host_absolute(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            absolute = (root.parent / "framework").as_posix()
            for path in (".", "..", "../framework", absolute):
                with self.subTest(path=path):
                    config = load_config(
                        self._write(
                            root,
                            f"""
                        [pluck]
                        description = "Default."
                        must = ["src/"]
                        [always.framework]
                        path = {path!r}
                        description = "Framework."
                        must = ["src/"]
                    """,
                        )
                    )
                    self.assertEqual(config.always["framework"].path, path)

    def test_always_path_must_be_concrete(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [always.framework]
                path = "framework*"
                description = "Framework."
                must = ["src/"]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_always_path_rejects_backslash_separator(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                r"""
                [pluck]
                description = "Default."
                must = ["src/"]
                [always.framework]
                path = 'shared\framework'
                description = "Framework."
                must = ["src/"]
            """,
            )
            with self.assertRaisesRegex(ConfigurationError, "backslashes"):
                load_config(manifest)

    def test_output_is_optional_when_loading_configuration(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
            """,
                add_output=False,
            )
            config = load_config(manifest)
            self.assertIsNone(config.output)

    def test_legacy_output_if_exists_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [output]
                path = "out.zip"
                if_exists = "rename"
            """,
                add_output=False,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_fixed_and_legacy_generated_output_fields_cannot_be_combined(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [output]
                path = "out.zip"
                overwrite = false
                directory = "snapshots"
                timestamp = true
            """,
                add_output=False,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_legacy_generated_output_rejects_overwrite(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [pluck]
                description = "Default."
                must = ["src/"]
                [output]
                directory = "snapshots"
                timestamp = true
                overwrite = false
            """,
                add_output=False,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_legacy_generated_output_shape_is_rejected(self):
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
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    must = ["src/"]
                    {textwrap.dedent(body)}
                """,
                    add_output=False,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_legacy_generated_output_fields_are_rejected(self):
        bad_values = (
            ("directory", "snap*shots"),
            ("directory", r"snap\shots"),
            ("prefix", "group/name"),
            ("suffix", "review?"),
            ("prefix", "bad\nname"),
        )
        for field, value in bad_values:
            with self.subTest(field=field, value=value), resolved_temporary_directory() as temp:
                root = Path(temp)
                extra = f"{field} = {value!r}\n"
                if field != "directory":
                    extra = 'directory = "snapshots"\n' + extra
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    must = ["src/"]
                    [output]
                    {extra}
                    timestamp = true
                """,
                    add_output=False,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_output_path_must_be_concrete_file_path(self):
        for path in ("*.zip", ".", r"artifacts\out.zip"):
            with self.subTest(path=path), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [pluck]
                    description = "Default."
                    must = ["src/"]
                    [output]
                    path = {path!r}
                    overwrite = false
                """,
                    add_output=False,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_output_path_accepts_parent_and_host_absolute(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            absolute = (root.parent / "out.zip").as_posix()
            for path in ("../out.zip", absolute):
                with self.subTest(path=path):
                    config = load_config(
                        self._write(
                            root,
                            f"""
                        [pluck]
                        description = "Default."
                        must = ["src/"]
                        [output]
                        path = {path!r}
                        overwrite = false
                    """,
                            add_output=False,
                        )
                    )
                    assert config.output is not None
                    self.assertEqual(config.output.path, path)

    def test_legacy_import_case_field_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [import.other]
                root = ".."
                configuration = "other/default.dirpluck"
                case = "release"
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_legacy_import_fields_are_rejected(self):
        invalid = (
            (
                "root = 'C:\\projects\\shikumi'\nconfiguration = \"a.dirpluck\"",
                "Windows backslash absolute root",
            ),
            (
                'root = "C:projects/shikumi"\nconfiguration = "a.dirpluck"',
                "Windows drive-relative root",
            ),
            ('root = "../*"\nconfiguration = "a.dirpluck"', "glob root"),
            ('root = ".."\nconfiguration = "../a.dirpluck"', "configuration traversal"),
            ('root = ".."\nconfiguration = "./a.dirpluck"', "configuration dot traversal"),
            ('root = ".."\nconfiguration = "C:/a.dirpluck"', "Windows absolute configuration"),
            ("root = '..'\nconfiguration = 'nested\\a.dirpluck'", "configuration backslash"),
            ('root = ".."\nconfiguration = "a.txt"', "configuration extension"),
        )
        for body, label in invalid:
            with self.subTest(label=label), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                    [import.other]
                    {body}
                """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)

    def test_legacy_import_targets_key_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [import.other]
                root = ".."
                configuration = "other/default.dirpluck"
                targets = ["."]
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_legacy_import_key_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                [import.other]
                root = ".."
                configuration = "other/default.dirpluck"
                inherit = true
            """,
            )
            with self.assertRaises(ConfigurationError):
                load_config(manifest)

    def test_legacy_target_skip_is_rejected(self):
        invalid = ("group/archive", "archive/", r"archive\old", "*", "foo*bar", "foo?", "[foo]")
        for pattern in invalid:
            with self.subTest(pattern=pattern), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaises(ConfigurationError):
                    load_config(
                        self._write(
                            root,
                            f"""
                        [pluck]
                        description = "Default."
                        must = ["src/"]
                        skip = [{pattern!r}]
                    """,
                        )
                    )

    def test_scope_names_and_tables_are_strict(self):
        invalid_bodies = (
            """            [pluck]
            description = "Default."
            must = ["src/"]
            [scope."work.dev"]
            path = "projects"
            """,
            """            [pluck]
            description = "Default."
            must = ["src/"]
            [scope.work]
            """,
            """            [pluck]
            description = "Default."
            must = ["src/"]
            [scope.work]
            path = "projects"
            extra = true
            """,
            r"""            [pluck]
            description = "Default."
            must = ["src/"]
            [scope.work]
            path = 'projects\nested'
            """,
        )
        for body in invalid_bodies:
            with self.subTest(body=body), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaises(ConfigurationError):
                    load_config(self._write(root, body))

    def test_scope_parses_description_and_target_kind_with_directory_default(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            config = load_config(
                self._write(
                    root,
                    """
                [pluck]
                description = "Default."
                must = ["src/"]

                [scope]
                description = "Default workspace."

                [scope.returned]
                path = "returned"
                description = "Returned archives."
                target_kind = "file"
            """,
                )
            )
            self.assertEqual(config.scopes[None].description, "Default workspace.")
            self.assertEqual(config.scopes[None].target_kind, "directory")
            self.assertEqual(config.scopes["returned"].description, "Returned archives.")
            self.assertEqual(config.scopes["returned"].target_kind, "file")

            both = load_config(
                self._write(
                    root,
                    """
                [scope.mixed]
                path = "mixed"
                target_kind = "both"
            """,
                )
            )
            self.assertEqual(both.scopes["mixed"].target_kind, "both")

    def test_scope_target_kind_rejects_unknown_and_non_string_values(self):
        invalid_values = ('"archive"', "true", "1")
        for value in invalid_values:
            with self.subTest(value=value), resolved_temporary_directory() as temp:
                root = Path(temp)
                with self.assertRaisesRegex(
                    ConfigurationError, "expected 'directory', 'file', or 'both'"
                ):
                    load_config(
                        self._write(
                            root,
                            f"""
                        [pluck]
                        description = "Default."
                        must = ["src/"]

                        [scope.work]
                        path = "work"
                        target_kind = {value}
                    """,
                        )
                    )

    def test_scope_description_must_be_nonempty_string(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ConfigurationError, "expected a non-empty string"):
                load_config(
                    self._write(
                        root,
                        """
                    [pluck]
                    description = "Default."
                    must = ["src/"]

                    [scope.work]
                    path = "work"
                    description = "   "
                """,
                    )
                )
