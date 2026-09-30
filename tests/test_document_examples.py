from __future__ import annotations

import re

import ast
from dataclasses import fields
import inspect
from inspect import cleandoc
from pathlib import Path
import tomllib
import unittest

from _temp import resolved_temporary_directory

import dirpluck


ROOT = Path(__file__).resolve().parents[1]
API_SOURCES = ROOT / "devdocs" / "canonical_sources" / "python_api"
CLI_SOURCES = ROOT / "devdocs" / "canonical_sources" / "cli"
CONFIGURATION_SOURCES = ROOT / "devdocs" / "canonical_sources" / "configuration"
GETTING_STARTED_SOURCE = ROOT / "devdocs" / "canonical_sources" / "getting_started" / "canonical.py"
README_SOURCE = ROOT / "devdocs" / "canonical_sources" / "readme" / "canonical.py"


def _test_target_fields(path: Path) -> dict[str, tuple[str | None, list[str]]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    languages: dict[str, str | None] = {}
    values: dict[str, list[str]] = {}

    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.Call):
            continue
        if getattr(node.value.func, "id", None) != "test_target_field":
            continue
        name = target.id
        match = re.search(
            rf"```([^\n]*)\n[ \t]*\{{\{{{re.escape(name)}\}}\}}[ \t]*\n[ \t]*```",
            source,
        )
        languages[name] = match.group(1).strip() if match else None
        values[name] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.AugAssign) or not isinstance(node.op, ast.MatMult):
            continue
        if not isinstance(node.target, ast.Name) or node.target.id not in languages:
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            values[node.target.id].append(cleandoc(node.value.value))

    return {name: (languages[name], values[name]) for name in languages}


