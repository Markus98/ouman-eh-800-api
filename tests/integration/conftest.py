"""Fixtures for integration tests that run against a real Ouman EH-800 device.

Required environment variables:
    OUMAN_URL: Base URL of the device (e.g. "http://192.168.1.100")
    OUMAN_USERNAME: Login username
    OUMAN_PASSWORD: Login password

Tests in this directory are skipped if the variables are not set.
Run with: `make integration` or `pytest --override-ini="addopts=" tests/integration/`
"""

import os
from collections.abc import AsyncGenerator

import aiohttp
import pytest
import pytest_asyncio

from ouman_eh_800_api.client import OumanEh800Client


def _env_or_skip(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} environment variable not set")
    return value


@pytest.fixture(scope="session")
def device_url() -> str:
    return _env_or_skip("OUMAN_URL")


@pytest.fixture(scope="session")
def device_username() -> str:
    return _env_or_skip("OUMAN_USERNAME")


@pytest.fixture(scope="session")
def device_password() -> str:
    return _env_or_skip("OUMAN_PASSWORD")


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession() as s:
        yield s


@pytest_asyncio.fixture
async def client(
    session: aiohttp.ClientSession,
    device_url: str,
    device_username: str,
    device_password: str,
) -> AsyncGenerator[OumanEh800Client]:
    """Logged-in client for the duration of a test."""
    c = OumanEh800Client(
        session=session,
        address=device_url,
        username=device_username,
        password=device_password,
    )
    await c.login()
    try:
        yield c
    finally:
        await c.logout()


@pytest_asyncio.fixture
async def l2_installed(client: OumanEh800Client) -> None:
    """Skip the test if the L2 heating circuit is not installed on the device."""
    if not await client.get_is_l2_installed():
        pytest.skip("L2 heating circuit not installed on device")


@pytest_asyncio.fixture
async def l1_room_sensor_installed(client: OumanEh800Client) -> None:
    """Skip the test if no L1 room sensor is installed on the device."""
    if not await client.get_is_l1_room_sensor_installed():
        pytest.skip("L1 room sensor not installed on device")


@pytest_asyncio.fixture
async def l2_room_sensor_installed(
    client: OumanEh800Client, l2_installed: None
) -> None:
    """Skip the test if no L2 room sensor is installed on the device."""
    if not await client.get_is_l2_room_sensor_installed():
        pytest.skip("L2 room sensor not installed on device")
