from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import json
import re
import tomllib
from tempfile import TemporaryDirectory
from typing import cast
import unittest

from dirpluck import __version__
from tools.check_published_docs import document_digest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SOURCES = ROOT / "devdocs" / "canonical_sources"
CANONICAL_DOCUMENTS = ROOT / "devdocs" / "canonical_documents"
REPOSITORY_URL = "https://github.com/minoru-jp/dirpluck"

CHANGELOG_DOCUMENTS = {
    "INDEX.md",
    "0.9.x.md",
    "0.1-0.8.md",
}
SPECIFICATION_DOCUMENTS = {
    "INDEX.md",
    "overview.md",
    "document-selection.md",
    "configuration-schema.md",
    "paths.md",
    "composition.md",
    "runtime-targets.md",
    "namespace.md",
    "selection.md",
    "filesystem.md",
    "archive.md",
    "output.md",
    "preview.md",
    "cli-contract.md",
    "compatibility.md",
}
CONFIGURATION_DOCUMENTS = {
    "INDEX.md",
    "overview.md",
    "sources.md",
    "selection.md",
    "composition.md",
    "output.md",
    "examples.md",
}
CLI_DOCUMENTS = {
    "INDEX.md",
    "overview.md",
    "invocation-templates.md",
    "targets.md",
    "output.md",
}
RECIPE_DOCUMENTS = {
    "INDEX.md",
    "llm-development-environment.md",
    "workspace-project-selection.md",
    "team-shared-configuration.md",
}
PYTHON_API_DOCUMENTS = {
    "INDEX.md",
    "overview.md",
    "run.md",
    "result.md",
    "errors.md",
    "surface.md",
}
EXPECTED_DOCUMENTS = {
    "README.md",
    "GLOSSARY.md",
    "CHANGELOG.md",
    "STATUS.md",
    "docs/GETTING_STARTED.md",
    "docs/migration/0.16.md",
    "docs/migration/0.17.md",
    *(f"docs/changelog/{name}" for name in CHANGELOG_DOCUMENTS),
    *(f"docs/cli/{name}" for name in CLI_DOCUMENTS),
    *(f"docs/configuration/{name}" for name in CONFIGURATION_DOCUMENTS),
    *(f"docs/recipes/{name}" for name in RECIPE_DOCUMENTS),
    "docs/TRUST.md",
    "devdocs/README.md",
    *(f"docs/specification/{name}" for name in SPECIFICATION_DOCUMENTS),
    *(f"docs/python_api/{name}" for name in PYTHON_API_DOCUMENTS),
}
CANONICAL_SOURCE = re.compile(r"正本は `([^`]+)` です。")


