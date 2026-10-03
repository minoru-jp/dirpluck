import unittest

import dirpluck


class PublicInterfaceTests(unittest.TestCase):
    def test_package_root_exports_only_the_supported_python_api(self):
        self.assertEqual(
            set(dirpluck.__all__),
            {"ConfigurationDeprecationWarning", "DirpluckError", "RunResult", "__version__", "run"},
        )

    def test_configuration_deprecation_warning_is_visible_warning_category(self):
        self.assertIn(
            FutureWarning,
            dirpluck.ConfigurationDeprecationWarning.__mro__,
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
