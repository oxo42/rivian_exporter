import testslide as ts

import rivian_exporter.exporter as exporter
import rivian_exporter.rivian_collectors as rivian_collectors
import rivian_exporter.vehicle as vehicle

from . import utils
from .pytest_testslide import testslide


def test_set_prom_metrics():
    """
    This actually sets the prometheus metrics.  If I were a Good Engineer™️ I'd go
    verify that they were actually called correctly.  The main thing I want here
    is to ensure I didn't fat-finger any of the keys so am calling it quits.
    P.S. I love PRs
    """
    data = utils.vehicle_data()
    exporter.set_prom_metrics(data)


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
