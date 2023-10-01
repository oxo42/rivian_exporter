import rivian
from testslide import StrictMock


def get_rivian_mock(testslide):
    rivian_mock = StrictMock(rivian.Rivian)
    testslide.mock_async_callable(rivian_mock, "__aenter__").to_return_value(
        rivian_mock
    )
    testslide.mock_async_callable(rivian_mock, "__aexit__").to_return_value(None)
    testslide.mock_async_callable(rivian_mock, "authenticate").to_return_value(None)
    return rivian_mock
