import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from aioresponses import aioresponses

from ouman_eh_800_api.client import OumanEh800Client
from ouman_eh_800_api.exceptions import (
    OumanClientAuthenticationError,
    OumanClientCommunicationError,
)

MOCK_ADDRESS = "http://10.0.0.1"
MOCK_USERNAME = "user"
MOCK_PASSWORD = "password"


@pytest_asyncio.fixture
async def client(session: ClientSession) -> AsyncGenerator[OumanEh800Client, None]:
    """Fixture to create a client instance."""
    return OumanEh800Client(
        session=session,
        address="http://10.0.0.1",
        username="user",
        password="password",
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


MOCK_LOGIN_URL = f"{MOCK_ADDRESS}/login?uid={MOCK_USERNAME}%253Bpwd%253D{MOCK_PASSWORD}"


@pytest.mark.asyncio
async def test_login_success(client: OumanEh800Client, m: aioresponses):
    m.get(
        MOCK_LOGIN_URL,
        body="login?result=ok;\x00",
        status=200,
    )

    result = await client._login()

    assert result.prefix == "login"
    assert result.values["result"] == "ok"


@pytest.mark.asyncio
async def test_login_failure(client: OumanEh800Client, m: aioresponses):
    m.get(
        MOCK_LOGIN_URL,
        body="login?result=error;\x00",
        status=200,
    )

    with pytest.raises(OumanClientAuthenticationError):
        await client._login()


@pytest.mark.asyncio
async def test_login_timeout(client: OumanEh800Client, m: aioresponses):
    m.get(MOCK_LOGIN_URL, exception=asyncio.TimeoutError)

    with pytest.raises(OumanClientCommunicationError):
        await client._login()


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
