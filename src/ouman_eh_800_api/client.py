import asyncio
import logging
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Iterable, Mapping, NamedTuple

import aiohttp
from aiohttp import ClientSession

from .const import (
    ENDPOINT_VALUE_MAPPING,
    ENDPOINTS,
    ControlEnum,
    HomeAwayControl,
    OperationMode,
)
from .endpoint import (
    EnumControlOumanEndpoint,
    FloatControlOumanEndpoint,
    IntControlOumanEndpoint,
    L1Endpoints,
    SystemEndpoints,
)
from .exceptions import (
    OumanClientAuthenticationError,
    OumanClientCommunicationError,
    OumanClientError,
)

_LOGGER = logging.getLogger(__name__)


class OumanResponse(NamedTuple):
    prefix: str
    values: Mapping[str, str]


class OumanEh800Client:
    def __init__(
        self, session: ClientSession, address: str, username: str, password: str
    ):
        self._session = session
        self._address = address
        self._username = username
        self._password = password

    @staticmethod
    def _parse_api_response(response_text: str) -> OumanResponse:
        prefix, key_val_str = response_text.split("?", maxsplit=1)
        pairs = [p for p in key_val_str.split(";") if p.strip()]

        # Handle null byte at the end of the response
        if pairs and pairs[-1] == "\x00":
            pairs.pop()

        values_result = {}
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                values_result[key.strip()] = value.strip()
            else:
                _LOGGER.warning(
                    "Skipping malformed key value pair in Ouman response: '%s'", pair
                )

        return OumanResponse(
            prefix=prefix,
            values=values_result,
        )

    def _construct_request_url(self, path: str, params: Iterable[str]) -> str:
        request_url = f"{self._address}/{path}"
        # Append gmt string and equals symbol to match what the web UI does.
        # The requests work without this param as well, except when there are no other params.
        gmt_string_param = (
            formatdate(
                timeval=datetime.now(timezone.utc).timestamp(),
                localtime=False,
                usegmt=True,
            )
            + "="
        )
        params = list(params)
        params.append(gmt_string_param)
        request_url += "?" + ";".join(params)
        return request_url

    async def _request(self, path: str, params: Iterable[str]) -> OumanResponse:
        request_url = self._construct_request_url(path, params)
        try:
            async with asyncio.timeout(10):
                async with self._session.get(request_url) as response:
                    response.raise_for_status()

                    response_text = await response.text()
                    _LOGGER.debug("Raw response from device: '%s'", response_text)

                    parsed_response = self._parse_api_response(response_text)
                    return parsed_response
        except asyncio.TimeoutError as err:
            raise OumanClientCommunicationError("Timeout connecting to device") from err
        except aiohttp.ClientResponseError as err:
            raise OumanClientCommunicationError(f"HTTP Error: {err.status}") from err
        except aiohttp.ClientError as err:
            raise OumanClientCommunicationError(f"Network error: {err}") from err

    async def login(self) -> OumanResponse:
        response = await self._request(
            "login", [f"uid={self._username}", f"pwd={self._password}"]
        )

        if response.values.get("result") == "ok":
            _LOGGER.debug("Successful login")
        elif response.values.get("result") == "error":
            raise OumanClientAuthenticationError("Wrong username or password")
        else:
            raise OumanClientError(
                f"Unexpected response from login request: {response}"
            )
        return response

    async def get_values(self):
        """Get all available values from the Ouman device"""
        params = ENDPOINTS.keys()
        response = await self._request("request", params)
        for param in params:
            if param not in response.values:
                _LOGGER.warning("Requested param '%s' not found in response", param)

        # TODO: actually do something with the values
        result = {**response.values}
        result = {
            ENDPOINTS.get(key, key): ENDPOINT_VALUE_MAPPING.get(key, {}).get(
                value, value
            )
            for key, value in result.items()
        }

        # FIXME: remove debugging lines
        import json

        _LOGGER.info(json.dumps(result, indent=2))

    async def _update_values(
        self, key_value_params: Mapping[str, str]
    ) -> OumanResponse:
        request_path = "update"
        params = [f"{key}={value}" for key, value in key_value_params.items()]
        try:
            response = await self._request(request_path, params)
        except OumanClientCommunicationError as err:
            if not isinstance(err.__cause__, aiohttp.ClientResponseError):
                raise
            if err.__cause__.status == 404:
                _LOGGER.debug("404 response from update request, logging in...")
                await self.login()
                response = await self._request(request_path, params)
        return response

    async def _set_int_endpoint(
        self, endpoint: IntControlOumanEndpoint, value: int
    ) -> OumanResponse:
        if not (endpoint.min_val <= value <= endpoint.max_val):
            raise ValueError(
                f"Value for {endpoint.name} out of bounds [{endpoint.min_val},{endpoint.max_val}]: {value}"
            )
        params = {endpoint.control_endpoint_id: str(value)}
        result = await self._update_values(params)

        if not (result_value := result.values.get(endpoint.sensor_endpoint_id)):
            raise OumanClientError(
                f"Endpoint ID missing from set int endpoint response: {result}"
            )

        try:
            float_result = float(result_value)
        except ValueError as err:
            raise OumanClientError(
                f"API returned value cannot be parsed into a float: {result}"
            ) from err

        if float_result != value:
            raise OumanClientError(
                f"Returned float does not match set int value. Got {result_value}, expected {value}"
            )

        return result

    async def _set_float_endpoint(
        self, endpoint: FloatControlOumanEndpoint, value: float
    ) -> OumanResponse:
        """Sets an endpoint value for endpoints which accept floating
        point numbers. Values are rounded to the precision of one
        decimal."""
        if not (endpoint.min_val <= value <= endpoint.max_val):
            raise ValueError(
                f"Value for {endpoint.name} out of bounds [{endpoint.min_val},{endpoint.max_val}]: {value}"
            )
        rounded_value = round(value, 1)
        params = {endpoint.control_endpoint_id: str(round(value, 1))}
        result = await self._update_values(params)

        if not (result_value := result.values.get(endpoint.sensor_endpoint_id)):
            raise OumanClientError(
                f"Endpoint ID missing from set float endpoint response: {result}"
            )

        try:
            float_result = float(result_value)
        except ValueError as err:
            raise OumanClientError(
                f"API returned value cannot be parsed into a float: {result}"
            ) from err

        if float_result != rounded_value:
            raise OumanClientError(
                f"Returned float does not match set value. Got {result_value}, expected {value}"
            )

        return result

    async def _set_enum_endpoint(
        self, endpoint: EnumControlOumanEndpoint, value: ControlEnum
    ) -> OumanResponse:
        if not isinstance(value, endpoint.enum_type):
            raise TypeError(
                f"Unexpected type for {endpoint.name} value. Expected {endpoint.enum_type}, got {value}."
            )
        params = {endpoint_id: value for endpoint_id in endpoint.control_endpoint_ids}
        result = await self._update_values(params)

        for endpoint_id in endpoint.response_endpoint_ids:
            if not (result_value := result.values.get(endpoint_id)):
                raise OumanClientError(
                    f"Endpoint ID missing from set enum endpoint response: {result}"
                )

        if result_value != value:
            raise OumanClientError(
                f"Returned value does not match str enum value. Got '{result_value}', expected '{value}'"
            )
        return result

    async def set_home_away(self, value: HomeAwayControl) -> OumanResponse:
        result = await self._set_enum_endpoint(SystemEndpoints.HOME_AWAY_MODE, value)
        return result

    async def set_trend_sample_interval(self, value: int) -> OumanResponse:
        result = await self._set_int_endpoint(
            SystemEndpoints.TREND_SAMPLE_INTERVAL, value
        )
        return result

    async def set_l1_operation_mode(self, value: OperationMode) -> OumanResponse:
        result = await self._set_enum_endpoint(L1Endpoints.OPERATION_MODE, value)
        return result

    async def set_l1_valve_position_setpoint(self, position: int) -> OumanResponse:
        result = await self._set_int_endpoint(
            L1Endpoints.VALVE_POSITION_SETPOINT, position
        )
        return result

    async def set_l1_curve_minus_20_temp(self, temperature: int) -> OumanResponse:
        result = await self._set_int_endpoint(
            L1Endpoints.CURVE_MINUS_20_TEMP, temperature
        )
        return result

    async def set_l1_curve_0_temp(self, temperature: int) -> OumanResponse:
        result = await self._set_int_endpoint(L1Endpoints.CURVE_0_TEMP, temperature)
        return result

    async def set_l1_curve_20_temp(self, temperature: int) -> OumanResponse:
        result = await self._set_int_endpoint(L1Endpoints.CURVE_20_TEMP, temperature)
        return result

    async def set_l1_temperature_drop(self, temperature: int) -> OumanResponse:
        result = await self._set_int_endpoint(L1Endpoints.TEMPERATURE_DROP, temperature)
        return result

    async def set_l1_big_temperature_drop(self, temperature: int) -> OumanResponse:
        result = await self._set_int_endpoint(
            L1Endpoints.BIG_TEMPERATURE_DROP, temperature
        )
        return result

    async def set_l1_water_out_minimum_temperature(
        self, temperature: int
    ) -> OumanResponse:
        result = await self._set_int_endpoint(
            L1Endpoints.WATER_OUT_MIN_TEMP, temperature
        )
        return result

    async def set_l1_water_out_maximum_temperature(
        self, temperature: int
    ) -> OumanResponse:
        result = await self._set_int_endpoint(
            L1Endpoints.WATER_OUT_MAX_TEMP, temperature
        )
        return result

    async def set_l1_room_temperature_fine_tuning(
        self, temperature: float
    ) -> OumanResponse:
        result = await self._set_float_endpoint(
            L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING, temperature
        )
        return result

    async def set_l1_room_temperature_fine_tuning_with_sensor(
        self, temperature: float
    ) -> OumanResponse:
        result = await self._set_float_endpoint(
            L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING_WITH_SENSOR, temperature
        )
        return result

    # TODO: get values for if L2 is installed, and if room sensors are installed for l1 or l2

    async def get_alarms(self):
        response = await self._request("alarms", [])
        return response

    async def get_available_settings(self):
        raise NotImplementedError()

    async def get_available_waterinfo(self):
        raise NotImplementedError()

    async def get_available_relay(self):
        raise NotImplementedError()

    async def logout(self) -> OumanResponse:
        response = await self._request("logout", [])
        if response.values.get("result") != "ok":
            raise OumanClientError(
                f"Unexpected response from logout request: {response}"
            )
        return response
