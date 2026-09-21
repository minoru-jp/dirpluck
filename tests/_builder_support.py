from pathlib import Path
import textwrap
import unittest

from dirpluck.config import load_config


CONFIG = r'''
[pluck]
description = "The project currently being worked on."
must = ["src", "README.md"]
ignore = ["generated/", "__pycache__/", ".DS_Store", "*.pyc"]

[always.framework]
path = "framework"
description = "A fixed framework needed with the target."
must = ["src", "README.md"]
ignore = ["generated/", "__pycache__/", ".DS_Store", "*.pyc"]
'''


class BuilderTestCase(unittest.TestCase):
    def _config(self, root: Path, text: str = CONFIG, *, output: str = "out.zip", overwrite: bool = False):
        body = textwrap.dedent(text)
        if "[pluck" in body and "[scope" not in body:
            body += "\n[scope]\n"
        if "[output]" not in body:
            body += f'\n[output]\npath = {output!r}\noverwrite = {str(overwrite).lower()}\n'
        manifest = root / "default.dirpluck"
        manifest.write_text(body, encoding="utf-8")
        return load_config(manifest)

    def _project(self, root: Path, relative: str, marker: str) -> Path:
        project = root / relative
        (project / "src" / "generated").mkdir(parents=True)
        (project / "src" / "nested" / "__pycache__").mkdir(parents=True)
        (project / "src" / "module.py").write_text(f"MARKER = {marker!r}\n", encoding="utf-8")
        (project / "src" / "nested" / "helper.py").write_text("HELPER = 1\n", encoding="utf-8")
        (project / "src" / "nested" / "cache.pyc").write_bytes(b"cache")
        (project / "src" / "nested" / "__pycache__" / "hidden.py").write_text("HIDDEN = 1\n", encoding="utf-8")
        (project / "src" / "generated" / "skip.py").write_text("SKIP = 1\n", encoding="utf-8")
        (project / "src" / ".DS_Store").write_text("metadata\n", encoding="utf-8")
        (project / "README.md").write_text(f"# {marker}\n", encoding="utf-8")
        (project / "notes.txt").write_text("not selected\n", encoding="utf-8")
        return project

