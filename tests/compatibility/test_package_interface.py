import unittest

import dirpluck


class Pre10PackageInterfaceCompatibilityTests(unittest.TestCase):
    def test_package_root_exposes_compatibility_warning_types(self):
        core = {"DirpluckError", "RunResult", "__version__", "run"}
        compatibility = {"AlwaysMigrationWarning", "ConfigurationDeprecationWarning"}
        self.assertEqual(set(dirpluck.__all__), core | compatibility)

    def test_configuration_deprecation_warning_is_visible_warning_category(self):
        self.assertIn(FutureWarning, dirpluck.ConfigurationDeprecationWarning.__mro__)

    def test_always_migration_warning_is_visible_warning_category(self):
        self.assertIn(FutureWarning, dirpluck.AlwaysMigrationWarning.__mro__)
