"""Expected errors raised by dirpluck."""


class DirpluckError(Exception):
    """Base class for expected dirpluck errors."""


class UsageError(DirpluckError):
    """Raised when one high-level invocation uses an invalid argument combination."""


class ConfigurationError(DirpluckError):
    """Raised when the dirpluck configuration is invalid."""


class SelectionError(DirpluckError):
    """Raised when configured directories cannot be resolved or extracted."""


class InvocationError(DirpluckError):
    """Raised when an Invocation Template cannot be selected or parsed."""
