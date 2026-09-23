from decimal import Decimal


class SystemTraitWriteRaceError(Exception):
    def __init__(self, composite_key: str) -> None:
        super().__init__(
            f"Gave up writing a system trait for identity {composite_key!r}: "
            "concurrent writers kept changing the document between read and "
            "conditional write."
        )
        self.composite_key = composite_key


class CapacityBudgetExceeded(Exception):
    def __init__(
        self,
        capacity_budget: Decimal,
        capacity_spent: Decimal,
    ) -> None:
        self.capacity_budget = capacity_budget
        self.capacity_spent = capacity_spent
