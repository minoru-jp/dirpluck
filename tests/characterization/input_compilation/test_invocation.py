import os
import subprocess
import textwrap
import unittest
from pathlib import Path

from tests._temp import resolved_temporary_directory

from dirpluck._case import CaseSelection
from dirpluck.errors import InvocationError
from dirpluck.invocation import (
    INVOCATION_SUFFIX,
    load_invocation,
    resolve_invocation_path,
)


class InvocationTemplateTests(unittest.TestCase):
    def _write(self, path: Path, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body), encoding="utf-8")
        return path

    def test_loads_one_invocation_template(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root / ".dirpluck" / "release.dirpluck-inv",
                """
                [invocation]
                config = "release.dirpluck"
                targets = ["work/frontend/", "work/backend/", "docs/"]
                case = "publish"
                """,
            )
            template = load_invocation(manifest)
            invocation = template.select()
            self.assertEqual(template.manifest, manifest.resolve())
            self.assertEqual(invocation.config, "release.dirpluck")
            self.assertEqual(
                invocation.targets,
                ("work/frontend/", "work/backend/", "docs/"),
            )
            self.assertEqual(invocation.case, CaseSelection(pluck="publish"))
            self.assertIsNone(invocation.archive_mtime)
            self.assertEqual(
                invocation.config_path(),
                (root / ".dirpluck" / "release.dirpluck").resolve(),
            )
            self.assertFalse(invocation.is_empty)
            self.assertEqual(dict(template.entries), {})

    def test_empty_document_requires_invocation_table(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(Path(temp) / "empty.dirpluck-inv", "")
            with self.assertRaisesRegex(
                InvocationError,
                r"\[invocation\] table is required",
            ):
                load_invocation(manifest)

    def test_invocation_key_must_be_a_table(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "invalid.dirpluck-inv",
                'invocation = "not-a-table"\n',
            )
            with self.assertRaisesRegex(InvocationError, r"\[invocation\]: expected a table"):
                load_invocation(manifest)

    def test_all_invocation_fields_are_optional(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(Path(temp) / "empty.dirpluck-inv", "[invocation]\n")
            template = load_invocation(manifest)
            invocation = template.select()
            self.assertIsNone(invocation.config)
            self.assertEqual(invocation.targets, ())
            self.assertIsNone(invocation.case)
            self.assertIsNone(invocation.archive_mtime)
            self.assertIsNone(invocation.config_path())
            self.assertTrue(invocation.is_empty)

    def test_config_appends_dirpluck_suffix_when_omitted(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root / "release.dirpluck-inv",
                """
                [invocation]
                config = "configs/release-1.2"
                """,
            )
            invocation = load_invocation(manifest).select()
            self.assertEqual(invocation.config, "configs/release-1.2.dirpluck")
            self.assertEqual(
                invocation.config_path(),
                root / "configs" / "release-1.2.dirpluck",
            )

    def test_named_invocation_entries_are_supported(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation.release]
                targets = ["./app/"]
                case = "publish"
                """,
            )
            template = load_invocation(manifest)
            self.assertTrue(template.select().is_empty)
            release = template.select("release")
            self.assertEqual(release.targets, ("./app/",))
            self.assertEqual(release.case, CaseSelection(pluck="publish"))

    def test_invocation_field_names_are_reserved_as_entry_names(self):
        for name in ("config", "targets", "case", "archive_mtime"):
            with self.subTest(name=name), resolved_temporary_directory() as temp:
                manifest = self._write(
                    Path(temp) / "release.dirpluck-inv",
                    f"""
                    [invocation.{name}]
                    value = "x"
                    """,
                )
                with self.assertRaisesRegex(
                    InvocationError,
                    rf"invocation entry name '{name}' is reserved",
                ):
                    load_invocation(manifest)

    def test_archive_mtime_is_supported_by_default_and_named_invocations(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                archive_mtime = "zip-epoch"

                [invocation.snapshot]
                archive_mtime = "now"
                """,
            )
            template = load_invocation(manifest)
            self.assertEqual(template.select().archive_mtime, "zip-epoch")
            self.assertFalse(template.select().is_empty)
            self.assertEqual(template.select("snapshot").archive_mtime, "now")

    def test_invalid_archive_mtime_is_rejected(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                archive_mtime = "1970-01-01T00:00:00"
                """,
            )
            with self.assertRaisesRegex(InvocationError, "archive mtime timestamp must be within"):
                load_invocation(manifest)

    def test_named_invocation_does_not_inherit_default_fields(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                config = "shared.dirpluck"
                case = "default-case"

                [invocation.release]
                targets = ["./app/"]
                """,
            )
            template = load_invocation(manifest)
            release = template.select("release")
            self.assertIsNone(release.config)
            self.assertEqual(release.targets, ("./app/",))
            self.assertIsNone(release.case)

    def test_unknown_invocation_entry_is_rejected_on_selection(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(Path(temp) / "release.dirpluck-inv", "[invocation]\n")
            template = load_invocation(manifest)
            with self.assertRaisesRegex(InvocationError, "invocation entry was not found: missing"):
                template.select("missing")

    def test_named_entry_accepts_same_fields_as_default(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            manifest = self._write(
                root / "release.dirpluck-inv",
                """
                [invocation.release]
                config = "release.dirpluck"
                targets = ["./app/"]
                case = "publish"
                """,
            )
            invocation = load_invocation(manifest).select("release")
            self.assertEqual(invocation.config, "release.dirpluck")
            self.assertEqual(invocation.targets, ("./app/",))
            self.assertEqual(invocation.case, CaseSelection(pluck="publish"))
            self.assertEqual(invocation.config_path(), (root / "release.dirpluck").resolve())

    def test_nested_table_inside_named_entry_is_rejected(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation.release.extra]
                value = true
                """,
            )
            with self.assertRaisesRegex(InvocationError, "unknown key.*extra"):
                load_invocation(manifest)

    def test_unknown_top_level_table_is_rejected(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                targets = ["./app/"]

                [other]
                value = true
                """,
            )
            with self.assertRaisesRegex(InvocationError, "unknown key.*other"):
                load_invocation(manifest)

    def test_targets_must_be_non_empty_strings(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                targets = [""]
                """,
            )
            with self.assertRaisesRegex(InvocationError, "expected a non-empty string"):
                load_invocation(manifest)

    def test_case_accepts_two_axis_selector_syntax(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                case = "review.release"

                [invocation.always-only]
                case = ".release"
                """,
            )
            template = load_invocation(manifest)
            self.assertEqual(
                template.select().case,
                CaseSelection(pluck="review", always="release"),
            )
            self.assertEqual(
                template.select("always-only").case,
                CaseSelection(always="release"),
            )

    def test_invalid_case_selector_syntax_is_rejected(self):
        for value in (".", "review.", "a.b.c"):
            with self.subTest(value=value), resolved_temporary_directory() as temp:
                manifest = self._write(
                    Path(temp) / "release.dirpluck-inv",
                    f"""
                    [invocation]
                    case = {value!r}
                    """,
                )
                with self.assertRaisesRegex(InvocationError, "PLUCK, .ALWAYS, or PLUCK.ALWAYS"):
                    load_invocation(manifest)

    def test_case_must_be_non_empty_when_present(self):
        with resolved_temporary_directory() as temp:
            manifest = self._write(
                Path(temp) / "release.dirpluck-inv",
                """
                [invocation]
                case = "   "
                """,
            )
            with self.assertRaisesRegex(InvocationError, "expected a non-empty string"):
                load_invocation(manifest)

    def test_document_suffix_is_required(self):
        with resolved_temporary_directory() as temp:
            path = self._write(Path(temp) / "release.toml", "[invocation]\n")
            with self.assertRaisesRegex(
                InvocationError,
                "invocation template file must end with '.dirpluck-inv'",
            ):
                load_invocation(path)

    def test_relative_template_path_is_resolved_from_cwd(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            nested = self._write(
                root / "invocations" / "release.dirpluck-inv",
                "[invocation]\n",
            )
            self.assertEqual(
                resolve_invocation_path("invocations/release", cwd=root),
                nested.resolve(),
            )

    def test_parent_relative_template_path_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            cwd = root / "workspace"
            cwd.mkdir()
            path = self._write(root / "shared" / "release.dirpluck-inv", "[invocation]\n")
            self.assertEqual(
                resolve_invocation_path("../shared/release", cwd=cwd),
                path.resolve(),
            )

    def test_absolute_template_path_is_supported(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            path = self._write(root / "shared" / "release.dirpluck-inv", "[invocation]\n")
            self.assertEqual(
                resolve_invocation_path(path.with_suffix("").as_posix(), cwd=root),
                path.resolve(),
            )

    def test_template_path_may_include_suffix(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            path = self._write(root / f"release{INVOCATION_SUFFIX}", "[invocation]\n")
            self.assertEqual(
                resolve_invocation_path(f"release{INVOCATION_SUFFIX}", cwd=root),
                path.resolve(),
            )

    def test_template_path_may_contain_dots_without_suffix(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            path = self._write(root / "set-2.1.dirpluck-inv", "[invocation]\n")
            self.assertEqual(resolve_invocation_path("set-2.1", cwd=root), path.resolve())

    def test_template_path_must_name_one_document(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for reference in (".", "..", "invocations/"):
                with (
                    self.subTest(reference=reference),
                    self.assertRaisesRegex(
                        InvocationError,
                        "must name one Invocation Template file",
                    ),
                ):
                    resolve_invocation_path(reference, cwd=root)

    def test_template_path_allows_symbolic_link_document_and_uses_link_location(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            real = self._write(
                shared / "release.dirpluck-inv",
                """
                [invocation]
                config = "release"
                """,
            )
            (root / "release.dirpluck").write_text("", encoding="utf-8")
            link = root / "release.dirpluck-inv"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            selected = resolve_invocation_path("release", cwd=root)
            self.assertEqual(selected, link.absolute())
            template = load_invocation(selected)
            self.assertEqual(template.manifest, link.absolute())
            self.assertEqual(template.select().config_path(), root / "release.dirpluck")

    def test_template_path_allows_symbolic_link_directory_component(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            real = self._write(shared / "release.dirpluck-inv", "[invocation]\n")
            link = root / "templates"
            try:
                link.symlink_to(shared, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            selected = resolve_invocation_path("templates/release", cwd=root)
            self.assertEqual(selected, root / "templates" / "release.dirpluck-inv")
            self.assertEqual(load_invocation(selected).manifest, selected)
            self.assertEqual(selected.resolve(), real.resolve())

    @unittest.skipUnless(os.name == "nt", "Windows junction semantics are Windows-specific")
    def test_template_path_allows_windows_directory_junction_component(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            shared = root / "shared"
            self._write(shared / "release.dirpluck-inv", "[invocation]\n")
            junction = root / "templates"
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
            selected = resolve_invocation_path("templates/release", cwd=root)
            self.assertEqual(selected, root / "templates" / "release.dirpluck-inv")
            self.assertEqual(load_invocation(selected).manifest, selected)

    def test_invocation_config_allows_symbolic_link_path(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            real = root / "shared.dirpluck"
            real.write_text("", encoding="utf-8")
            link = root / "release.dirpluck"
            try:
                link.symlink_to(real)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are not available")
            manifest = self._write(
                root / "release.dirpluck-inv",
                """
                [invocation]
                config = "release"
                """,
            )
            invocation = load_invocation(manifest).select()
            config_path = invocation.config_path()
            self.assertIsNotNone(config_path)
            assert config_path is not None
            self.assertEqual(config_path, link.absolute())
            self.assertEqual(config_path.resolve(), real.resolve())

    def test_template_path_uses_filesystem_location_notation(self):
        with resolved_temporary_directory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(InvocationError, "use '/' as the path separator"):
                resolve_invocation_path(r"invocations\\release", cwd=root)
            with self.assertRaises(InvocationError):
                resolve_invocation_path("invocations/*.dirpluck-inv", cwd=root)


if __name__ == "__main__":
    unittest.main()