class DocumentBuildTests(unittest.TestCase):
    def test_japanese_canonical_document_paths_are_canonical(self):
        actual = {
            path.relative_to(CANONICAL_DOCUMENTS).as_posix()
            for path in CANONICAL_DOCUMENTS.rglob("*.md")
        }
        self.assertEqual(actual, EXPECTED_DOCUMENTS)
        self.assertNotIn("USAGE.md", actual)
        self.assertNotIn("docs/SPECIFICATION.md", actual)
        self.assertNotIn("docs/PYTHON_API.md", actual)
        self.assertNotIn("docs/CONFIGURATION.md", actual)

    def test_japanese_canonical_document_notices_use_portable_source_paths(self):
        for relative in sorted(EXPECTED_DOCUMENTS):
            with self.subTest(document=relative):
                text = (CANONICAL_DOCUMENTS / relative).read_text(encoding="utf-8")
                match = CANONICAL_SOURCE.search(text)
                self.assertIsNotNone(match)
                assert match is not None
                canonical = match.group(1)
                self.assertTrue(canonical.startswith("devdocs/canonical_sources/"), canonical)
                self.assertFalse(PurePosixPath(canonical).is_absolute(), canonical)
                windows_path = PureWindowsPath(canonical)
                self.assertFalse(windows_path.is_absolute(), canonical)
                self.assertFalse(windows_path.drive, canonical)

    def test_canonical_sources_use_direct_vocabulary_references(self):
        self.assertTrue((ROOT / "devdocs" / "__init__.py").is_file())
        self.assertTrue((CANONICAL_SOURCES / "__init__.py").is_file())
        self.assertFalse((CANONICAL_SOURCES / "terms.py").exists())

        for source in CANONICAL_SOURCES.rglob("*.py"):
            if source.name == "__init__.py" or source.parent.name == "vocabulary":
                continue
            text = source.read_text(encoding="utf-8")
            with self.subTest(source=source.relative_to(ROOT).as_posix()):
                if "{{TERM_" in text:
                    self.assertIn(
                        "from devdocs.canonical_sources.vocabulary.canonical import TERMS",
                        text,
                    )
                    self.assertIn("merge @= TERMS.TERM_", text)
                self.assertNotIn("from canonical_documents import terms", text)
                self.assertNotIn("vocabulary_refs", text)
                self.assertNotIn("dirpluck_docs", text)

    def test_vocabulary_uses_canonical_term_classes(self):
        canonical = (CANONICAL_SOURCES / "vocabulary" / "canonical.py").read_text(encoding="utf-8")
        self.assertIn("@vocabulary", canonical)
        self.assertIn("@canonical_source", canonical)
        self.assertIn("class TERM_1:", canonical)
        self.assertNotIn("@term(", canonical)
        self.assertNotIn("glossary @= True", canonical)

    def test_document_context_version_matches_package_version(self):
        context_path = ROOT / "devdocs" / "config" / "context.json"
        context = cast(dict[str, object], json.loads(context_path.read_text(encoding="utf-8")))
        self.assertEqual(context, {"version": __version__})

    def test_publication_digest_is_independent_of_markdown_line_endings(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            lf = root / "lf.md"
            crlf = root / "crlf.md"
            lf.write_bytes(b"# Title\n\nBody\n")
            crlf.write_bytes(b"# Title\r\n\r\nBody\r\n")
            self.assertEqual(document_digest(lf), document_digest(crlf))

    def test_publication_manifest_tracks_canonical_and_public_documents(self):
        manifest_path = ROOT / "devdocs" / "config" / "publication_manifest.json"
        manifest = cast(dict[str, object], json.loads(manifest_path.read_text(encoding="utf-8")))
        self.assertEqual(manifest.get("version"), 2)
        documents_raw = manifest.get("documents")
        self.assertIsInstance(documents_raw, dict)
        documents = cast(dict[str, object], documents_raw)
        self.assertEqual(set(documents), EXPECTED_DOCUMENTS)

        for relative in sorted(EXPECTED_DOCUMENTS):
            with self.subTest(document=relative):
                entry_raw = documents[relative]
                self.assertIsInstance(entry_raw, dict)
                entry = cast(dict[str, object], entry_raw)
                canonical = CANONICAL_DOCUMENTS / relative
                public = ROOT / relative
                self.assertTrue(public.is_file())
                self.assertEqual(entry.get("canonical_sha256"), document_digest(canonical))
                self.assertEqual(entry.get("public_sha256"), document_digest(public))
                public_text = public.read_text(encoding="utf-8")
                self.assertNotIn("shikumi-devdoc:translation-metadata", public_text)
                self.assertNotIn("この文書は自動生成された翻訳元", public_text)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"The current version is **{__version__}**.", readme)
        self.assertIn(f"## {__version__}", changelog)

    def test_published_document_snapshot_is_part_of_ci_and_release_checks(self):
        workflow = (ROOT / ".github" / "workflows" / "checks.yml").read_text(encoding="utf-8")
        release_check = (ROOT / "tools" / "check_release.py").read_text(encoding="utf-8")
        command = "tools/check_published_docs.py"
        self.assertIn(command, workflow)
        self.assertIn(command, release_check)

    def test_documentation_and_test_tooling_dependencies_are_explicit(self):
        with (ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)
        self.assertEqual(project["project"]["dependencies"], [])
        self.assertEqual(
            project["project"]["optional-dependencies"]["test"],
            ["shikumi-devdoc>=0.3.2"],
        )
        self.assertEqual(
            project["dependency-groups"]["docs"],
            ["shikumi-devdoc>=0.3.2"],
        )

    def test_project_urls_point_to_public_repository(self):
        with (ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)

        self.assertEqual(
            project["project"]["urls"],
            {
                "Homepage": REPOSITORY_URL,
                "Documentation": f"{REPOSITORY_URL}#documentation",
                "Repository": REPOSITORY_URL,
                "Issues": f"{REPOSITORY_URL}/issues",
                "Changelog": f"{REPOSITORY_URL}/blob/main/CHANGELOG.md",
            },
        )

    def test_root_readme_navigation_uses_public_absolute_urls(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        published_paths = (
            "docs/GETTING_STARTED.md",
            "docs/migration/0.16.md",
            "docs/migration/0.17.md",
            "GLOSSARY.md",
            "docs/configuration/INDEX.md",
            "docs/recipes/INDEX.md",
            "docs/cli/INDEX.md",
            "docs/python_api/INDEX.md",
            "docs/specification/INDEX.md",
            "docs/TRUST.md",
            "CHANGELOG.md",
            "STATUS.md",
            "LICENSE",
        )

        for relative in published_paths:
            with self.subTest(path=relative):
                url = f"{REPOSITORY_URL}/blob/main/{relative}"
                self.assertIn(url, readme)

        self.assertNotRegex(
            readme,
            r"\]\((?:docs/|GLOSSARY\.md|CHANGELOG\.md|STATUS\.md|LICENSE\))",
        )

    def test_distribution_uses_hatchling_and_full_public_docs(self):
        with (ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)

        self.assertEqual(project["build-system"]["build-backend"], "hatchling.build")
        self.assertEqual(project["build-system"]["requires"], ["hatchling>=1.27"])
        self.assertEqual(project["project"]["dynamic"], ["version"])
        self.assertEqual(
            project["tool"]["hatch"]["version"]["path"],
            "src/dirpluck/__init__.py",
        )
        self.assertEqual(
            project["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"],
            {
                "README.md": "dirpluck/_docs/README.md",
                "GLOSSARY.md": "dirpluck/_docs/GLOSSARY.md",
                "CHANGELOG.md": "dirpluck/_docs/CHANGELOG.md",
                "STATUS.md": "dirpluck/_docs/STATUS.md",
                "docs": "dirpluck/_docs/docs",
            },
        )
        self.assertEqual(
            project["tool"]["hatch"]["build"]["targets"]["sdist"]["exclude"],
            ["/.github"],
        )
        self.assertFalse((ROOT / "MANIFEST.in").exists())
        self.assertFalse((ROOT / "src" / "dirpluck.egg-info").exists())

    def test_vocabulary_does_not_define_current_release_version(self):
        canonical = (CANONICAL_SOURCES / "vocabulary" / "canonical.py").read_text(encoding="utf-8")
        self.assertNotIn(f"{{{{{__version__}}}}}", canonical)
        self.assertNotRegex(canonical, r'class TERM_\d+:\s+r?["\']{3}\{\{\d+\.\d+\.\d+\}\}')

    def test_readme_uses_external_version_context(self):
        canonical = (CANONICAL_SOURCES / "readme" / "canonical.py").read_text(encoding="utf-8")
        self.assertIn("{{version}}", canonical)
        self.assertNotIn("TERM_11", canonical)

    def test_changelog_cli_configuration_specification_and_python_api_are_collections(self):
        changelog_sources = {
            path.stem
            for path in (CANONICAL_SOURCES / "changelog" / "archive").glob("*.py")
            if path.name != "__init__.py"
        }
        cli_sources = {
            path.stem
            for path in (CANONICAL_SOURCES / "cli").glob("*.py")
            if path.name != "__init__.py"
        }
        spec_sources = {
            path.stem
            for path in (CANONICAL_SOURCES / "specification").glob("*.py")
            if path.name != "__init__.py"
        }
        api_sources = {
            path.stem
            for path in (CANONICAL_SOURCES / "python_api").glob("*.py")
            if path.name != "__init__.py"
        }
        recipe_sources = {
            path.stem
            for path in (CANONICAL_SOURCES / "recipes").glob("*.py")
            if path.name != "__init__.py"
        }
        configuration_sources = {
            path.stem
            for path in (CANONICAL_SOURCES / "configuration").glob("*.py")
            if path.name != "__init__.py"
        }
        self.assertNotIn("canonical", changelog_sources)
        self.assertEqual(changelog_sources, {"v0_9", "v0_1_to_0_8"})
        self.assertNotIn("canonical", cli_sources)
        self.assertNotIn("canonical", spec_sources)
        self.assertNotIn("canonical", api_sources)
        self.assertNotIn("canonical", configuration_sources)
        self.assertEqual(
            recipe_sources,
            {
                "llm_development_environment",
                "workspace_project_selection",
                "team_shared_configuration",
            },
        )
        self.assertGreaterEqual(len(cli_sources), 4)
        self.assertGreaterEqual(len(spec_sources), 10)
        self.assertGreaterEqual(len(api_sources), 5)
        self.assertGreaterEqual(len(configuration_sources), 6)

        for source in [
            *(CANONICAL_SOURCES / "changelog" / "archive").glob("*.py"),
            *(CANONICAL_SOURCES / "cli").glob("*.py"),
            *(CANONICAL_SOURCES / "configuration").glob("*.py"),
            *(CANONICAL_SOURCES / "recipes").glob("*.py"),
            *(CANONICAL_SOURCES / "specification").glob("*.py"),
            *(CANONICAL_SOURCES / "python_api").glob("*.py"),
        ]:
            if source.name == "__init__.py":
                continue
            text = source.read_text(encoding="utf-8")
            with self.subTest(source=source.relative_to(ROOT).as_posix()):
                self.assertIn("@summary(", text)
                self.assertIn("@canonical_source(", text)
                self.assertRegex(text, r"\border=\d+")

    def test_canonical_sources_use_current_shikumi_devdoc_authoring_contract(self):
        for source in CANONICAL_SOURCES.rglob("*.py"):
            if source.name == "__init__.py":
                continue
            text = source.read_text(encoding="utf-8")
            with self.subTest(source=source.relative_to(ROOT).as_posix()):
                self.assertNotRegex(text, r"(?m)^\s*@title\(")
                self.assertNotRegex(text, r"(?m)^\s*\w+\s*=\s*code_field\(")
                if "@canonical_source(" in text:
                    self.assertRegex(
                        text, r"(?s)@canonical_source\([^)]*heading=[\"'](?:title|identity)[\"']"
                    )

        for source in (CANONICAL_SOURCES / "specification").glob("*.py"):
            if source.name == "__init__.py":
                continue
            self.assertIn('heading="identity"', source.read_text(encoding="utf-8"))

    def test_split_specification_has_no_legacy_numbered_section_references(self):
        legacy_reference = re.compile(r"(?:\d+節|Section\s+\d+)")
        sources = sorted((CANONICAL_SOURCES / "specification").glob("*.py"))
        canonical_documents = sorted((CANONICAL_DOCUMENTS / "docs" / "specification").glob("*.md"))
        public_documents = sorted((ROOT / "docs" / "specification").glob("*.md"))

        for path in [*sources, *canonical_documents, *public_documents]:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(legacy_reference.search(text))

    def test_public_collections_replace_legacy_single_files(self):
        self.assertFalse((ROOT / "docs" / "CLI.md").exists())
        self.assertFalse((ROOT / "docs" / "SPECIFICATION.md").exists())
        self.assertFalse((ROOT / "docs" / "PYTHON_API.md").exists())
        self.assertFalse((ROOT / "docs" / "CONFIGURATION.md").exists())
        self.assertTrue((ROOT / "docs" / "changelog" / "INDEX.md").is_file())
        self.assertTrue((ROOT / "docs" / "cli" / "INDEX.md").is_file())
        self.assertTrue((ROOT / "docs" / "configuration" / "INDEX.md").is_file())
        self.assertTrue((ROOT / "docs" / "recipes" / "INDEX.md").is_file())
        self.assertTrue((ROOT / "docs" / "specification" / "INDEX.md").is_file())
        self.assertTrue((ROOT / "docs" / "python_api" / "INDEX.md").is_file())

    def test_changelog_keeps_current_history_at_root_and_archives_earlier_releases(self):
        current = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        archive_09 = (ROOT / "docs" / "changelog" / "0.9.x.md").read_text(encoding="utf-8")
        archive_early = (ROOT / "docs" / "changelog" / "0.1-0.8.md").read_text(encoding="utf-8")

        self.assertIn("## 0.10.0", current)
        self.assertNotIn("## 0.9.1", current)
        self.assertIn("docs/changelog/INDEX.md", current)

        self.assertIn("## 0.9.1", archive_09)
        self.assertIn("## 0.9.0", archive_09)
        self.assertNotIn("## 0.8.0", archive_09)

        self.assertIn("## 0.8.0", archive_early)
        self.assertIn("## 0.1.0", archive_early)
        self.assertNotIn("## 0.9.0", archive_early)

    def test_public_markdown_links_resolve_locally(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        heading_pattern = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)

        def github_fragment(heading: str) -> str:
            normalized = heading.strip().lower()
            normalized = "".join(
                character for character in normalized if character.isalnum() or character in "-_ "
            )
            return re.sub(r"\s+", "-", normalized)

        documents = [
            ROOT / "README.md",
            ROOT / "CHANGELOG.md",
            *sorted((ROOT / "docs").rglob("*.md")),
        ]
        checked = 0
        fragment_checked = 0
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for target in cast(list[str], link_pattern.findall(text)):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                path_part, separator, fragment = target.partition("#")
                resolved = document if not path_part else (document.parent / path_part).resolve()
                with self.subTest(document=document.relative_to(ROOT).as_posix(), target=target):
                    self.assertTrue(resolved.exists(), resolved)
                    if separator and fragment:
                        headings = {
                            github_fragment(match.group(1))
                            for match in heading_pattern.finditer(
                                resolved.read_text(encoding="utf-8")
                            )
                        }
                        self.assertIn(fragment, headings)
                        fragment_checked += 1
                checked += 1
        self.assertGreaterEqual(checked, 70)
        self.assertGreaterEqual(fragment_checked, 20)

    def test_public_collection_indexes_are_index_only(self):
        indexes = [
            ROOT / "docs" / "changelog" / "INDEX.md",
            ROOT / "docs" / "cli" / "INDEX.md",
            ROOT / "docs" / "configuration" / "INDEX.md",
            ROOT / "docs" / "specification" / "INDEX.md",
            ROOT / "docs" / "python_api" / "INDEX.md",
        ]
        for index in indexes:
            lines = [line for line in index.read_text(encoding="utf-8").splitlines() if line]
            with self.subTest(index=index.relative_to(ROOT).as_posix()):
                self.assertTrue(lines[0].startswith("# "))
                self.assertEqual(lines[1], "| Document | Summary |")
                self.assertEqual(lines[2], "| --- | --- |")
                self.assertTrue(all(line.startswith("|") for line in lines[1:]))

    def test_public_collection_index_links_match_canonical_indexes(self):
        collections = ["changelog", "cli", "configuration", "specification", "python_api"]
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
        for collection in collections:
            canonical = (CANONICAL_DOCUMENTS / "docs" / collection / "INDEX.md").read_text(
                encoding="utf-8"
            )
            public = (ROOT / "docs" / collection / "INDEX.md").read_text(encoding="utf-8")
            with self.subTest(collection=collection):
                self.assertEqual(
                    link_pattern.findall(public),
                    link_pattern.findall(canonical),
                )

    def test_compact_package_documentation_channel_is_removed(self):
        for name in ["package_cli", "package_configuration", "package_trust"]:
            self.assertFalse((CANONICAL_SOURCES / name).exists())
        self.assertFalse((CANONICAL_DOCUMENTS / "package").exists())
        self.assertFalse((ROOT / "src" / "dirpluck" / "docs").exists())

    def test_specification_uses_stable_rule_nodes_and_semantic_fields(self):
        seen: set[str] = set()
        for source in sorted((CANONICAL_SOURCES / "specification").glob("*.py")):
            if source.name == "__init__.py":
                continue
            text = source.read_text(encoding="utf-8")
            rule_ids = set(re.findall(r"\bclass (SPEC_\d{3}):", text))
            with self.subTest(source=source.relative_to(ROOT).as_posix()):
                self.assertTrue(rule_ids)
                self.assertIn("level @=", text)
                self.assertFalse(seen & rule_ids, seen & rule_ids)
            seen.update(rule_ids)

        self.assertGreaterEqual(len(seen), 150)

    def test_public_specification_exposes_the_same_rule_identities(self):
        source_ids: set[str] = set()
        for source in (CANONICAL_SOURCES / "specification").glob("*.py"):
            source_ids.update(
                re.findall(r"\bclass (SPEC_\d{3}):", source.read_text(encoding="utf-8"))
            )

        public_ids: set[str] = set()
        for document in (ROOT / "docs" / "specification").glob("*.md"):
            public_ids.update(
                re.findall(
                    r"^#{2,} (SPEC_\d{3})$", document.read_text(encoding="utf-8"), re.MULTILINE
                )
            )

        self.assertEqual(public_ids, source_ids)

    def test_public_specification_exposes_the_same_section_identities(self):
        source_ids: set[str] = set()
        for source in (CANONICAL_SOURCES / "specification").glob("*.py"):
            source_ids.update(
                re.findall(r"\bclass (SECTION_\d+):", source.read_text(encoding="utf-8"))
            )

        public_ids: set[str] = set()
        for document in (ROOT / "docs" / "specification").glob("*.md"):
            public_ids.update(
                re.findall(
                    r"^#{2,} (SECTION_\d+)$",
                    document.read_text(encoding="utf-8"),
                    re.MULTILINE,
                )
            )

        self.assertEqual(public_ids, source_ids)

    def test_public_specification_preserves_rule_levels(self):
        rendered_levels = {
            "MUST": "MUST",
            "MUST_NOT": "MUST NOT",
            "SHOULD": "SHOULD",
            "SHOULD_NOT": "SHOULD NOT",
            "MAY": "MAY",
            "INFORMATIVE": "INFORMATIVE",
        }
        source_levels: dict[str, str] = {}
        for source in (CANONICAL_SOURCES / "specification").glob("*.py"):
            text = source.read_text(encoding="utf-8")
            for rule_id, level_name in cast(
                list[tuple[str, str]],
                re.findall(
                    r"class (SPEC_\d{3}):.*?\n\s+level @= ([A-Z_]+)",
                    text,
                    re.DOTALL,
                ),
            ):
                source_levels[rule_id] = rendered_levels[level_name]

        public_levels: dict[str, str] = {}
        for document in (ROOT / "docs" / "specification").glob("*.md"):
            text = document.read_text(encoding="utf-8")
            for match in re.finditer(
                r"^#{2,} (SPEC_\d{3})$.*?^level: ([A-Z ]+)$",
                text,
                re.MULTILINE | re.DOTALL,
            ):
                public_levels[match.group(1)] = match.group(2)

        self.assertEqual(public_levels, source_levels)

    def test_python_api_examples_use_test_target_fields(self):
        api_root = CANONICAL_SOURCES / "python_api"
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(api_root.glob("*.py"))
            if path.name != "__init__.py"
        )
        self.assertNotRegex(combined, r"(?m)^\s*\w+\s*=\s*code_field\(")
        self.assertGreaterEqual(combined.count("test_target_field("), 10)
        self.assertIn("```python", combined)


if __name__ == "__main__":
    unittest.main()
