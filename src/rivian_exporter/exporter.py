import asyncio
import time
import rivian
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
        modifier=lambda v: v / 100,
    ),
    gauge("rivian_bearing_degrees", "Bearing of the vehicle", "gnssBearing"),
    gauge(
        "rivian_cabin_climate_driver_temperature_celsius",
        "Desired temperature for the driver",
        "cabinClimateInteriorTemperature",
    ),
    gauge(
        "rivian_cabin_climate_interior_temperature_celsius",
        "Current temperature in the cabin in C",
        "cabinClimateInteriorTemperature",
    ),
    gauge(
        "rivian_distance_to_empty_meters",
        "range",
        "distanceToEmpty",
        modifier=lambda v: v * 1000,
    ),
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
    gauge("rivian_speed_kph", "speed", "gnssSpeed"),
    gauge(
        "rivian_time_to_end_of_charge_seconds",
        "Time to end of charge",
        "timeToEndOfCharge",
    ),
    gauge(
        "rivian_vehicle_mileage_meters",
        "current odo reading in meters",
        "vehicleMileage",
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
        log.debug(f"Info {key} to {value}")

    count = len(COLLECTORS) + len(RIVIAN_INFOS)
    log.info(f"Set {count} metrics")


class RivianExporter:
    vin: str
    scrape_interval: int
    rivian: rivian.Rivian

    def __init__(self, vin: str, scrape_interval: int) -> None:
        self.vin = vin
        self.rivian = vehicle.get_rivian()
        self.scrape_interval = scrape_interval

    async def get_vehicle_state(self) -> Any:
        state = await self.rivian.get_vehicle_state(self.vin)
        body = await state.json()
        return body

    async def run(self):
        await self.rivian.create_csrf_token()
        while True:
            try:
                state = await self.get_vehicle_state()
                set_prom_metrics(state)
                time.sleep(self.scrape_interval)
            except Exception as e:
                log.exception(str(e))
                exception_backoff = 60
                log.info(f"Sleeping {exception_backoff} seconds")
                time.sleep(exception_backoff)


def run(port: int, scrape_interval: int, vin: str) -> None:
    log.info(f"Starting prometheus server on port {port}")
    prom.start_http_server(port)
    exporter = RivianExporter(vin, scrape_interval)
    asyncio.run(exporter.run())
