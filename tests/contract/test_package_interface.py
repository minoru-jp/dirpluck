import unittest

import dirpluck


class PublicInterfaceTests(unittest.TestCase):
    def test_package_root_exports_the_core_python_api(self):
        self.assertTrue(
            {"DirpluckError", "RunResult", "__version__", "run"}.issubset(dirpluck.__all__)
        )

    def test_low_level_modules_are_not_reexported_from_package_root(self):
        for name in (
            "Always",
            "ArchivePlan",
            "BuildRequest",
            "Config",
            "InvocationTemplate",
            "Output",
            "Pluck",
            "ResolvedSource",
            "Scope",
            "Selection",
            "SelectionDefinition",
            "SharedPatterns",
            "build_archive",
            "build_archive_with_plan",
            "collect_files",
            "load_config",
            "load_invocation",
            "plan_archive",
            "resolve_sources",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(dirpluck, name))


if __name__ == "__main__":
    unittest.main()
