import asyncio
import json
import os
from typing import Any

import click
import prometheus_client as prom
import glog as log

from . import exporter, vehicle


@click.group()
def cli() -> None:
    pass


@cli.command(help="Start a Prometheus exporter for a specific VIN")
@click.option("--port", default=8000)
@click.option("--scrape-interval", default=60)
def prometheus(port: int, scrape_interval: int) -> None:
    vehicle.ensure_auth()
    vin = os.environ["VIN"]
    exporter.run(port, scrape_interval, vin)


@cli.command(help="create tokens needed for the graph api")
def login() -> None:
    (access_token, refresh_token, user_session_token) = asyncio.run(vehicle.login())
    print(f"ACCESS_TOKEN={access_token}")
    print(f"REFRESH_TOKEN={refresh_token}")
    print(f"USER_SESSION_TOKEN={user_session_token}")


@cli.command()
def user_info():
    info = asyncio.run(vehicle.get_user_info())
    print(json.dumps(info))


@cli.command()
@click.argument("vin")
def vehicle_state(vin: str) -> None:
    state = asyncio.run(vehicle.get_vehicle_state(vin))
    print(json.dumps(state))


if __name__ == "__main__":
    log.setLevel("INFO")
    cli()
