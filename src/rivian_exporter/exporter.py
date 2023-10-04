import asyncio
from typing import Any

import glog as log
import prometheus_client as prom
from rivian import Rivian
from rivian.exceptions import (
    RivianApiException,
    RivianApiRateLimitError,
    RivianExpiredTokenError,
    RivianUnauthenticated,
)

from . import vehicle
from .rivian_collector import RivianCollector, gauge

COLLECTORS: list[RivianCollector] = [
    gauge("rivian_battery_capacity_kwh", "battery capacity in kwH", "batteryCapacity"),
    gauge(
        "rivian_battery_level_ratio",
        "current level of battery as a %",
        "batteryLevel",
        modifier=lambda v: v / 100,
    ),  # type: ignore
    gauge(
        "rivian_battery_limit_ratio",
        "Limit to which the battery will charge",
        "batteryLimit",
        modifier=lambda v: v / 100,
    ),  # type: ignore
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
    ),  # type: ignore
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
    "otaCurrentVersion": prom.Info("rivian_ota_current_version", "Current OTA Version"),
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
    rivian: Rivian

    def __init__(self, vin: str, scrape_interval: int) -> None:
        self.vin = vin
        self.rivian = vehicle.get_rivian()
        self.scrape_interval = scrape_interval

    async def get_vehicle_state(self) -> Any:
        state = await self.rivian.get_vehicle_state(self.vin)
        body = await state.json()
        return body

    async def inner_loop(self) -> None:
        try:
            state = await self.get_vehicle_state()
            set_prom_metrics(state)
            await asyncio.sleep(self.scrape_interval)
        except RivianExpiredTokenError:
            log.info("Rivian token expired, refreshing")
            await self.rivian.create_csrf_token()
        except RivianApiRateLimitError as err:
            log.error("Rate limit being enforced: %s", err, exc_info=1)
            log.info("Sleeping 900 seconds")
            await asyncio.sleep(900)
        except RivianUnauthenticated:
            raise
        except RivianApiException as ex:
            log.error("Rivian api exception: %s", ex, exc_info=1)
        except Exception as ex:  # pylint: disable=broad-except
            log.error(
                "Unknown Exception while updating Rivian data: %s", ex, exc_info=1
            )

    async def run(self) -> None:
        await self.rivian.create_csrf_token()
        while True:
            await self.inner_loop()


def run(port: int, scrape_interval: int, vin: str) -> None:
    log.info(f"Starting prometheus server on port {port}")
    prom.start_http_server(port)
    exporter = RivianExporter(vin, scrape_interval)
    asyncio.run(exporter.run())
