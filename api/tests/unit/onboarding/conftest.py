from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture()
def is_oss(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("common.core.utils.is_oss", return_value=True)
