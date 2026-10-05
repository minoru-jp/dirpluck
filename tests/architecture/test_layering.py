from __future__ import annotations

import ast
from pathlib import Path
import unittest


PACKAGE = Path(__file__).parents[2] / "src" / "dirpluck"


def _relative_imports(module: str) -> set[str]:
    tree = ast.parse((PACKAGE / f"{module}.py").read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is not None:
            imports.add(f"_{node.module.removeprefix('_')}")
    return imports


class LayeringTests(unittest.TestCase):
    def test_configuration_parsing_does_not_depend_on_compilation(self):
        parsing_modules = {
            "_config_models",
            "_config_parser",
            "_config_values",
        }
        forbidden = {
            "_configuration_compiler",
            "_normalization",
            "_selection_normalization",
            "_extraction",
            "_source_resolution",
            "_target_resolution",
            "_archive",
            "_output",
        }
        for module in parsing_modules:
            with self.subTest(module=module):
                self.assertFalse(_relative_imports(module) & forbidden)

    def test_frontends_do_not_depend_on_configuration_value_grammar(self):
        frontend_modules = {"_application", "cli", "invocation"}
        for module in frontend_modules:
            with self.subTest(module=module):
                self.assertNotIn("_config_values", _relative_imports(module))

    def test_normalization_layer_does_not_depend_on_filesystem_execution(self):
        normalization_modules = {
            "_configuration_compiler",
            "_normalization",
            "_selection_normalization",
            "_target_syntax",
        }
        forbidden = {
            "_archive",
            "_archive_models",
            "_extraction",
            "_output",
            "_selection",
            "_source_resolution",
            "_target_resolution",
        }
        for module in normalization_modules:
            with self.subTest(module=module):
                self.assertFalse(_relative_imports(module) & forbidden)

    def test_zip_writer_depends_on_archive_payload_not_rendered_plan(self):
        imports = _relative_imports("_output")
        self.assertIn("_archive_payload", imports)
        self.assertNotIn("_archive_models", imports)
        self.assertNotIn("_extraction_models", imports)

    def test_extraction_layer_does_not_depend_on_input_language_modules(self):
        extraction_modules = {
            "_target_resolution",
            "_source_resolution",
            "_selection",
            "_extraction",
        }
        forbidden = {
            "_application",
            "_case",
            "_compatibility",
            "_config_models",
            "_config_parser",
            "_config_values",
            "_configuration_compiler",
            "_invocation",
            "_normalization",
            "_request_models",
            "_archive_models",
            "_output_models",
            "_selection_normalization",
            "_target_syntax",
        }
        for module in extraction_modules:
            with self.subTest(module=module):
                self.assertFalse(_relative_imports(module) & forbidden)

    def test_output_layer_does_not_call_input_or_extraction_processors(self):
        output_modules = {"_archive", "_output"}
        forbidden = {
            "_application",
            "_case",
            "_compatibility",
            "_config_models",
            "_config_parser",
            "_config_values",
            "_configuration_compiler",
            "_extraction",
            "_extraction_spec",
            "_invocation",
            "_normalization",
            "_request_models",
            "_resolution_models",
            "_selection",
            "_selection_normalization",
            "_source_resolution",
            "_target_resolution",
        }
        for module in output_modules:
            with self.subTest(module=module):
                self.assertFalse(_relative_imports(module) & forbidden)


if __name__ == "__main__":
    unittest.main()
