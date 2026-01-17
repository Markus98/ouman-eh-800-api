import asyncio
import re
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import MagicMock

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import ClientSession
from aioresponses import aioresponses

from ouman_eh_800_api.client import OumanEh800Client
from ouman_eh_800_api.const import HomeAwayControl, OperationMode
from ouman_eh_800_api.exceptions import (
    OumanClientAuthenticationError,
    OumanClientCommunicationError,
    OumanClientError,
)
from ouman_eh_800_api.registry import (
    L1Endpoints,
    L1EndpointsWithRoomSensor,
    L2Endpoints,
    L2EndpointsWithRoomSensor,
    OumanRegistrySet,
    SystemEndpoints,
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


# =============================================================================
# Tests for _construct_request_url
# =============================================================================


def test_construct_request_url_with_params(client: OumanEh800Client):
    url = client._construct_request_url("request", ["S_227_85", "S_259_85"])
    assert url.startswith(f"{MOCK_ADDRESS}/request?")
    assert "S_227_85" in url
    assert "S_259_85" in url
    # Check GMT string is appended
    assert "GMT" in url
    # Check params are separated by semicolons
    assert ";" in url


def test_construct_request_url_empty_params(client: OumanEh800Client):
    url = client._construct_request_url("alarms", [])
    assert url.startswith(f"{MOCK_ADDRESS}/alarms?")
    # Should still have the GMT string
    assert "GMT" in url


# =============================================================================
# Tests for _request (HTTP and network errors)
# =============================================================================


@pytest.mark.asyncio
async def test_request_http_error(client: OumanEh800Client, m: aioresponses):
    m.get(
        f"{MOCK_ADDRESS}/request?S_227_85%253B{MOCK_DATE_PARAM}",
        status=500,
    )

    with pytest.raises(OumanClientCommunicationError) as exc_info:
        await client._request("request", ["S_227_85"])

    assert "HTTP Error: 500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_request_network_error(client: OumanEh800Client, m: aioresponses):
    m.get(
        f"{MOCK_ADDRESS}/request?S_227_85%253B{MOCK_DATE_PARAM}",
        exception=aiohttp.ClientError("Connection refused"),
    )

    with pytest.raises(OumanClientCommunicationError) as exc_info:
        await client._request("request", ["S_227_85"])

    assert "Network error" in str(exc_info.value)


# =============================================================================
# Tests for _get_values
# =============================================================================


@pytest.mark.asyncio
async def test_get_values_success(client: OumanEh800Client, m: aioresponses):
    m.get(
        f"{MOCK_ADDRESS}/request?S_227_85%253BS_259_85%253B{MOCK_DATE_PARAM}",
        body="request?S_227_85=-13.3;S_259_85=39.1;\x00",
        status=200,
    )

    response = await client._get_values(["S_227_85", "S_259_85"])

    assert response.prefix == "request"
    assert response.values["S_227_85"] == "-13.3"
    assert response.values["S_259_85"] == "39.1"


@pytest.mark.asyncio
async def test_get_values_missing_endpoint_logs_warning(
    client: OumanEh800Client, m: aioresponses, caplog
):
    m.get(
        f"{MOCK_ADDRESS}/request?S_227_85%253BS_259_85%253B{MOCK_DATE_PARAM}",
        body="request?S_227_85=-13.3;\x00",  # S_259_85 is missing
        status=200,
    )

    await client._get_values(["S_227_85", "S_259_85"])

    assert "S_259_85" in caplog.text
    assert "not found in response" in caplog.text


# =============================================================================
# Tests for _update_values (including 404 retry)
# =============================================================================


@pytest.mark.asyncio
async def test_update_values_success(client: OumanEh800Client, m: aioresponses):
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        body="update?S_92_85=50.0;\x00",
        status=200,
    )

    response = await client._update_values({"S_92_85": "50"})

    assert response.values["S_92_85"] == "50.0"


@pytest.mark.asyncio
async def test_update_values_404_triggers_relogin(
    client: OumanEh800Client, m: aioresponses
):
    # First request returns 404
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        status=404,
    )
    # Then login
    m.get(
        MOCK_LOGIN_URL,
        body="login?result=ok;\x00",
        status=200,
    )
    # Then retry update succeeds
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        body="update?S_92_85=50.0;\x00",
        status=200,
    )

    response = await client._update_values({"S_92_85": "50"})

    assert response.values["S_92_85"] == "50.0"


