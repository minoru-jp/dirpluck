from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "devdocs" / "config" / "context.json"


def current_version() -> str:
    sys.path.insert(0, str(SRC))
    try:
        from dirpluck import __version__
    finally:
        _ = sys.path.pop(0)
    return __version__


def main() -> None:
    payload = {"version": current_version()}
    _ = OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"document context generated: {OUTPUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
