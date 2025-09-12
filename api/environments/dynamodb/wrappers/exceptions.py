from decimal import Decimal


class CapacityBudgetExceeded(Exception):
    def __init__(
        self,
        capacity_budget: Decimal,
        capacity_spent: Decimal,
    ) -> None:
        self.capacity_budget = capacity_budget
        self.capacity_spent = capacity_spent
