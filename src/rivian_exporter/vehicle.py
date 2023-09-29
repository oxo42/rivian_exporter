import asyncio
import json
import os
from typing import Any, Tuple

import glog as log
import rivian


def ensure_auth() -> None:
    """
    Ensure ACCESS_TOKEN, REFRESH_TOKEN and USER_SESSION_TOKEN are in the environment and nonnull

    Throws if any issues
    """
    pass


async def login() -> Tuple[str, str, str]:
    async with rivian.Rivian() as r:
        username = input("Username: ")
        password = input("Password: ")
        log.info(f"Authenticating as {username}")
        await r.authenticate(username, password)
        if r._otp_needed:
            log.info("OTP Required")
            otp_code = input()
            await r.validate_otp(username, otp_code)
        return (r._access_token, r._refresh_token, r._user_session_token)


def get_rivian() -> rivian.Rivian:
    ensure_auth()
    access_token = os.getenv("ACCESS_TOKEN")
    refresh_token = os.getenv("REFRESH_TOKEN")
    user_session_token = os.getenv("USER_SESSION_TOKEN")
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
