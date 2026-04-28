# Compatibility shim: pytest-lazy-fixture was replaced with pytest-lazy-fixtures.
# This module allows third-party test code that still imports from pytest_lazyfixture
# to continue working without modification.
from pytest_lazy_fixtures import lf as lazy_fixture

__all__ = ["lazy_fixture"]
