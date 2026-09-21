from pathlib import Path
import os
import subprocess
import unittest

from _config_support import ConfigTestCase
from _temp import resolved_temporary_directory

from dirpluck.config import load_config, resolve_config_path
from dirpluck.errors import ConfigurationError


class ConfigPathTests(ConfigTestCase):
    def test_configuration_document_requires_dirpluck_extension(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            legacy = root / "dirpluck.toml"
            legacy.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            with self.assertRaisesRegex(
                ConfigurationError,
                r"configuration file must end with '\.dirpluck'",
            ):
                load_config(legacy)

    def test_default_configuration_resolution_uses_only_cwd_default(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            nested = root / ".dirpluck" / "default.dirpluck"
            nested.parent.mkdir()
            nested.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            with self.assertRaisesRegex(ConfigurationError, "configuration file was not found"):
                resolve_config_path(cwd=root)

            default = root / "default.dirpluck"
            default.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            self.assertEqual(resolve_config_path(cwd=root), default.resolve())

    def test_explicit_configuration_path_is_resolved_from_cwd(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            path = root / "configs" / "release-1.2.dirpluck"
            path.parent.mkdir()
            path.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            self.assertEqual(
                resolve_config_path("configs/release-1.2", cwd=root),
                path.resolve(),
            )

    def test_parent_relative_configuration_path_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            cwd = root / "workspace"
            cwd.mkdir()
            path = root / "shared" / "release.dirpluck"
            path.parent.mkdir()
            path.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            self.assertEqual(
                resolve_config_path("../shared/release", cwd=cwd),
                path.resolve(),
            )

    def test_absolute_configuration_path_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            path = root / "shared" / "release.dirpluck"
            path.parent.mkdir()
            path.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            self.assertEqual(
                resolve_config_path(str(path.with_suffix("")), cwd=root),
                path.resolve(),
            )

    def test_configuration_path_allows_symbolic_link_document_and_preserves_selected_path(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            real = root / "shared.dirpluck"
            real.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            link = root / "default.dirpluck"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            selected = resolve_config_path(cwd=root)
            self.assertEqual(selected, link.absolute())
            self.assertEqual(load_config(selected).manifest, link.absolute())

    def test_configuration_path_allows_symbolic_link_directory_component(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            shared.mkdir()
            real = shared / "release.dirpluck"
            real.write_text('[output]\npath = "out.zip"\n', encoding="utf-8")
            link = root / "configs"
            try:
                link.symlink_to(shared, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            selected = resolve_config_path("configs/release", cwd=root)
            self.assertEqual(selected, root / "configs" / "release.dirpluck")
            self.assertEqual(load_config(selected).manifest, selected)

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics are Windows-specific")
    def test_configuration_path_allows_windows_directory_junction_component(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            shared.mkdir()
            (shared / "release.dirpluck").write_text(
                '[output]\npath = "out.zip"\n', encoding="utf-8"
            )
            junction = root / "configs"
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(shared)],
                capture_output=True,
                text=True,
                check=False,
            )
            if created.returncode != 0:
                self.fail(
                    f"could not create Windows directory junction: {created.stderr or created.stdout}"
                )
            selected = resolve_config_path("configs/release", cwd=root)
            self.assertEqual(selected, root / "configs" / "release.dirpluck")
            self.assertEqual(load_config(selected).manifest, selected)

    def test_configuration_path_must_name_one_document(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for reference in (".", "..", "configs/"):
                with self.subTest(reference=reference), self.assertRaisesRegex(
                    ConfigurationError,
                    "must name one Configuration file",
                ):
                    resolve_config_path(reference, cwd=root)

    def test_configuration_path_uses_filesystem_location_notation(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ConfigurationError, "use '/' as the path separator"):
                resolve_config_path(r"configs\\release", cwd=root)
            with self.assertRaises(ConfigurationError):
                resolve_config_path("configs/*.dirpluck", cwd=root)

    def test_about_base_requires_dirpluck_extension(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(
                ConfigurationError,
                r"base Configuration path must end with '\.dirpluck'",
            ):
                load_config(self._write(root, '''
                    [about]
                    base = "base.toml"
                '''))
