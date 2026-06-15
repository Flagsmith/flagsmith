class FlagdTranslationError(Exception):
    """Base class for translation errors."""


class UntranslatableConditionError(FlagdTranslationError):
    """Raised when a condition cannot be expressed in JsonLogic."""

    def __init__(self, reason: str, operator: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operator = operator
