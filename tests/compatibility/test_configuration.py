from pathlib import Path
from typing import cast
import textwrap
import unittest
import warnings

from tests._builder_support import BuilderTestCase
from tests._config_support import ConfigTestCase
from tests._temp import resolved_temporary_directory
from tests._pipeline import resolve_sources

from dirpluck import AlwaysMigrationWarning, ConfigurationDeprecationWarning
from dirpluck._request_models import BuildRequest
from dirpluck._selection_models import PathExclusion
from dirpluck._config_models import SharedReference
from dirpluck._config_parser import load_config
from dirpluck.errors import ConfigurationError, SelectionError


class Pre10ConfigCompatibilityTests(ConfigTestCase):
    # Moved from test_config_schema.py:ConfigSchemaTests.test_always_namespace_emits_transitional_name_override_warning
    def test_always_namespace_emits_transitional_name_override_warning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root,
                """
                    [namespace.external]

                    [always.docs]
                    path = "docs"
                    namespace = "external"
                    may = ["*.md"]
                    allow_empty = true
                    """,
            )
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", AlwaysMigrationWarning)
                config = load_config(manifest)
            self.assertEqual(config.always["docs"].compatibility_namespace, "external")
            messages = [
                str(item.message)
                for item in caught
                if issubclass(item.category, AlwaysMigrationWarning)
            ]
            self.assertEqual(len(messages), 1)
            self.assertIn("replaces the Always source name 'docs'", messages[0])
            self.assertIn("will be removed in 1.0.0", messages[0])

    # Moved from test_config_selection.py:ConfigSelectionTests.test_legacy_pluck_case_is_accepted_with_migration_warning
    def test_legacy_pluck_case_is_accepted_with_migration_warning(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConfigurationDeprecationWarning)
                config = load_config(
                    self._write(
                        root,
                        """
                        [pluck.case.review]
                        must = ["src/"]
                    """,
                    )
                )
            self.assertIsNone(config.pluck)
            self.assertIn("review", config.pluck_cases)
            messages = [
                str(warning.message)
                for warning in caught
                if issubclass(warning.category, ConfigurationDeprecationWarning)
            ]
            self.assertEqual(len(messages), 1)
            self.assertIn("[pluck.case.<name>]", messages[0])
            self.assertIn("[case.pluck.<name>]", messages[0])
            self.assertIn("1.0.0", messages[0])

    # Moved from test_config_selection.py:ConfigSelectionTests.test_legacy_and_canonical_pluck_case_same_name_is_rejected
    def test_legacy_and_canonical_pluck_case_same_name_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ConfigurationError, "defined using both"):
                load_config(
                    self._write(
                        root,
                        """
                        [pluck.case.review]
                        must = ["src/"]

                        [case.pluck.review]
                        must = ["tests/"]
                    """,
                    )
                )

    # Moved from test_config_selection.py:IgnorePathReferenceConfigTests.test_ignore_plain_nested_array_still_means_shared_reference
    def test_ignore_plain_nested_array_still_means_shared_reference(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConfigurationDeprecationWarning)
                config = load_config(
                    self._write(
                        root,
                        """
                        [shared.ignore]
                        common = ["*.pyc"]

                        [pluck]
                        must = ["src/"]
                        ignore = [["common"], ["./src/generated/"]]
                    """,
                    )
                )
            self.assertEqual(
                sum(
                    issubclass(warning.category, ConfigurationDeprecationWarning)
                    for warning in caught
                ),
                1,
            )
            assert config.pluck is not None
            ignore = config.pluck.ignore
            shared_reference = cast(SharedReference, ignore[0])
            path_exclusion = cast(PathExclusion, ignore[1])
            self.assertIsInstance(shared_reference, SharedReference)
            self.assertEqual(shared_reference.name, "common")
            self.assertIsInstance(path_exclusion, PathExclusion)
            self.assertEqual(path_exclusion.raw, "./src/generated/")

    # Moved from test_config_selection.py:IgnorePathReferenceConfigTests.test_ignore_path_reference_must_be_concrete_and_stay_inside_selection_root
    def test_ignore_path_reference_must_be_concrete_and_stay_inside_selection_root(self):
        invalid = (
            "./",
            "./../outside.txt",
            "./tests/*.bin",
            "./tests\\big.bin",
        )
        for reference in invalid:
            with self.subTest(reference=reference), resolved_temporary_directory() as temp:
                root = Path(temp)
                manifest = self._write(
                    root,
                    f"""
                        [pluck]
                        must = ["src/"]
                        ignore = [[{reference!r}]]
                    """,
                )
                with self.assertRaises(ConfigurationError):
                    load_config(manifest)


class Pre10EffectiveCompatibilityTests(unittest.TestCase):
    def _write(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    # Moved from test_configuration_compiler.py:ConfigurationCompilerTests.test_unknown_always_namespace_reference_is_rejected
    def test_unknown_always_namespace_reference_is_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("guide", encoding="utf-8")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                    [always.docs]
                    path = "docs"
                    namespace = "missing"
                    description = "Docs."
                    must = ["guide.md"]
                    [output]
                    path = "out.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "unknown Namespace 'missing'"):
                resolve_sources(config, BuildRequest.create())

    # Moved from test_configuration_compiler.py:ConfigurationCompilerTests.test_always_namespace_override_names_must_be_unique_after_composition
    def test_always_namespace_override_names_must_be_unique_after_composition(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for directory in ("a-source", "shared-source"):
                path = root / directory
                path.mkdir()
                (path / "file.txt").write_text(directory, encoding="utf-8")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                        [namespace.shared]

                        [always.a]
                        path = "a-source"
                        namespace = "shared"
                        must = ["file.txt"]

                        [always.shared]
                        path = "shared-source"
                        must = ["file.txt"]
                    """,
                )
            )
            with self.assertRaisesRegex(
                ConfigurationError,
                "distinct ignoring case after namespace resolution",
            ):
                resolve_sources(config, BuildRequest.create())

    # Moved from test_configuration_compiler.py:ConfigurationCompilerTests.test_always_effective_names_must_be_unique_ignoring_case
    def test_always_effective_names_must_be_unique_ignoring_case(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for directory in ("a-source", "docs-source"):
                path = root / directory
                path.mkdir()
                (path / "file.txt").write_text(directory, encoding="utf-8")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                        [namespace.Docs]

                        [always.a]
                        path = "a-source"
                        namespace = "Docs"
                        must = ["file.txt"]

                        [always.docs]
                        path = "docs-source"
                        must = ["file.txt"]
                    """,
                )
            )
            with self.assertRaisesRegex(
                ConfigurationError,
                "distinct ignoring case after namespace resolution",
            ):
                resolve_sources(config, BuildRequest.create())

    def test_always_layout_warning_is_not_emitted_for_unselected_source(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            (source / "guide.md").write_text("guide", encoding="utf-8")
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                    [always.docs]
                    path = "source"
                    must = ["guide.md"]

                    [case.always.none]
                    include = []
                    """,
                )
            )
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", AlwaysMigrationWarning)
                sources = resolve_sources(config, BuildRequest.create(case=".none"))
            self.assertEqual(sources, ())
            self.assertFalse(
                any(issubclass(item.category, AlwaysMigrationWarning) for item in caught)
            )


class Pre10SourceCompatibilityTests(BuilderTestCase):
    # Moved from test_source_resolution.py:SourceResolutionTests.test_namespace_cannot_place_source_under_generated_archive_readme
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
