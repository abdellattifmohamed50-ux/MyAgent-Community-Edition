class MyAgentError(Exception):
    """Base class for domain-aware application errors."""


class ProviderError(MyAgentError):
    """Raised when an AI provider fails or returns invalid data."""


class ProviderRequestError(ProviderError):
    """Provider transport failure classified for the retry policy."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class AuthenticationError(MyAgentError):
    """Raised when authentication fails."""


class AuthorizationError(MyAgentError):
    """Raised when a user lacks required permissions."""


class ToolExecutionError(MyAgentError):
    """Raised when a tool cannot execute safely."""


class RateLimitError(MyAgentError):
    """Raised when a caller exceeds limits."""


class ValidationError(MyAgentError):
    """Raised when input is structurally invalid."""
