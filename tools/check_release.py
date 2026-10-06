from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Protocol, cast


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class _Arguments(Protocol):
    archive_only: bool


def _run(args: list[str | Path]) -> None:
    command = [str(arg) for arg in args]
    print("+", " ".join(command), flush=True)
    _ = subprocess.run(command, cwd=ROOT, check=True)


def _clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()


def _artifacts() -> tuple[Path, Path]:
    wheels = sorted(DIST.glob("*.whl"))
    sdists = sorted(DIST.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit(
            f"expected one wheel and one sdist in dist/, found {len(wheels)} wheel(s) and {len(sdists)} sdist(s)"
        )
    return wheels[0], sdists[0]


def _venv_paths(root: Path) -> tuple[Path, Path]:
    if sys.platform == "win32":
        scripts = root / "Scripts"
        return scripts / "python.exe", scripts / "dirpluck.exe"
    scripts = root / "bin"
    return scripts / "python", scripts / "dirpluck"


def _installed_wheel_smoke(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="dirpluck-release-") as raw_temp:
        env_root = Path(raw_temp) / "wheel-env"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python, cli = _venv_paths(env_root)
        _run([python, "-m", "pip", "install", "--no-deps", wheel])
        _run([python, "-m", "pip", "check"])
        _run([cli, "--version"])
        _run([python, "-c", "import dirpluck; print(dirpluck.__version__)"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and locally verify dirpluck release distributions."
    )
    _ = parser.add_argument(
        "--archive-only",
        action="store_true",
        help="build and inspect wheel/sdist without installing the wheel into a temporary environment",
    )
    args = cast(_Arguments, cast(object, parser.parse_args()))

    _run([sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "tools"])
    _run([sys.executable, "-m", "ruff", "check", "."])
    _run([sys.executable, "-m", "basedpyright", "--pythonpath", sys.executable])
    _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"])
    _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    _run([sys.executable, "tools/render_canonical_docs.py", "--check"])
    _run([sys.executable, "tools/check_published_docs.py"])
    _clean_dist()
    _run([sys.executable, "-m", "build"])
    wheel, sdist = _artifacts()
    _run([sys.executable, "-m", "twine", "check", wheel, sdist])
    _run([sys.executable, "tools/verify_distribution_contents.py"])
    if not args.archive_only:
        _installed_wheel_smoke(wheel)

    print(f"release distributions verified: {wheel.name}, {sdist.name}")


if __name__ == "__main__":
    main()
