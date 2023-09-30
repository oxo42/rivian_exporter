import asyncio
import time
from typing import Any

import glog as log
import prometheus_client as prom

from . import vehicle

RIVIAN_GAUGES = {
    "batteryCapacity": prom.Gauge(
        "rivian_battery_capacity_kwh", "battery capacity in kwH"
    ),
    "batteryLevel": prom.Gauge(
        "rivian_battery_level_ratio", "current level of battery as a %"
    ),
    "batteryLimit": prom.Gauge(
        "rivian_battery_limit_ratio", "Limit to which the battery will charge"
    ),
    "cabinClimateInteriorTemperature": prom.Gauge(
        "rivian_cabin_climate_interior_temperature_celsius",
        "Current temperature in the cabin in C",
    ),
    "distanceToEmpty": prom.Gauge("rivian_distance_to_empty_meters", "range"),
    "vehicleMileage": prom.Gauge(
        "rivian_vehicle_mileage_meters", "current odo reading in meters"
    ),
    "gnssBearing": prom.Gauge("rivian_bearing_degrees", "Bearing of th vehicle"),
    "gnssSpeed": prom.Gauge("rivian_speed_kph", "speed"),
}
RIVIAN_INFOS = {
    "otaCurrentVersion": prom.Info(
        "rivian_ota_current_version_info", "Current OTA Version"
    ),
}

LATITUDE = prom.Gauge("rivian_latitude_degrees", "Latitude")
LONGITUDE = prom.Gauge("rivian_longitude_degrees", "Longitude")


def set_prom_metrics(data: Any) -> None:
    state = data["data"]["vehicleState"]
    for key, gauge in RIVIAN_GAUGES.items():
        value = state[key]["value"]
        gauge.set(value)
        log.info(f"Gauge {key} to {value}")
    for key, info in RIVIAN_INFOS.items():
        value = state[key]["value"]
        info.info({key: value})
        log.info(f"Info {key} to {value}")

    LATITUDE.set(state["gnssLocation"]["latitude"])
    LONGITUDE.set(state["gnssLocation"]["longitude"])


def run(port: int, scrape_interval: int, vin: str) -> None:
    log.info(f"Starting prometheus server on port {port}")
    prom.start_http_server(port)
    while True:
        state = asyncio.run(vehicle.get_vehicle_state(vin))
        set_prom_metrics(state)
        time.sleep(scrape_interval)
