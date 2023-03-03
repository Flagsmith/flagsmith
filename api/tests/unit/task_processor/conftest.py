import pytest


@pytest.fixture
def run_by_processor(monkeypatch):
    monkeypatch.setenv("RUN_BY_PROCESSOR", "True")
