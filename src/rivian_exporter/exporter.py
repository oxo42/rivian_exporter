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
from .rivian_collectors import gauge, info

GAUGES = [
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

INFOS = [
    info(
        "rivian_charger",
        "Charger Info",
        {
            "derate_status": "chargerDerateStatus",
            "state": "chargerState",
            "status": "chargerStatus",
        },
    ),
    info(
        "rivian_closures",
        "Closures",
        {
            "frunk_closed": "closureFrunkClosed",
            "frunk_locked": "closureFrunkLocked",
            "liftgate_closed": "closureLiftgateClosed",
            "liftgate_locked": "closureLiftgateLocked",
        },
    ),
    info(
        "rivian_doors",
        "Doors",
        {
            "front_left_closed": "doorFrontLeftClosed",
            "front_left_locked": "doorFrontLeftLocked",
            "front_right_closed": "doorFrontRightClosed",
            "front_right_locked": "doorFrontRightLocked",
            "rear_left_closed": "doorRearLeftClosed",
            "rear_left_locked": "doorRearLeftLocked",
            "rear_right_closed": "doorRearRightClosed",
            "rear_right_locked": "doorRearRightLocked",
        },
    ),
    info("rivian_drive_mode", "Drive Mode", {"drive_mode": "driveMode"}),
    info(
        "rivian_ota_version",
        "OTA Version",
        {
            "version": "otaCurrentVersion",
            "githash": "otaCurrentVersionGitHash",
        },
    ),
    info(
        "rivian_pet_mode",
        "Pet Mode",
        {
            "status": "petModeStatus",
            "temperature_status": "petModeTemperatureStatus",
        },
    ),
    info(
        "rivian_vehicle_state",
        "Vehicle states",
        {
            "defrost_defog": "defrostDefogStatus",
            "gear": "gearStatus",
            "power": "powerState",
            "wiper_fluid": "wiperFluidState",
        },
    ),
    info("rivian_range_threshold", "Range threshold", {"state": "rangeThreshold"}),
    info(
        "rivian_tire_pressure",
        "Tire Pressure",
        {
            "front_left": "tirePressureStatusFrontLeft",
            "front_right": "tirePressureStatusFrontRight",
            "rear_left": "tirePressureStatusRearLeft",
            "rear_right": "tirePressureStatusRearRight",
        },
    ),
]


COLLECTORS = GAUGES + INFOS


def set_prom_metrics(data: Any) -> None:
    state = data["data"]["vehicleState"]
    for collector in COLLECTORS:
        collector.process(state)

    count = len(COLLECTORS)
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
