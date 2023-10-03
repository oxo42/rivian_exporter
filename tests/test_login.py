import io
import builtins
import os

import pytest
import rivian
from testslide import StrictMock

from rivian_exporter import vehicle

from . import utils
from .pytest_testslide import testslide


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


def test_get_token_from_env(testslide):
    token = "foo"
    testslide.mock_callable(os, "getenv").for_call(token).to_return_value(
        "foobar"
    ).and_assert_called_once()
    assert vehicle.get_token(token) == "foobar"


def test_get_token_from_file_not_found(testslide):
    testslide.mock_callable(os.path, "isfile").to_return_value(False)
    with pytest.raises(vehicle.TokenUnavailableException):
        vehicle.get_token("foo")


def test_get_token_from_file_not_found(testslide):
    token = "foo"
    testslide.mock_callable(os, "getenv").for_call("foo").to_return_value(
        None
    ).and_assert_called_once()
    testslide.mock_callable(os, "getenv").for_call("foo_FILE").to_return_value(
        "thefile"
    ).and_assert_called_once()
    testslide.mock_callable(os.path, "isfile").for_call("thefile").to_return_value(
        True
    ).and_assert_called_once()
    file_mock = StrictMock(default_context_manager=True)
    file_mock.__enter__ = lambda: file_mock
    file_mock.__exit__ = lambda exc_type, exc_val, exc_tb: None
    testslide.mock_callable(file_mock, "readline").to_return_value("TheToken\n")
    testslide.mock_callable(builtins, "open").to_return_value(file_mock)
    assert vehicle.get_token(token) == "TheToken"
