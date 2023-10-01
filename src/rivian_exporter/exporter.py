import asyncio
import time
from typing import Any

import glog as log
import prometheus_client as prom

from . import vehicle
from .rivian_collector import gauge, info

COLLECTORS = [
    gauge("rivian_battery_capacity_kwh", "battery capacity in kwH", "batteryCapacity"),
    gauge(
        "rivian_battery_level_ratio",
        "current level of battery as a %",
        "batteryLevel",
        modifier=lambda v: v / 100,
    ),
    gauge(
        "rivian_battery_limit_ratio",
        "Limit to which the battery will charge",
        "batteryLimit",
    ),
    gauge(
        "rivian_cabin_climate_interior_temperature_celsius",
        "Current temperature in the cabin in C",
        "cabinClimateInteriorTemperature",
    ),
    gauge("rivian_distance_to_empty_meters", "range", "distanceToEmpty"),
    gauge(
        "rivian_vehicle_mileage_meters",
        "current odo reading in meters",
        "vehicleMileage",
    ),
    gauge("rivian_bearing_degrees", "Bearing of the vehicle", "gnssBearing"),
    gauge("rivian_speed_kph", "speed", "gnssSpeed"),
    gauge(
        "rivian_latitude_degrees",
        "Latitude",
        "gnssLocation",
        getter=lambda v: v["latitude"],
    ),
    gauge(
        "rivian_longitude_degrees",
        "Longitude",
        "gnssLocation",
        getter=lambda v: v["longitude"],
    ),
]
RIVIAN_INFOS = {
    "otaCurrentVersion": prom.Info(
        "rivian_ota_current_version_info", "Current OTA Version"
    ),
}


def set_prom_metrics(data: Any) -> None:
    state = data["data"]["vehicleState"]
    for collector in COLLECTORS:
        collector.process(state)

    for key, info in RIVIAN_INFOS.items():
        value = state[key]["value"]
        info.info({key: value})
        log.info(f"Info {key} to {value}")


def run(port: int, scrape_interval: int, vin: str) -> None:
    log.info(f"Starting prometheus server on port {port}")
    prom.start_http_server(port)
    while True:
        state = asyncio.run(vehicle.get_vehicle_state(vin))
        set_prom_metrics(state)
        time.sleep(scrape_interval)
