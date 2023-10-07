import prometheus_client as prom
import testslide as ts

from rivian_exporter import rivian_collectors

from .pytest_testslide import testslide

VEHICLE_STATE = {
    "alarmSoundStatus": {"timeStamp": "2023-09-29T23:04:12.222Z", "value": "false"},
    "batteryCapacity": {"timeStamp": "2023-09-30T04:35:27.825Z", "value": 127},
    "batteryHvThermalEvent": {"timeStamp": "2023-09-30T04:34:47.474Z", "value": "off"},
    "batteryHvThermalEventPropagation": {
        "timeStamp": "2023-09-30T04:34:49.167Z",
        "value": "nominal",
    },
    "batteryLevel": {"timeStamp": "2023-09-30T04:35:27.825Z", "value": 52.6},
    "batteryLimit": {"timeStamp": "2023-09-28T05:08:19.501Z", "value": 70},
    "brakeFluidLow": None,
    "cabinClimateDriverTemperature": {
        "timeStamp": "2023-09-30T05:03:36.213Z",
        "value": 21,
    },
    "gnssLocation": {
        "latitude": 17.8216,
        "longitude": 31.0492,
        "timeStamp": "2023-09-30T05:08:33.002Z",
    },
    "otaCurrentVersionWeek": {"timeStamp": "2023-09-28T14:28:55.388Z", "value": 34},
    "otaCurrentVersionNumber": {"timeStamp": "2023-09-28T14:28:55.388Z", "value": 0},
}


def test_info():
    version_info = rivian_collectors.RivianInfo(
        "test_info",
        "description",
        data={
            "week": ("otaCurrentVersionWeek", "value"),
            "number": ("otaCurrentVersionNumber", "value"),
        },
    )
    expected = {"week": "34", "number": "0"}
    assert version_info.values(VEHICLE_STATE) == expected


def test_gauge(testslide):
    prom_mock = ts.StrictMock(prom.Gauge)
    testslide.mock_constructor(prom, "Gauge").to_return_value(prom_mock)
    testslide.mock_callable(prom_mock, "set").to_return_value(
        None
    ).and_assert_called_once()
    collector = rivian_collectors.gauge(
        "rivian_battery_capacity_kwh",
        "Battery capacity",
        "batteryCapacity",
    )
    datum = VEHICLE_STATE[collector.rivian_label]
    assert datum["value"] == 127  # Just check we got the right one
    # Check we get the value out of the dict
    assert collector.getter(datum) == 127
    # Check we don't change the value
    assert collector.modifier(127) == 127

    collector.process(VEHICLE_STATE)


def test_gauge_with_modifier(testslide):
    """
    The battery level is 52.6%.  Prometheus wants ratios to be from 0-1. Make this divide by 100
    """
    prom_mock = ts.StrictMock(prom.Gauge)
    testslide.mock_constructor(prom, "Gauge").to_return_value(prom_mock)
    testslide.mock_callable(prom_mock, "set").for_call(0.526).to_return_value(
        None
    ).and_assert_called_once()
    collector = rivian_collectors.gauge(
        "rivian_battery_level_ratio",
        "Percentage of battery remaining",
        "batteryLevel",
        modifier=lambda v: v / 100,
    )
    collector.process(VEHICLE_STATE)


def test_gauge_with_getter(testslide):
    prom_mock = ts.StrictMock(prom.Gauge)
    testslide.mock_constructor(prom, "Gauge").to_return_value(prom_mock)
    testslide.mock_callable(prom_mock, "set").for_call(17.8216).to_return_value(
        None
    ).and_assert_called_once()
    collector = rivian_collectors.gauge(
        "rivian_latitude_degrees",
        "Latitude of vehicle",
        "gnssLocation",
        getter=lambda v: v["latitude"],
    )
    collector.process(VEHICLE_STATE)


def test_info_function_expands_data_dict():
    i = rivian_collectors.info("name", "desc", {"key": "rivian_value"})
    expected_data_dict = {"key": ("rivian_value", "value")}
    assert i.data == expected_data_dict
