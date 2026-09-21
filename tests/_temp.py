from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import tempfile


@contextmanager
def resolved_temporary_directory() -> Iterator[str]:
    """Yield a temporary directory through its symlink-free absolute path."""
    with tempfile.TemporaryDirectory() as temp:
        yield str(Path(temp).resolve())
