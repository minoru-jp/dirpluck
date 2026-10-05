from pathlib import Path
import textwrap
import unittest
from unittest.mock import patch

from tests._temp import resolved_temporary_directory

from dirpluck._request_models import BuildRequest
from dirpluck.builder import resolve_sources
from dirpluck.builder import build_archive
from dirpluck._config_parser import load_config
from dirpluck.errors import ConfigurationError


class RemovedPre10BehaviorTests(unittest.TestCase):
    """Characterization tests for constraints intentionally removed from the 1.0 contract."""

    def _write(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def _project(self, root: Path, name: str, filename: str = "file.txt") -> Path:
        project = root / name
        project.mkdir(parents=True, exist_ok=True)
        (project / filename).write_text(name, encoding="utf-8")
        return project

    # Formerly test_configuration_semantics.py:test_named_scope_cannot_duplicate_default_scope_root
    def test_named_scope_cannot_duplicate_default_scope_root(self):
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
                    [scope.local]
                    path = "."
                    [output]
                    path = "out.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "Scope roots must be distinct"):
                resolve_sources(config, BuildRequest.create("./project/"))

    # Formerly test_configuration_semantics.py:test_duplicate_effective_scope_roots_are_rejected
    def test_duplicate_effective_scope_roots_are_rejected(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "work").mkdir()
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                    [pluck]
                    description = "P."
                    may = ["x"]
                    [scope.local]
                    path = "work"
                    [scope.other]
                    path = "./work"
                    [output]
                    path = "out.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "Scope roots must be distinct"):
                resolve_sources(config, BuildRequest.create("local/x/"))

    # Formerly test_configuration_semantics.py:test_output_fixed_paths_in_same_directory_do_not_conflict
    def test_output_fixed_paths_in_same_directory_do_not_conflict(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(
                root / "base.dirpluck",
                """
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                    [output]
                    path = "out/base.zip"
                """,
            )
            config = load_config(
                self._write(
                    root / "derived.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"
                    [output]
                    path = "out/derived.zip"
                """,
                )
            )
            self.assertEqual(len(resolve_sources(config, BuildRequest.create())), 1)

    # Formerly test_configuration_semantics.py:test_output_same_fixed_file_conflicts_across_base_chain
    def test_output_same_fixed_file_conflicts_across_base_chain(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(
                root / "base.dirpluck",
                """
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                    [output]
                    path = "out/result.zip"
                """,
            )
            config = load_config(
                self._write(
                    root / "derived.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"
                    [output]
                    path = "out/result.zip"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "write boundaries overlap"):
                resolve_sources(config, BuildRequest.create())

    # Formerly test_configuration_semantics.py:test_timestamp_boundary_conflicts_with_descendant_timestamp_and_fixed_file
    def test_timestamp_boundary_conflicts_with_descendant_timestamp_and_fixed_file(self):
        cases = (
            '''[output.timestamp]\npath = "artifacts/release/"''',
            '''[output]\npath = "artifacts/result.zip"''',
        )
        for derived_output in cases:
            with (
                self.subTest(derived_output=derived_output),
                resolved_temporary_directory() as temp,
            ):
                root = Path(temp)
                (root / "data").mkdir()
                (root / "data" / "x").write_text("x")
                self._write(
                    root / "base.dirpluck",
                    """
                        [always.data]
                        path = "data"
                        description = "D."
                        must = ["x"]
                        [output.timestamp]
                        path = "artifacts/"
                    """,
                )
                config = load_config(
                    self._write(
                        root / "derived.dirpluck",
                        f"""
                        [about]
                        base = "base.dirpluck"
                        {derived_output}
                    """,
                    )
                )
                with self.assertRaisesRegex(ConfigurationError, "write boundaries overlap"):
                    resolve_sources(config, BuildRequest.create())

    # Formerly test_configuration_semantics.py:test_outputless_base_does_not_create_a_write_boundary
    def test_outputless_base_does_not_create_a_write_boundary(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x")
            self._write(
                root / "base.dirpluck",
                """
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                """,
            )
            config = load_config(
                self._write(
                    root / "default.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"

                    [output.timestamp]
                    path = "artifacts/"
                """,
                )
            )
            with patch(
                "dirpluck._output._current_output_timestamp", return_value="20260920-120000"
            ):
                output = build_archive(config, BuildRequest.create())
            self.assertEqual(output, (root / "artifacts/20260920-120000.zip").resolve())

    # Formerly test_effective_configuration.py:test_outer_timestamp_boundary_conflicts_with_ancestor_timestamp
    def test_outer_timestamp_boundary_conflicts_with_ancestor_timestamp(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            self._write(
                root / "base.dirpluck",
                """
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                    [output.timestamp]
                    path = "artifacts/release/"
                """,
            )
            config = load_config(
                self._write(
                    root / "derived.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"
                    [output.timestamp]
                    path = "artifacts/"
                """,
                )
            )
            with self.assertRaisesRegex(ConfigurationError, "write boundaries overlap"):
                resolve_sources(config, BuildRequest.create())

    # Formerly test_effective_configuration.py:test_fixed_output_outside_timestamp_boundary_is_allowed
    def test_fixed_output_outside_timestamp_boundary_is_allowed(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            self._write(
                root / "base.dirpluck",
                """
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                    [output.timestamp]
                    path = "artifacts/"
                """,
            )
            config = load_config(
                self._write(
                    root / "derived.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"
                    [output]
                    path = "release/result.zip"
                """,
                )
            )
            self.assertEqual(len(resolve_sources(config, BuildRequest.create())), 1)

    # Formerly test_effective_configuration.py:test_fixed_output_in_ancestor_directory_of_timestamp_boundary_is_allowed
    def test_fixed_output_in_ancestor_directory_of_timestamp_boundary_is_allowed(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "x").write_text("x", encoding="utf-8")
            self._write(
                root / "base.dirpluck",
                """
                    [always.data]
                    path = "data"
                    description = "D."
                    must = ["x"]
                    [output.timestamp]
                    path = "artifacts/release/"
                """,
            )
            config = load_config(
                self._write(
                    root / "derived.dirpluck",
                    """
                    [about]
                    base = "base.dirpluck"
                    [output]
                    path = "artifacts/result.zip"
                """,
                )
            )
            self.assertEqual(len(resolve_sources(config, BuildRequest.create())), 1)
