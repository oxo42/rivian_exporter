import testslide as ts

import rivian_exporter.exporter as exporter
import rivian_exporter.vehicle as vehicle
from rivian_exporter import exporter

from . import utils
from .pytest_testslide import testslide


def test_collectors_exist():
    assert len(exporter.COLLECTORS) > 0


def test_rivian_exporter_get_vehicle_state(testslide):
    pass


async def test_get_vehicle_state(testslide):
    vin = "TheVin"
    response_mock = ts.StrictMock()
    testslide.mock_async_callable(response_mock, "json").to_return_value("{}")
    rivian_mock = utils.get_rivian_mock(testslide)
    testslide.mock_async_callable(rivian_mock, "get_vehicle_state").for_call(
        vin
    ).to_return_value(response_mock).and_assert_called_once()

    testslide.mock_callable(vehicle, "get_rivian").to_return_value(rivian_mock)
    rivian_exporter = exporter.RivianExporter(vin, scrape_interval=30)
    state = await rivian_exporter.get_vehicle_state()
    assert state is not None