@pytest.mark.asyncio
async def test_update_values_non_404_error_raises(
    client: OumanEh800Client, m: aioresponses
):
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        status=500,
    )

    with pytest.raises(OumanClientCommunicationError):
        await client._update_values({"S_92_85": "50"})


# =============================================================================
# Tests for _set_int_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_set_int_endpoint_success(client: OumanEh800Client, m: aioresponses):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=50.0;\x00",
        status=200,
    )

    result = await client._set_int_endpoint(endpoint, 50)

    assert result == 50


@pytest.mark.asyncio
async def test_set_int_endpoint_value_below_min_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT  # min_val=0, max_val=100

    with pytest.raises(ValueError) as exc_info:
        await client._set_int_endpoint(endpoint, -1)

    assert "out of bounds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_int_endpoint_value_above_max_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT  # min_val=0, max_val=100

    with pytest.raises(ValueError) as exc_info:
        await client._set_int_endpoint(endpoint, 101)

    assert "out of bounds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_int_endpoint_missing_response_raises(
    client: OumanEh800Client, m: aioresponses
):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        body="update?some_other_id=50.0;\x00",
        status=200,
    )

    with pytest.raises(OumanClientError) as exc_info:
        await client._set_int_endpoint(endpoint, 50)

    assert "Endpoint ID missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_int_endpoint_mismatched_value_raises(
    client: OumanEh800Client, m: aioresponses
):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=99.0;\x00",  # Returns different value
        status=200,
    )

    with pytest.raises(OumanClientError) as exc_info:
        await client._set_int_endpoint(endpoint, 50)

    assert "does not match" in str(exc_info.value)


# =============================================================================
# Tests for _set_float_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_set_float_endpoint_success(client: OumanEh800Client, m: aioresponses):
    endpoint = L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING
    m.get(
        re.compile(r".*/update\?.*S_134_85.*1\.5.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=1.5;\x00",
        status=200,
    )

    result = await client._set_float_endpoint(endpoint, 1.5)

    assert result == 1.5


@pytest.mark.asyncio
async def test_set_float_endpoint_rounds_to_one_decimal(
    client: OumanEh800Client, m: aioresponses
):
    endpoint = L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING
    # Value 1.55 should be rounded to 1.6
    m.get(
        re.compile(r".*/update\?.*S_134_85.*1\.6.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=1.6;\x00",
        status=200,
    )

    result = await client._set_float_endpoint(endpoint, 1.55)

    assert result == 1.6


@pytest.mark.asyncio
async def test_set_float_endpoint_value_below_min_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING  # min_val=-4.0, max_val=4.0

    with pytest.raises(ValueError) as exc_info:
        await client._set_float_endpoint(endpoint, -5.0)

    assert "out of bounds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_float_endpoint_value_above_max_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING  # min_val=-4.0, max_val=4.0

    with pytest.raises(ValueError) as exc_info:
        await client._set_float_endpoint(endpoint, 5.0)

    assert "out of bounds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_float_endpoint_mismatched_value_raises(
    client: OumanEh800Client, m: aioresponses
):
    endpoint = L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING
    m.get(
        re.compile(r".*/update\?.*S_134_85.*1\.5.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=2.5;\x00",  # Returns different value
        status=200,
    )

    with pytest.raises(OumanClientError) as exc_info:
        await client._set_float_endpoint(endpoint, 1.5)

    assert "does not match" in str(exc_info.value)


# =============================================================================
# Tests for _set_enum_endpoint
# =============================================================================


@pytest.mark.asyncio
async def test_set_enum_endpoint_success(client: OumanEh800Client, m: aioresponses):
    endpoint = L1Endpoints.OPERATION_MODE
    m.get(
        re.compile(r".*/update\?S_59_85.*0.*"),
        body="update?S_59_85=0;\x00",
        status=200,
    )

    result = await client._set_enum_endpoint(endpoint, OperationMode.AUTOMATIC)

    assert result == OperationMode.AUTOMATIC


@pytest.mark.asyncio
async def test_set_enum_endpoint_wrong_type_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.OPERATION_MODE  # expects OperationMode

    with pytest.raises(TypeError) as exc_info:
        await client._set_enum_endpoint(endpoint, HomeAwayControl.HOME)  # Wrong type

    assert "Unexpected type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_enum_endpoint_missing_response_raises(
    client: OumanEh800Client, m: aioresponses
):
    endpoint = L1Endpoints.OPERATION_MODE
    m.get(
        re.compile(r".*/update\?S_59_85.*0.*"),
        body="update?some_other_id=0;\x00",
        status=200,
    )

    with pytest.raises(OumanClientError) as exc_info:
        await client._set_enum_endpoint(endpoint, OperationMode.AUTOMATIC)

    assert "Endpoint ID missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_enum_endpoint_mismatched_value_raises(
    client: OumanEh800Client, m: aioresponses
):
    endpoint = L1Endpoints.OPERATION_MODE
    m.get(
        re.compile(r".*/update\?S_59_85.*0.*"),
        body="update?S_59_85=1;\x00",  # Returns TEMPERATURE_DROP instead of AUTOMATIC
        status=200,
    )

    with pytest.raises(OumanClientError) as exc_info:
        await client._set_enum_endpoint(endpoint, OperationMode.AUTOMATIC)

    assert "does not match" in str(exc_info.value)


