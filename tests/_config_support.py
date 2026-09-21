from pathlib import Path
import textwrap
import unittest

from dirpluck.config import load_config


OUTPUT = '''
[output]
path = "out.zip"
overwrite = false
'''


class ConfigTestCase(unittest.TestCase):
    def _write(self, root: Path, text: str, *, add_output: bool = True) -> Path:
        body = textwrap.dedent(text)
        if add_output and "[output]" not in body:
            body += textwrap.dedent(OUTPUT)
        path = root / "default.dirpluck"
        path.write_text(body, encoding="utf-8")
        return path
