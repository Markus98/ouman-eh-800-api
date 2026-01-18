from dataclasses import dataclass
from typing import Sequence

from .const import ControlEnum, OumanUnit

OumanValues = str | float | ControlEnum
"""Type alias for possible endpoint values: string, float, or a control enum."""


@dataclass(frozen=True)
class OumanEndpoint:
    """Base class for all Ouman device endpoints.

    Attributes:
        name: Human-readable name of the endpoint.
        unit: Unit of measurement, or None if not applicable.
        sensor_endpoint_id: The device API identifier for reading this endpoint.
    """

    name: str
    unit: OumanUnit | None
    sensor_endpoint_id: str

    def parse_value(self, value: str) -> OumanValues:
        return value


class ControllableEndpoint:
    """Base marker class for all writable endpoints."""

    pass


class NumberOumanEndpoint(OumanEndpoint):
    """Endpoint that returns numeric (float) values."""

    def parse_value(self, value: str) -> float:
        return float(value)


@dataclass(frozen=True)
class EnumControlOumanEndpoint(OumanEndpoint, ControllableEndpoint):
    """Controllable endpoint that accepts enum values.

    Attributes:
        control_endpoint_ids: API identifiers for writing to this endpoint.
        response_endpoint_ids: API identifiers expected in the response.
        enum_type: The enum class for valid values.
    """

    control_endpoint_ids: Sequence[str]
    response_endpoint_ids: Sequence[str]
    enum_type: type[ControlEnum]

    def parse_value(self, value: str) -> ControlEnum:
        return self.enum_type(value)


@dataclass(frozen=True)
class IntControlOumanEndpoint(NumberOumanEndpoint, ControllableEndpoint):
    """Controllable endpoint that accepts integer values.

    Attributes:
        control_endpoint_id: API identifier for writing to this endpoint.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
    """

    control_endpoint_id: str
    min_val: int
    max_val: int


@dataclass(frozen=True)
class FloatControlOumanEndpoint(NumberOumanEndpoint, ControllableEndpoint):
    """Controllable endpoint that accepts float values.

    Attributes:
        control_endpoint_id: API identifier for writing to this endpoint.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
    """

    control_endpoint_id: str
    min_val: float
    max_val: float