class DocumentExampleTests(unittest.TestCase):
    def test_python_test_targets_are_valid_python_syntax(self):
        checked = 0
        for path in sorted(API_SOURCES.glob("*.py")):
            if path.name == "__init__.py":
                continue
            for name, (language, snippets) in _test_target_fields(path).items():
                if language != "python":
                    continue
                for snippet in snippets:
                    with self.subTest(source=path.name, field=name):
                        ast.parse(snippet)
                    checked += 1
        self.assertGreaterEqual(checked, 8)

    def test_configuration_toml_test_targets_are_valid_toml(self):
        checked = 0
        sources = [
            *sorted(CONFIGURATION_SOURCES.glob("*.py")),
            GETTING_STARTED_SOURCE,
            README_SOURCE,
        ]
        for source in sources:
            if source.name == "__init__.py":
                continue
            for name, (language, snippets) in _test_target_fields(source).items():
                if language != "toml":
                    continue
                for snippet in snippets:
                    with self.subTest(source=source.name, field=name):
                        tomllib.loads(snippet)
                    checked += 1
        self.assertGreaterEqual(checked, 22)

    def test_readme_llm_context_configuration_is_executable(self):
        snippets = _test_target_fields(README_SOURCE)["readme_llm_context_configuration"][1]
        self.assertEqual(len(snippets), 1)
        configuration = snippets[0]

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            (root / "framework-core" / "dist").mkdir(parents=True)
            (root / "docs-builder" / "dist").mkdir(parents=True)
            for repository in ("service-api", "worker-jobs", "web-console"):
                project = root / "repositories" / repository
                (project / "src").mkdir(parents=True)
                (project / "private" / "local-notes").mkdir(parents=True)
                (project / ".tmp").mkdir(parents=True)
                (project / "README.md").write_text(repository + "\n", encoding="utf-8")
                (project / "src" / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
                (project / ".env.local").write_text("SECRET=example\n", encoding="utf-8")
                (project / "private" / "local-notes" / "notes.txt").write_text(
                    "local notes\n", encoding="utf-8"
                )
                (project / ".tmp" / "proposed-changes.patch").write_text(
                    "diff --git a/src/main.py b/src/main.py\n", encoding="utf-8"
                )

            (root / "framework-core" / "dist" / "framework_core-2.4.0-py3-none-any.whl").write_bytes(b"wheel")
            (root / "docs-builder" / "dist" / "docs_builder-1.6.0-py3-none-any.whl").write_bytes(b"wheel")
            (root / "default.dirpluck").write_text(configuration + "\n", encoding="utf-8")

            result = dirpluck.run(
                "projects/service-api/",
                "projects/web-console/",
                preview=True,
                cwd=root,
            )

            self.assertIsNone(result.output_path)
            self.assertFalse((root / "develop-target.zip").exists())
            self.assertIn(
                "dependencies/framework-core/dist/framework_core-2.4.0-py3-none-any.whl",
                result.archive_entries,
            )
            self.assertIn(
                "tools/docs-builder/dist/docs_builder-1.6.0-py3-none-any.whl",
                result.archive_entries,
            )
            self.assertIn("repositories/service-api/README.md", result.archive_entries)
            self.assertIn("repositories/web-console/README.md", result.archive_entries)
            self.assertNotIn("repositories/worker-jobs/README.md", result.archive_entries)
            self.assertFalse(any(".env" in entry for entry in result.archive_entries))
            self.assertFalse(any("private/local-notes" in entry for entry in result.archive_entries))
            self.assertFalse(any("/.tmp/" in entry for entry in result.archive_entries))

            diff_result = dirpluck.run(
                "projects/service-api/",
                case="diff",
                preview=True,
                cwd=root,
            )
            self.assertIn(
                "repositories/service-api/.tmp/proposed-changes.patch",
                diff_result.archive_entries,
            )
            self.assertNotIn("repositories/worker-jobs/README.md", diff_result.archive_entries)
            self.assertNotIn("repositories/web-console/README.md", diff_result.archive_entries)
            self.assertFalse(any(".env" in entry for entry in diff_result.archive_entries))
            self.assertFalse(any("private/local-notes" in entry for entry in diff_result.archive_entries))
            self.assertIn(
                ".tmp/ に評価してほしい差分が含まれています。",
                diff_result.archive_readme,
            )

    def test_cli_console_test_targets_are_commands(self):
        checked = 0
        for source in sorted(CLI_SOURCES.glob("*.py")):
            if source.name == "__init__.py":
                continue
            for name, (language, snippets) in _test_target_fields(source).items():
                if language != "console":
                    continue
                for snippet in snippets:
                    with self.subTest(source=source.name, field=name):
                        commands = [line.strip() for line in snippet.splitlines() if line.strip()]
                        self.assertTrue(commands)
                        self.assertTrue(all(command.startswith("dirpluck") for command in commands))
                    checked += 1
        self.assertGreaterEqual(checked, 15)

    def test_documented_run_signature_tracks_public_run_parameters(self):
        snippets = _test_target_fields(API_SOURCES / "run.py")["run_signature"][1]
        self.assertEqual(len(snippets), 1)
        expression = ast.parse(snippets[0]).body[0]
        self.assertIsInstance(expression, ast.Expr)
        call = expression.value
        self.assertIsInstance(call, ast.Call)

        documented = []
        for argument in call.args:
            if isinstance(argument, ast.Starred) and isinstance(argument.value, ast.Name):
                documented.append(argument.value.id)
        documented.extend(keyword.arg for keyword in call.keywords if keyword.arg is not None)

        actual = list(inspect.signature(dirpluck.run).parameters)
        self.assertEqual(documented, actual)

    def test_documented_run_result_fields_track_public_dataclass(self):
        snippets = _test_target_fields(API_SOURCES / "result.py")["result_fields"][1]
        self.assertEqual(len(snippets), 1)
        documented = [line.split()[0] for line in snippets[0].splitlines() if line.strip()]
        actual = [field.name for field in fields(dirpluck.RunResult)]
        self.assertEqual(documented, actual)

    def test_documented_package_exports_exist(self):
        snippets = _test_target_fields(API_SOURCES / "surface.py")["package_exports"][1]
        self.assertEqual(len(snippets), 1)
        statement = ast.parse(snippets[0]).body[0]
        self.assertIsInstance(statement, ast.ImportFrom)
        names = [alias.name for alias in statement.names]
        self.assertEqual(names, ["ConfigurationDeprecationWarning", "DirpluckError", "RunResult", "__version__", "run"])
        for name in names:
            self.assertTrue(hasattr(dirpluck, name), name)


if __name__ == "__main__":
    unittest.main()
