import os
from typing import Any, Tuple

import glog as log
import rivian


class RivianExporterException(Exception):
    """Base exception"""


class TokenUnavailableException(RivianExporterException):
    """Cannot read the token from the environment or the file"""


async def login() -> Tuple[str, str, str]:
    async with rivian.Rivian() as r:
        username = input("Username: ")
        password = input("Password: ")
        log.info(f"Authenticating as {username}")
        await r.authenticate(username, password)
        if r._otp_needed:
            log.info("OTP Required")
            otp_code = input("OTP: ")
            await r.validate_otp(username, otp_code)
        return (r._access_token, r._refresh_token, r._user_session_token)


def get_token(token: str) -> str:
    """
    This will get a token (or the VIN) either directly from an environment
    variable `token` or from the file specified in the environment variable
    `{token}_FILE`
    """
    env = os.getenv(token)
    if env:
        return env

    filename = os.environ[f"{token}_FILE"]
    if not os.path.isfile(filename):
        raise TokenUnavailableException(token)

    with open(filename) as f:
        line = f.readline()
        return line.strip()


def get_rivian() -> rivian.Rivian:
    access_token = get_token("ACCESS_TOKEN")
    refresh_token = get_token("REFRESH_TOKEN")
    user_session_token = get_token("USER_SESSION_TOKEN")
    return rivian.Rivian(
        access_token=access_token,
        refresh_token=refresh_token,
        user_session_token=user_session_token,
    )


async def get_user_info() -> Any:
    async with get_rivian() as r:
        await r.create_csrf_token()
        info = await r.get_user_information()
        body = await info.json()
        return body


async def get_vehicle_state(vin: str) -> Any:
    async with get_rivian() as r:
        await r.create_csrf_token()
        state = await r.get_vehicle_state(vin)
        body = await state.json()
        return body
