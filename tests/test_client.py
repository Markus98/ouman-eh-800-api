import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from aioresponses import aioresponses

from ouman_eh_800_api.client import OumanEh800Client
from ouman_eh_800_api.exceptions import (
    OumanClientAuthenticationError,
    OumanClientCommunicationError,
    OumanClientError,
)

MOCK_ADDRESS = "http://10.0.0.1"
MOCK_USERNAME = "user"
MOCK_PASSWORD = "password"


MOCK_DATE_PARAM = (
    "Tue%252C+06+Jan+2026+12%253A00%253A00+GMT%253D"  # "Tue, 06 Jan 2026 12:00:00 GMT="
)
MOCK_LOGIN_URL = f"{MOCK_ADDRESS}/login?uid={MOCK_USERNAME}%253Bpwd%253D{MOCK_PASSWORD}%253B{MOCK_DATE_PARAM}"
MOCK_LOGOUT_URL = f"{MOCK_ADDRESS}/logout?{MOCK_DATE_PARAM}"


@pytest.fixture(autouse=True)
def mock_datetime_now_for_client(monkeypatch):
    fake_now = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
    mock_dt = MagicMock(wraps=datetime)
    mock_dt.now.return_value = fake_now

    monkeypatch.setattr("ouman_eh_800_api.client.datetime", mock_dt)


@pytest_asyncio.fixture
async def client(session: ClientSession) -> OumanEh800Client:
    """Fixture to create a client instance."""
    return OumanEh800Client(
        session=session,
        address=MOCK_ADDRESS,
        username=MOCK_USERNAME,
        password=MOCK_PASSWORD,
    )


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[ClientSession, None]:
    """Fixture for aiohttp session."""
    async with ClientSession() as sess:
        yield sess


@pytest_asyncio.fixture
async def m() -> AsyncGenerator[aioresponses, None]:
    """Fixture for aioresponses for mocking aiohttp requests."""
    with aioresponses() as mock:
        yield mock


@pytest.mark.asyncio
async def test_login_success(client: OumanEh800Client, m: aioresponses):
    m.get(
        MOCK_LOGIN_URL,
        body="login?result=ok;\x00",
        status=200,
    )

    await client.login()


@pytest.mark.asyncio
async def test_login_failure(client: OumanEh800Client, m: aioresponses):
    m.get(
        MOCK_LOGIN_URL,
        body="login?result=error;\x00",
        status=200,
    )

    with pytest.raises(OumanClientAuthenticationError):
        await client.login()


@pytest.mark.asyncio
async def test_login_timeout(client: OumanEh800Client, m: aioresponses):
    m.get(MOCK_LOGIN_URL, exception=asyncio.TimeoutError)

    with pytest.raises(OumanClientCommunicationError):
        await client.login()


@pytest.mark.asyncio
async def test_logout_success(client: OumanEh800Client, m: aioresponses):
    m.get(
        MOCK_LOGOUT_URL,
        body="logout?result=ok;\x00",
        status=200,
    )

    await client.logout()


@pytest.mark.asyncio
async def test_logout_failure(client: OumanEh800Client, m: aioresponses):
    m.get(
        MOCK_LOGIN_URL,
        body="logout?result=error;\x00",
        status=200,
    )

    with pytest.raises(OumanClientError):
        await client.logout()


# TODO: test update values with intial 404 error


@pytest.mark.parametrize(
    "response_text,prefix,params_n",
    [
        (
            "request?S_227_85=-13.3;S_259_85=39.1;S_272_85=1;S_89_85=20.0;S_90_85=13.0;S_54_85=12.0;S_55_85=76.0;S_61_85=40.0;S_63_85=28.0;S_65_85=10.0;S_59_85=5;S_92_85=0;S_135_85=2;S_26_85=600;S_275_85=13.9;S_134_85=0.0;S_0_0=0.0;S_1000_0=L1 Alasajo;\x00",
            "request",
            18,
        ),
        (
            "login?result=error;\x00",
            "login",
            1,
        ),
    ],
)
def test_parse_response(response_text: str, prefix: str, params_n: int):
    parsed_response = OumanEh800Client._parse_api_response(response_text)

    assert parsed_response.prefix == prefix
    assert len(parsed_response.values) == params_n
    for key, value in parsed_response.values.items():
        assert isinstance(key, str)
        assert key
        assert isinstance(value, str)
        assert key in response_text
        assert value in response_text
