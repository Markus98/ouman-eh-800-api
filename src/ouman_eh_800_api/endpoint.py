from dataclasses import dataclass
from typing import Sequence

from .const import ControlEnum, OumanUnit

OumanValues = str | float | ControlEnum


@dataclass(frozen=True)
class OumanEndpoint:
    name: str
    unit: OumanUnit | None
    sensor_endpoint_id: str

    def parse_value(self, value: str) -> OumanValues:
        return value


class ControllableEndpoint:
    """Base marker for all writable endpoints."""

    pass


class NumberOumanEndpoint(OumanEndpoint):
    def parse_value(self, value: str) -> float:
        return float(value)


@dataclass(frozen=True)
class EnumControlOumanEndpoint(OumanEndpoint, ControllableEndpoint):
    control_endpoint_ids: Sequence[str]
    response_endpoint_ids: Sequence[str]
    enum_type: type[ControlEnum]

    def parse_value(self, value: str) -> ControlEnum:
        return self.enum_type(value)


@dataclass(frozen=True)
class IntControlOumanEndpoint(NumberOumanEndpoint, ControllableEndpoint):
    control_endpoint_id: str
    min_val: int
    max_val: int


@dataclass(frozen=True)
class FloatControlOumanEndpoint(NumberOumanEndpoint, ControllableEndpoint):
    control_endpoint_id: str
    min_val: float
    max_val: float
