"""Expected errors raised by dirpluck."""


class DirpluckError(Exception):
    """Base class for expected dirpluck errors."""


class ConfigurationError(DirpluckError):
    """Raised when the dirpluck configuration is invalid."""


class SelectionError(DirpluckError):
    """Raised when configured directories cannot be resolved or extracted."""
