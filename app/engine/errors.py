"""Typed errors. All are ValueErrors, so a caller can catch either."""


class EngineError(ValueError):
    """Base class for every error the engine raises on purpose."""


class InvalidAccountIdError(EngineError):
    """reason is 'not_digits' or 'not_found'. value is what the caller passed."""

    def __init__(self, value, reason, message):
        super().__init__(message)
        self.value = value
        self.reason = reason


class InvalidShockError(EngineError):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


class InvalidPlanError(EngineError):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field
