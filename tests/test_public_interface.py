import unittest

import dirpluck


class PublicInterfaceTests(unittest.TestCase):
    def test_package_root_does_not_reexport_python_internals(self):
        for name in (
            "BuildRequest",
            "Companion",
            "ConfigurationImport",
            "Config",
            "Output",
            "ResolvedSource",
            "Selection",
            "Target",
            "build_archive",
            "collect_files",
            "load_config",
            "resolve_sources",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(dirpluck, name))


if __name__ == "__main__":
    unittest.main()
