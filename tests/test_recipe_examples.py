from __future__ import annotations

from pathlib import Path
import unittest

import dirpluck

from tests._temp import resolved_temporary_directory
from tests.test_document_examples import _test_target_fields


ROOT = Path(__file__).resolve().parents[1]
RECIPE_SOURCES = ROOT / "devdocs" / "canonical_sources" / "recipes"


def _snippet(source_name: str, field: str) -> str:
    snippets = _test_target_fields(RECIPE_SOURCES / source_name)[field][1]
    if len(snippets) != 1:
        raise AssertionError(f"expected exactly one {field!r} snippet in {source_name}")
    return snippets[0]


def _write(path: Path, text: str = "example\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class RecipeExampleTests(unittest.TestCase):
    def test_llm_environment_recipe_switches_offline_wheels_with_always_case(self):
        configuration = _snippet("llm_development_environment.py", "configuration_example")

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            project = root / "project"
            _write(project / "README.md")
            _write(project / "pyproject.toml")
            _write(project / "src" / "main.py")
            _write(project / "tests" / "test_main.py")
            _write(project / ".git" / "config")
            _write(project / ".venv" / "pyvenv.cfg")
            _write(root / "offline_wheels" / "shikumi-0.2.4-py3-none-any.whl", "wheel")
            _write(root / "offline_wheels" / "shikumi_devdoc-0.3.5-py3-none-any.whl", "wheel")
            _write(root / "offline_wheels" / "basedpyright-1.40.1-py3-none-any.whl", "wheel")
            _write(root / "offline_wheels" / "ruff-0.16.10-py3-none-any.whl", "wheel")
            _write(root / "default.dirpluck", configuration)

            offline = dirpluck.run("./project/", preview=True, cwd=root)
            self.assertIn(
                "offline_wheels/shikumi-0.2.4-py3-none-any.whl",
                offline.archive_entries,
            )
            self.assertIn("project/src/main.py", offline.archive_entries)
            self.assertFalse(any("/.git/" in entry for entry in offline.archive_entries))
            self.assertFalse(any("/.venv/" in entry for entry in offline.archive_entries))
            self.assertIn("If the Python package index is unavailable", offline.archive_readme)

            online = dirpluck.run("./project/", case=".claude", preview=True, cwd=root)
            self.assertFalse(
                any(entry.startswith("offline_wheels/") for entry in online.archive_entries)
            )
            self.assertIn("project/src/main.py", online.archive_entries)

    def test_workspace_recipe_target_forms_select_the_expected_projects(self):
        configuration = _snippet("workspace_project_selection.py", "configuration_example")

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            for name in ("service-api", "web-console", "worker-jobs"):
                project = root / "projects" / name
                _write(project / "README.md", name + "\n")
                _write(project / "pyproject.toml")
                _write(project / "src" / "main.py")
                _write(project / "tests" / "test_main.py")
            _write(root / "projects" / "scratch" / "notes.txt")
            _write(root / "default.dirpluck", configuration)

            one = dirpluck.run("projects/service-api/", preview=True, cwd=root)
            self.assertIn("repositories/service-api/README.md", one.archive_entries)
            self.assertNotIn("repositories/web-console/README.md", one.archive_entries)

            separate = dirpluck.run(
                "projects/service-api/",
                "projects/web-console/",
                preview=True,
                cwd=root,
            )
            listed = dirpluck.run(
                "projects:[service-api//web-console/]",
                preview=True,
                cwd=root,
            )
            regex = dirpluck.run(
                "projects:<.*-(api|console)/>",
                preview=True,
                cwd=root,
            )
            expected = {
                "repositories/service-api/README.md",
                "repositories/web-console/README.md",
            }
            for result in (separate, listed, regex):
                self.assertTrue(expected.issubset(result.archive_entries))
                self.assertNotIn("repositories/worker-jobs/README.md", result.archive_entries)
                self.assertFalse(any("scratch" in entry for entry in result.archive_entries))

            whole = dirpluck.run("projects/", preview=True, cwd=root)
            self.assertIn("repositories/service-api/README.md", whole.archive_entries)
            self.assertIn("repositories/web-console/README.md", whole.archive_entries)
            self.assertIn("repositories/worker-jobs/README.md", whole.archive_entries)
            self.assertFalse(any("scratch" in entry for entry in whole.archive_entries))

    def test_team_shared_recipe_inherits_policy_and_expands_full_case(self):
        base_configuration = _snippet("team_shared_configuration.py", "base_configuration")
        root_configuration = _snippet("team_shared_configuration.py", "root_configuration")

        with resolved_temporary_directory() as temp:
            root = Path(temp)
            _write(root / "common" / "common.dirpluck", base_configuration)
            _write(root / "common" / "team_guidelines" / "REVIEW.md")
            _write(root / "common" / "team_guidelines" / "SECURITY.md")
            _write(root / "default.dirpluck", root_configuration)

            project = root / "project"
            _write(project / "README.md")
            _write(project / "pyproject.toml")
            _write(project / "src" / "main.py")
            _write(project / "tests" / "test_main.py")
            _write(project / "docs" / "guide.md")
            _write(project / "examples" / "demo.py")
            _write(project / ".git" / "config")
            _write(project / ".venv" / "pyvenv.cfg")
            _write(project / "src" / "__pycache__" / "main.cpython-313.pyc")

            review = dirpluck.run("./project/", preview=True, cwd=root)
            self.assertIn("project/README.md", review.archive_entries)
            self.assertIn("project/pyproject.toml", review.archive_entries)
            self.assertIn("project/src/main.py", review.archive_entries)
            self.assertIn("project/tests/test_main.py", review.archive_entries)
            self.assertNotIn("project/docs/guide.md", review.archive_entries)
            self.assertNotIn("project/examples/demo.py", review.archive_entries)
            self.assertIn("team_guidelines/REVIEW.md", review.archive_entries)
            self.assertIn("team_guidelines/SECURITY.md", review.archive_entries)
            self.assertFalse(any("/.git/" in entry for entry in review.archive_entries))
            self.assertFalse(any("/.venv/" in entry for entry in review.archive_entries))
            self.assertFalse(any("__pycache__" in entry for entry in review.archive_entries))
            self.assertIn("Package prepared for review", review.archive_readme)

            full = dirpluck.run("./project/", case="full", preview=True, cwd=root)
            self.assertIn("project/docs/guide.md", full.archive_entries)
            self.assertIn("project/examples/demo.py", full.archive_entries)
            self.assertIn("team_guidelines/REVIEW.md", full.archive_entries)
            self.assertIn(
                "Full review package including documentation and examples", full.archive_readme
            )


if __name__ == "__main__":
    unittest.main()
