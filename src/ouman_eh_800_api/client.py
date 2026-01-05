import asyncio
import logging
from typing import NamedTuple

import aiohttp
from aiohttp import ClientSession

from .const import ENDPOINT_VALUE_MAPPING, ENDPOINTS
from .exceptions import (
    OumanClientAuthenticationError,
    OumanClientCommunicationError,
    OumanClientError,
)

_LOGGER = logging.getLogger(__name__)


class OumanResponse(NamedTuple):
    prefix: str
    values: dict[str, str]


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

    def _construct_request_url(self, path: str, params: list[str]) -> str:
        base = f"{self._address}/{path}?"
        request_url = base + ";".join(params)
        return request_url

    async def _request(self, path: str, params: list[str]) -> OumanResponse:
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

    async def _login(self) -> OumanResponse:
        response = await self._request(
            "login", [f"uid={self._username}", f"pwd={self._password}"]
        )

        if response.values.get("result") == "ok":
            _LOGGER.debug("Successful login")
        elif response.values.get("result") == "error":
            raise OumanClientAuthenticationError("Wrong username or password")
        else:
            raise OumanClientError(f"Unexpected response from login request: {response}")
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

    async def update_values(self) -> OumanResponse:
        request_path = "update"
        # TODO: move params var to acutal params
        params = ["S_135_85=0","S_222_85=0"]
        try:
            response = await self._request(request_path, params)
        except OumanClientCommunicationError as err:
            if not isinstance(err.__cause__, aiohttp.ClientResponseError):
                raise
            if err.__cause__.status == 404:
                _LOGGER.debug("404 response from update request, logging in...")
                await self._login()
                response = await self._request(request_path, params)
        return response

    async def get_alarms(self):
        raise NotImplementedError()

    async def get_available_settings(self):
        raise NotImplementedError()

    async def get_available_waterinfo(self):
        raise NotImplementedError()

    async def get_available_relay(self):
        raise NotImplementedError()

