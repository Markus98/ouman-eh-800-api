import asyncio
import logging
from datetime import datetime, timezone
from email.utils import formatdate
from typing import Iterable, Mapping, NamedTuple, Sequence

import aiohttp
from aiohttp import ClientSession

from .const import ControlEnum, HomeAwayControl, OperationMode
from .endpoint import (
    ControllableEndpoint,
    EnumControlOumanEndpoint,
    FloatControlOumanEndpoint,
    IntControlOumanEndpoint,
    OumanEndpoint,
    OumanValues,
)
from .exceptions import (
    OumanClientAuthenticationError,
    OumanClientCommunicationError,
    OumanClientError,
)
from .registry import (
    L1Endpoints,
    L1EndpointsWithRoomSensor,
    L2Endpoints,
    L2EndpointsWithRoomSensor,
    OumanRegistry,
    OumanRegistrySet,
    SystemEndpoints,
)

_LOGGER = logging.getLogger(__name__)


class _OumanResponse(NamedTuple):
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
    def _parse_api_response(response_text: str) -> _OumanResponse:
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

        return _OumanResponse(
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

    async def _request(self, path: str, params: Iterable[str]) -> _OumanResponse:
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

    async def login(self) -> None:
        """Authenticate with the Ouman EH-800 device.

        Raises:
            OumanClientAuthenticationError: If authentication fails.
            OumanClientError: If the response is unexpected.
        """
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

    async def _get_values(self, endpoint_ids: Sequence[str]) -> _OumanResponse:
        response = await self._request("request", endpoint_ids)
        for endpoint_id in endpoint_ids:
            if endpoint_id not in response.values:
                _LOGGER.warning(
                    "Requested endpoint ID '%s' not found in response", endpoint_id
                )
        return response

    async def get_registry_values(
        self, registries: Sequence[type[OumanRegistry]]
    ) -> dict[OumanEndpoint, OumanValues]:
        """Get all values from the specified endpoint registries"""
        endpoint_ids = [
            endpoint_id
            for registry in registries
            for endpoint_id in registry.get_sensor_endpoint_ids()
        ]
        response = await self._get_values(endpoint_ids)

        def get_endpoint_from_id(id: str) -> OumanEndpoint | None:
            for registry in registries:
                endpoint = registry.get_endpoint_by_sensor_id(id)
                if endpoint:
                    return endpoint
            return None

        result = {}
        for key, value in response.values.items():
            endpoint = get_endpoint_from_id(key)
            if not endpoint:
                _LOGGER.warning(f"Unknown endpoint ID in response: '{key}'")
                continue
            parsed_value = endpoint.parse_value(value)
            result[endpoint] = parsed_value

        return result

    async def _update_values(
        self, key_value_params: Mapping[str, str]
    ) -> _OumanResponse:
        request_path = "update"
        params = [f"{key}={value}" for key, value in key_value_params.items()]
        try:
            response = await self._request(request_path, params)
        except OumanClientCommunicationError as err:
            if not isinstance(err.__cause__, aiohttp.ClientResponseError):
                raise
            if err.__cause__.status != 404:
                raise
            _LOGGER.debug("404 response from update request, logging in...")
            await self.login()
            response = await self._request(request_path, params)
        return response

    async def _set_int_endpoint(
        self, endpoint: IntControlOumanEndpoint, value: int
    ) -> int:
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
            float_result = endpoint.parse_value(result_value)
        except ValueError as err:
            raise OumanClientError(
                f"API returned value cannot be parsed into a float: {result}"
            ) from err

        if float_result != value:
            raise OumanClientError(
                f"Returned float does not match set int value. Got {result_value}, expected {value}"
            )

        return int(float_result)

    async def _set_float_endpoint(
        self, endpoint: FloatControlOumanEndpoint, value: float
    ) -> float:
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
            float_result = endpoint.parse_value(result_value)
        except ValueError as err:
            raise OumanClientError(
                f"API returned value cannot be parsed into a float: {result}"
            ) from err

        if float_result != rounded_value:
            raise OumanClientError(
                f"Returned float does not match set value. Got {result_value}, expected {value}"
            )

        return float_result

    async def _set_enum_endpoint(
        self, endpoint: EnumControlOumanEndpoint, value: ControlEnum
    ) -> ControlEnum:
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
        try:
            enum_result = endpoint.parse_value(result_value)
        except ValueError as err:
            raise OumanClientError(
                f"API returned value cannot be parsed into an enum: {enum_result}"
            ) from err
        return enum_result

    async def set_endpoint_value(
        self,
        endpoint: ControllableEndpoint,
        value: OumanValues | int,
    ) -> OumanValues:
        """Set a value for a controllable endpoint.

        Args:
            endpoint: The controllable endpoint to set.
            value: The value to set for the endpoint.

        Returns:
            The confirmed value from the device.

        Raises:
            TypeError: If the endpoint is not controllable or value type is wrong.
            ValueError: If the value is out of bounds.
        """
        if not isinstance(endpoint, ControllableEndpoint):
            raise TypeError(f"Endpoint {endpoint} is not a controllable endpoint.")

        result: OumanValues
        if isinstance(endpoint, IntControlOumanEndpoint):
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Value for {endpoint.name} must be numeric, got {type(value).__name__}"
                )
            if not value.is_integer():
                raise ValueError(
                    f"Value for {endpoint.name} must be an integer, got {value}"
                )
            result = await self._set_int_endpoint(endpoint, int(value))
        elif isinstance(endpoint, FloatControlOumanEndpoint):
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Value for {endpoint.name} must be numeric, got {type(value).__name__}"
                )
            result = await self._set_float_endpoint(endpoint, value)
        elif isinstance(endpoint, EnumControlOumanEndpoint):
            if not isinstance(value, ControlEnum):
                raise TypeError(
                    f"Value for {endpoint.name} must be a ControlEnum, "
                    f"got {type(value).__name__}"
                )
            result = await self._set_enum_endpoint(endpoint, value)
        else:
            raise NotImplementedError(
                f"No control handler implemented for {type(endpoint).__name__}"
            )

        return result

    async def set_home_away(self, value: HomeAwayControl) -> HomeAwayControl:
        """Set the home/away mode for the system.

        Args:
            value: The home/away mode to set.

        Returns:
            The confirmed home/away mode from the device.
        """
        result = await self._set_enum_endpoint(SystemEndpoints.HOME_AWAY_MODE, value)
        if not isinstance(result, HomeAwayControl):
            raise TypeError(f"Unexpected return type: {type(result).__name__}")
        return result

    async def set_trend_sample_interval(self, value: int) -> int:
        """Set the trend sampling interval.

        Args:
            value: The sampling interval in seconds (30-21600).

        Returns:
            The confirmed sampling interval from the device.
        """
        result = await self._set_int_endpoint(
            SystemEndpoints.TREND_SAMPLE_INTERVAL, value
        )
        return result

    async def get_system_values(self) -> dict[OumanEndpoint, OumanValues]:
        """Get all values from the system endpoints registry.

        Returns:
            A dictionary mapping endpoints to their current values.
        """
        result = await self.get_registry_values([SystemEndpoints])
        return result

    async def set_l1_operation_mode(self, value: OperationMode) -> OperationMode:
        """Set the operation mode for L1 heating circuit.

        Args:
            value: The operation mode to set.

        Returns:
            The confirmed operation mode from the device.
        """
        result = await self._set_enum_endpoint(L1Endpoints.OPERATION_MODE, value)
        if not isinstance(result, OperationMode):
            raise TypeError(f"Unexpected return type: {type(result).__name__}")
        return result

    async def set_l1_valve_position_setpoint(self, position: int) -> int:
        """Set the valve position setpoint for L1 heating circuit.

        Args:
            position: The valve position percentage (0-100).

        Returns:
            The confirmed valve position from the device.
        """
        result = await self._set_int_endpoint(
            L1Endpoints.VALVE_POSITION_SETPOINT, position
        )
        return result

    async def set_l1_curve_minus_20_temp(self, temperature: int) -> int:
        """Set the heating curve temperature at -20°C outdoor temp for L1.

        Args:
            temperature: The supply water temperature in Celsius (0-99).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L1Endpoints.CURVE_MINUS_20_TEMP, temperature
        )
        return result

    async def set_l1_curve_0_temp(self, temperature: int) -> int:
        """Set the heating curve temperature at 0°C outdoor temp for L1.

        Args:
            temperature: The supply water temperature in Celsius (0-99).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(L1Endpoints.CURVE_0_TEMP, temperature)
        return result

    async def set_l1_curve_20_temp(self, temperature: int) -> int:
        """Set the heating curve temperature at +20°C outdoor temp for L1.

        Args:
            temperature: The supply water temperature in Celsius (0-99).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(L1Endpoints.CURVE_20_TEMP, temperature)
        return result

    async def set_l1_temperature_drop(self, temperature: int) -> int:
        """Set the supply water setpoint for "temperature drop" operation mode on L1.

        This is the target supply water temperature used when the L1 heating
        circuit is set to "temperature drop" operation mode.

        Args:
            temperature: The supply water setpoint in Celsius (0-90).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(L1Endpoints.TEMPERATURE_DROP, temperature)
        return result

    async def set_l1_big_temperature_drop(self, temperature: int) -> int:
        """Set the supply water setpoint for "big temperature drop" operation mode on L1.

        This is the target supply water temperature used when the L1 heating
        circuit is set to "big temperature drop" operation mode.

        Args:
            temperature: The supply water setpoint in Celsius (0-90).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L1Endpoints.BIG_TEMPERATURE_DROP, temperature
        )
        return result

    async def set_l1_water_out_minimum_temperature(self, temperature: int) -> int:
        """Set the minimum outgoing water temperature for L1 heating circuit.

        Args:
            temperature: The minimum temperature in Celsius (5-95).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L1Endpoints.WATER_OUT_MIN_TEMP, temperature
        )
        return result

    async def set_l1_water_out_maximum_temperature(self, temperature: int) -> int:
        """Set the maximum outgoing water temperature for L1 heating circuit.

        Args:
            temperature: The maximum temperature in Celsius (5-95).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L1Endpoints.WATER_OUT_MAX_TEMP, temperature
        )
        return result

    async def set_l1_room_temperature_fine_tuning(self, temperature: float) -> float:
        """Set the room temperature fine tuning offset for L1 (without room sensor).

        Args:
            temperature: The fine tuning offset in Celsius (-4.0 to 4.0).

        Returns:
            The confirmed offset from the device.
        """
        result = await self._set_float_endpoint(
            L1Endpoints.ROOM_TEMPERATURE_FINE_TUNING, temperature
        )
        return result

    async def set_l1_room_temperature_fine_tuning_with_sensor(
        self, temperature: float
    ) -> float:
        """Set the room temperature fine tuning offset for L1 (with room sensor).

        Args:
            temperature: The fine tuning offset in Celsius (-4.0 to 4.0).

        Returns:
            The confirmed offset from the device.
        """
        result = await self._set_float_endpoint(
            L1EndpointsWithRoomSensor.ROOM_TEMPERATURE_FINE_TUNING, temperature
        )
        return result

    async def get_l1_values(self) -> dict[OumanEndpoint, OumanValues]:
        """Get all values from the L1 heating circuit endpoints registry.

        Returns:
            A dictionary mapping endpoints to their current values.
        """
        result = await self.get_registry_values([L1Endpoints])
        return result

    async def set_l2_operation_mode(self, value: OperationMode) -> OperationMode:
        """Set the operation mode for L2 heating circuit.

        Args:
            value: The operation mode to set.

        Returns:
            The confirmed operation mode from the device.
        """
        result = await self._set_enum_endpoint(L2Endpoints.OPERATION_MODE, value)
        if not isinstance(result, OperationMode):
            raise TypeError(f"Unexpected return type: {type(result).__name__}")
        return result

    async def set_l2_valve_position_setpoint(self, position: int) -> int:
        """Set the valve position setpoint for L2 heating circuit.

        Args:
            position: The valve position percentage (0-100).

        Returns:
            The confirmed valve position from the device.
        """
        result = await self._set_int_endpoint(
            L2Endpoints.VALVE_POSITION_SETPOINT, position
        )
        return result

    async def set_l2_curve_minus_20_temp(self, temperature: int) -> int:
        """Set the heating curve temperature at -20°C outdoor temp for L2.

        Args:
            temperature: The supply water temperature in Celsius (0-99).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L2Endpoints.CURVE_MINUS_20_TEMP, temperature
        )
        return result

    async def set_l2_curve_0_temp(self, temperature: int) -> int:
        """Set the heating curve temperature at 0°C outdoor temp for L2.

        Args:
            temperature: The supply water temperature in Celsius (0-99).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(L2Endpoints.CURVE_0_TEMP, temperature)
        return result

    async def set_l2_curve_20_temp(self, temperature: int) -> int:
        """Set the heating curve temperature at +20°C outdoor temp for L2.

        Args:
            temperature: The supply water temperature in Celsius (0-99).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(L2Endpoints.CURVE_20_TEMP, temperature)
        return result

    async def set_l2_temperature_drop(self, temperature: int) -> int:
        """Set the supply water setpoint for "temperature drop" operation mode on L2.

        This is the target supply water temperature used when the L2 heating
        circuit is set to "temperature drop" operation mode.

        Args:
            temperature: The supply water setpoint in Celsius (0-90).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(L2Endpoints.TEMPERATURE_DROP, temperature)
        return result

    async def set_l2_big_temperature_drop(self, temperature: int) -> int:
        """Set the supply water setpoint for "big temperature drop" operation mode on L2.

        This is the target supply water temperature used when the L2 heating
        circuit is set to "big temperature drop" operation mode.

        Args:
            temperature: The supply water setpoint in Celsius (0-90).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L2Endpoints.BIG_TEMPERATURE_DROP, temperature
        )
        return result

    async def set_l2_water_out_minimum_temperature(self, temperature: int) -> int:
        """Set the minimum outgoing water temperature for L2 heating circuit.

        Args:
            temperature: The minimum temperature in Celsius (5-95).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L2Endpoints.WATER_OUT_MIN_TEMP, temperature
        )
        return result

    async def set_l2_water_out_maximum_temperature(self, temperature: int) -> int:
        """Set the maximum outgoing water temperature for L2 heating circuit.

        Args:
            temperature: The maximum temperature in Celsius (5-95).

        Returns:
            The confirmed temperature from the device.
        """
        result = await self._set_int_endpoint(
            L2Endpoints.WATER_OUT_MAX_TEMP, temperature
        )
        return result

    async def set_l2_room_temperature_fine_tuning(self, temperature: float) -> float:
        """Set the room temperature fine tuning offset for L2 (without room sensor).

        Args:
            temperature: The fine tuning offset in Celsius (-4.0 to 4.0).

        Returns:
            The confirmed offset from the device.
        """
        result = await self._set_float_endpoint(
            L2Endpoints.ROOM_TEMPERATURE_FINE_TUNING, temperature
        )
        return result

    async def set_l2_room_temperature_fine_tuning_with_sensor(
        self, temperature: float
    ) -> float:
        """Set the room temperature fine tuning offset for L2 (with room sensor).

        Args:
            temperature: The fine tuning offset in Celsius (-4.0 to 4.0).

        Returns:
            The confirmed offset from the device.
        """
        result = await self._set_float_endpoint(
            L2EndpointsWithRoomSensor.ROOM_TEMPERATURE_FINE_TUNING, temperature
        )
        return result

    async def get_l2_values(self) -> dict[OumanEndpoint, OumanValues]:
        """Get all values from the L2 heating circuit endpoints registry.

        Returns:
            A dictionary mapping endpoints to their current values.
        """
        result = await self.get_registry_values([L2Endpoints])
        return result

    async def get_is_l2_installed(self) -> bool:
        """Check if the L2 heating circuit is installed.

        Returns:
            True if L2 is installed, False otherwise.
        """
        endpoint_id = SystemEndpoints.L2_INSTALLED_STATUS.sensor_endpoint_id
        response = await self._get_values([endpoint_id])
        value = response.values.get(endpoint_id)
        if value is None:
            raise ValueError("Response value should be defined")

        # FIXME:
        # This is a temporary solution. It hasn't been tested what the
        # endpoint returns when L2 is installed, so now we
        # just assume that when the value differs from the falsy value,
        # it is means it is truthy and L2 is installed.
        return value != "0"

    async def _get_is_room_sensor_installed(self, endpoint_id: str) -> bool:
        response = await self._get_values([endpoint_id])
        value = response.values.get(endpoint_id)
        if value is None:
            raise ValueError("Response value should be defined")

        # FIXME:
        # This is a temporary solution. It hasn't been tested what the
        # endpoint returns when a room sensor is installed, so now we
        # just assume that when the value differs from the falsy value,
        # it is means it is truthy and a room sensor is installed.
        return value != "off"

    async def get_is_l1_room_sensor_installed(self) -> bool:
        """Check if a room sensor is installed for the L1 heating circuit.

        Returns:
            True if a room sensor is installed, False otherwise.
        """
        return await self._get_is_room_sensor_installed(
            L1Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
        )

    async def get_is_l2_room_sensor_installed(self) -> bool:
        """Check if a room sensor is installed for the L2 heating circuit.

        Returns:
            True if a room sensor is installed, False otherwise.
        """
        return await self._get_is_room_sensor_installed(
            L2Endpoints.ROOM_SENSOR_INSTALLED.sensor_endpoint_id
        )

    async def get_active_registries(self) -> OumanRegistrySet:
        """Get the list of active registries which contain the sets of
        endpoints that can currently be read and written to."""
        registries: list[type[OumanRegistry]] = [SystemEndpoints]
        if await self.get_is_l1_room_sensor_installed():
            registries.append(L1EndpointsWithRoomSensor)
        else:
            registries.append(L1Endpoints)
        if await self.get_is_l2_installed():
            if await self.get_is_l2_room_sensor_installed():
                registries.append(L2EndpointsWithRoomSensor)
            else:
                registries.append(L2Endpoints)
        return OumanRegistrySet(registries)

    async def get_alarms(self) -> Mapping[str, str]:
        """Get all active alarms from the device.

        Returns:
            A mapping of alarm identifiers to their values.
        """
        response = await self._request("alarms", [])
        return response.values

    async def logout(self) -> None:
        """Log out from the Ouman EH-800 device.

        Raises:
            OumanClientError: If the logout fails.
        """
        response = await self._request("logout", [])
        if response.values.get("result") != "ok":
            raise OumanClientError(
                f"Unexpected response from logout request: {response}"
            )
