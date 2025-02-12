from typing import Generator

import pytest

from app.utils import get_version_info


@pytest.fixture(autouse=True)
def clear_get_version_info_cache() -> Generator[None, None, None]:
    yield
    get_version_info.cache_clear()