# =============================================================================
# Tests for set_endpoint_value (type dispatcher)
# =============================================================================


@pytest.mark.asyncio
async def test_set_endpoint_value_int(client: OumanEh800Client, m: aioresponses):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT
    m.get(
        re.compile(r".*/update\?S_92_85.*50.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=50.0;\x00",
        status=200,
    )

    result = await client.set_endpoint_value(endpoint, 50)

    assert result == 50


@pytest.mark.asyncio
async def test_set_endpoint_value_float(client: OumanEh800Client, m: aioresponses):
    endpoint = L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING
    m.get(
        re.compile(r".*/update\?.*S_134_85.*1\.5.*"),
        body=f"update?{endpoint.sensor_endpoint_id}=1.5;\x00",
        status=200,
    )

    result = await client.set_endpoint_value(endpoint, 1.5)

    assert result == 1.5


@pytest.mark.asyncio
async def test_set_endpoint_value_enum(client: OumanEh800Client, m: aioresponses):
    endpoint = L1Endpoints.OPERATION_MODE
    m.get(
        re.compile(r".*/update\?S_59_85.*0.*"),
        body="update?S_59_85=0;\x00",
        status=200,
    )

    result = await client.set_endpoint_value(endpoint, OperationMode.AUTOMATIC)

    assert result == OperationMode.AUTOMATIC


@pytest.mark.asyncio
async def test_set_endpoint_value_non_controllable_raises(client: OumanEh800Client):
    endpoint = SystemEndpoints.OUTSIDE_TEMPERATURE  # Not controllable

    with pytest.raises(TypeError) as exc_info:
        await client.set_endpoint_value(endpoint, 20.0)

    assert "not a controllable endpoint" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_endpoint_value_int_with_float_value_raises(
    client: OumanEh800Client,
):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT  # IntControlOumanEndpoint

    with pytest.raises(ValueError) as exc_info:
        await client.set_endpoint_value(endpoint, 50.5)  # Non-integer float

    assert "must be an integer" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_endpoint_value_int_with_wrong_type_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.VALVE_POSITION_SETPOINT

    with pytest.raises(TypeError) as exc_info:
        await client.set_endpoint_value(endpoint, "50")  # String instead of int

    assert "must be numeric" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_endpoint_value_enum_with_wrong_type_raises(client: OumanEh800Client):
    endpoint = L1Endpoints.OPERATION_MODE

    with pytest.raises(TypeError) as exc_info:
        await client.set_endpoint_value(endpoint, 0)  # int instead of ControlEnum

    assert "must be a ControlEnum" in str(exc_info.value)


# =============================================================================
# Tests for get_values
# =============================================================================


@pytest.mark.asyncio
async def test_get_values_single_registry(client: OumanEh800Client, m: aioresponses):
    # Build the endpoint IDs that will be requested
    registry_set = OumanRegistrySet([SystemEndpoints])
    params = "%253B".join(registry_set.sensor_endpoint_ids)

    m.get(
        f"{MOCK_ADDRESS}/request?{params}%253B{MOCK_DATE_PARAM}",
        body="request?S_26_85=600;S_135_85=0;S_227_85=-13.3;S_1002_85=test;S_1004_85=ok;S_140_85=0;\x00",
        status=200,
    )

    result = await client.get_values(registry_set)

    assert SystemEndpoints.OUTSIDE_TEMPERATURE in result
    assert result[SystemEndpoints.OUTSIDE_TEMPERATURE] == -13.3
    assert SystemEndpoints.HOME_AWAY_MODE in result
    assert result[SystemEndpoints.HOME_AWAY_MODE] == HomeAwayControl.HOME


@pytest.mark.asyncio
async def test_get_values_unknown_endpoint_logs_warning(
    client: OumanEh800Client, m: aioresponses, caplog
):
    registry_set = OumanRegistrySet([SystemEndpoints])
    params = "%253B".join(registry_set.sensor_endpoint_ids)

    # Response includes an unknown endpoint
    m.get(
        f"{MOCK_ADDRESS}/request?{params}%253B{MOCK_DATE_PARAM}",
        body="request?S_26_85=600;S_135_85=0;S_227_85=-13.3;S_1002_85=test;S_1004_85=ok;S_140_85=0;UNKNOWN_ID=123;\x00",
        status=200,
    )

    await client.get_values(registry_set)

    assert "Unexpected endpoint ID" in caplog.text
    assert "UNKNOWN_ID" in caplog.text


# =============================================================================
# Tests for get_is_l2_installed
# =============================================================================


@pytest.mark.asyncio
async def test_get_is_l2_installed_true(client: OumanEh800Client, m: aioresponses):
    endpoint_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id
    m.get(
        f"{MOCK_ADDRESS}/request?{endpoint_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{endpoint_id}=1;\x00",  # Non-zero means installed
        status=200,
    )

    result = await client.get_is_l2_installed()

    assert result is True


@pytest.mark.asyncio
async def test_get_is_l2_installed_false(client: OumanEh800Client, m: aioresponses):
    endpoint_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id
    m.get(
        f"{MOCK_ADDRESS}/request?{endpoint_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{endpoint_id}=0;\x00",
        status=200,
    )

    result = await client.get_is_l2_installed()

    assert result is False


# =============================================================================
# Tests for _get_is_room_sensor_installed
# =============================================================================


@pytest.mark.asyncio
async def test_get_is_room_sensor_installed_true(
    client: OumanEh800Client, m: aioresponses
):
    endpoint_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    m.get(
        f"{MOCK_ADDRESS}/request?{endpoint_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{endpoint_id}=on;\x00",  # Non-"off" means installed
        status=200,
    )

    result = await client._get_is_room_sensor_installed(endpoint_id)

    assert result is True


@pytest.mark.asyncio
async def test_get_is_room_sensor_installed_false(
    client: OumanEh800Client, m: aioresponses
):
    endpoint_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    m.get(
        f"{MOCK_ADDRESS}/request?{endpoint_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{endpoint_id}=off;\x00",
        status=200,
    )

    result = await client._get_is_room_sensor_installed(endpoint_id)

    assert result is False


@pytest.mark.asyncio
async def test_get_is_l1_room_sensor_installed(
    client: OumanEh800Client, m: aioresponses
):
    endpoint_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    m.get(
        f"{MOCK_ADDRESS}/request?{endpoint_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{endpoint_id}=off;\x00",
        status=200,
    )

    result = await client.get_is_l1_room_sensor_installed()

    assert result is False


@pytest.mark.asyncio
async def test_get_is_l2_room_sensor_installed(
    client: OumanEh800Client, m: aioresponses
):
    endpoint_id = L2Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    m.get(
        f"{MOCK_ADDRESS}/request?{endpoint_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{endpoint_id}=off;\x00",
        status=200,
    )

    result = await client.get_is_l2_room_sensor_installed()

    assert result is False


# =============================================================================
# Tests for get_active_registries
# =============================================================================


@pytest.mark.asyncio
async def test_get_active_registries_l1_only_no_room_sensor(
    client: OumanEh800Client, m: aioresponses
):
    l1_sensor_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    l2_installed_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id

    # L1 room sensor: off
    m.get(
        f"{MOCK_ADDRESS}/request?{l1_sensor_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l1_sensor_id}=off;\x00",
        status=200,
    )
    # L2 not installed
    m.get(
        f"{MOCK_ADDRESS}/request?{l2_installed_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l2_installed_id}=0;\x00",
        status=200,
    )

    result = await client.get_active_registries()

    assert SystemEndpoints in result.registries
    assert L1Endpoints in result.registries
    assert L1EndpointsWithRoomSensor not in result.registries
    assert L2Endpoints not in result.registries


@pytest.mark.asyncio
async def test_get_active_registries_l1_with_room_sensor(
    client: OumanEh800Client, m: aioresponses
):
    l1_sensor_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    l2_installed_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id

    # L1 room sensor: installed
    m.get(
        f"{MOCK_ADDRESS}/request?{l1_sensor_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l1_sensor_id}=on;\x00",
        status=200,
    )
    # L2 not installed
    m.get(
        f"{MOCK_ADDRESS}/request?{l2_installed_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l2_installed_id}=0;\x00",
        status=200,
    )

    result = await client.get_active_registries()

    assert SystemEndpoints in result.registries
    assert L1EndpointsWithRoomSensor in result.registries
    assert L1Endpoints not in result.registries
    assert L2Endpoints not in result.registries


@pytest.mark.asyncio
async def test_get_active_registries_l1_and_l2_no_room_sensors(
    client: OumanEh800Client, m: aioresponses
):
    l1_sensor_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    l2_installed_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id
    l2_sensor_id = L2Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id

    # L1 room sensor: off
    m.get(
        f"{MOCK_ADDRESS}/request?{l1_sensor_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l1_sensor_id}=off;\x00",
        status=200,
    )
    # L2 installed
    m.get(
        f"{MOCK_ADDRESS}/request?{l2_installed_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l2_installed_id}=1;\x00",
        status=200,
    )
    # L2 room sensor: off
    m.get(
        f"{MOCK_ADDRESS}/request?{l2_sensor_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l2_sensor_id}=off;\x00",
        status=200,
    )

    result = await client.get_active_registries()

    assert SystemEndpoints in result.registries
    assert L1Endpoints in result.registries
    assert L2Endpoints in result.registries
    assert L1EndpointsWithRoomSensor not in result.registries
    assert L2EndpointsWithRoomSensor not in result.registries


@pytest.mark.asyncio
async def test_get_active_registries_all_with_room_sensors(
    client: OumanEh800Client, m: aioresponses
):
    l1_sensor_id = L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
    l2_installed_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id
    l2_sensor_id = L2Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id

    # L1 room sensor: on
    m.get(
        f"{MOCK_ADDRESS}/request?{l1_sensor_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l1_sensor_id}=on;\x00",
        status=200,
    )
    # L2 installed
    m.get(
        f"{MOCK_ADDRESS}/request?{l2_installed_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l2_installed_id}=1;\x00",
        status=200,
    )
    # L2 room sensor: on
    m.get(
        f"{MOCK_ADDRESS}/request?{l2_sensor_id}%253B{MOCK_DATE_PARAM}",
        body=f"request?{l2_sensor_id}=on;\x00",
        status=200,
    )

    result = await client.get_active_registries()

    assert SystemEndpoints in result.registries
    assert L1EndpointsWithRoomSensor in result.registries
    assert L2EndpointsWithRoomSensor in result.registries
    assert L1Endpoints not in result.registries
    assert L2Endpoints not in result.registries


# =============================================================================
# Tests for get_alarms
# =============================================================================


@pytest.mark.asyncio
async def test_get_alarms_success(client: OumanEh800Client, m: aioresponses):
    m.get(
        f"{MOCK_ADDRESS}/alarms?{MOCK_DATE_PARAM}",
        body="alarms?alarm1=test;alarm2=none;\x00",
        status=200,
    )

    response = await client.get_alarms()

    assert "alarm1" in response
    assert response["alarm1"] == "test"
