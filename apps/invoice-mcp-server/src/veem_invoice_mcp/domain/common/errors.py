"""Shared error types."""


class ToolError(RuntimeError):
    """A deterministic, user-facing tool error."""

    def __init__(self, message: str, *, code: str = "TOOL_ERROR", details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
