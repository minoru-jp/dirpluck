"""Public Python API for dirpluck."""

from ._application import RunResult, run
from .errors import DirpluckError
from ._warnings import AlwaysMigrationWarning, ConfigurationDeprecationWarning

__version__ = "0.18.0"

__all__ = [
    "AlwaysMigrationWarning",
    "ConfigurationDeprecationWarning",
    "DirpluckError",
    "RunResult",
    "__version__",
    "run",
]
