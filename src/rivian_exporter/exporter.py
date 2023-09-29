import asyncio
import time
from typing import Any

import glog as log
import prometheus_client as prom

from . import vehicle

RIVIAN_GAUGES = {
    "batteryCapacity": prom.Gauge("battery_capacity", "battery capacity in kwH"),
    "batteryLevel": prom.Gauge("battery_level", "current level of battery as a %"),
    "cabinClimateInteriorTemperature": prom.Gauge(
        "cabin_climate_interior_temperature", "Current temperature in the cabin in C"
    ),
    "distanceToEmpty": prom.Gauge("distance_to_empty", "range in km"),
    "vehicleMileage": prom.Gauge("vehicle_mileage", "current odo reading in m"),
}
RIVIAN_INFOS = {
    "otaCurrentVersion": prom.Info("ota_current_version", "Current OTA Version"),
}


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


def run(port: int, scrape_interval: int, vin: str) -> None:
    # Start up the server to expose the metrics.
    loop = asyncio.new_event_loop()
    log.info(f"Starting prometheus server on port {port}")
    prom.start_http_server(port)
    # Generate some requests.
    while True:
        state = asyncio.run(vehicle.get_vehicle_state(vin))
        set_prom_metrics(state)
        time.sleep(scrape_interval)
