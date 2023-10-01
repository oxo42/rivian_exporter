import io
import os

import pytest
import rivian
from testslide import StrictMock

from rivian_exporter import vehicle

from . import utils
from .pytest_testslide import testslide


def test_ensure_auth():
    env = "ACCESS_TOKEN"
    assert os.getenv(env) is None
    with pytest.raises(Exception) as e:
        vehicle.ensure_auth()


async def test_login_without_otp(testslide, monkeypatch):
    rivian_mock = utils.get_rivian_mock(testslide)
    testslide.mock_async_callable(rivian_mock, "validate_otp").to_return_value(
        None
    ).and_assert_not_called()
    rivian_mock._otp_needed = False
    rivian_mock._access_token = "access"
    rivian_mock._refresh_token = "refresh"
    rivian_mock._user_session_token = "user"
    testslide.mock_constructor(rivian, "Rivian").to_return_value(rivian_mock)
    monkeypatch.setattr("sys.stdin", io.StringIO("user\npass"))
    (a, r, u) = await vehicle.login()
    assert a == "access"
    assert r == "refresh"
    assert u == "user"
