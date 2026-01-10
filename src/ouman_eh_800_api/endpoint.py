from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from .const import OumanUnit, OperationMode, HomeAwayControl


@dataclass
class OumanEndpoint:
    name: str
    unit: OumanUnit
    sensor_endpoint_id: str


class NumberOumanEndpoint(OumanEndpoint):
    pass


@dataclass
class EnumControlOumanEndpoint(OumanEndpoint):
    control_endpoint_ids: Sequence[str]
    response_endpoint_ids: Sequence[str]
    enum_type: type[StrEnum]


@dataclass
class IntControlOumanEndpoint(NumberOumanEndpoint):
    control_endpoint_id: str
    min_val: int
    max_val: int


@dataclass
class FloatControlOumanEndpoint(NumberOumanEndpoint):
    control_endpoint_id: str
    min_val: float
    max_val: float


class L1Endpoints:
    OPERATION_MODE = EnumControlOumanEndpoint(
        name="l1_operation_mode",
        unit=OumanUnit.ENUM,
        sensor_endpoint_id="S_59_85",
        control_endpoint_ids=["S_59_85"],
        response_endpoint_ids=["S_59_85"],
        enum_type=OperationMode,
    )

    VALVE_POSITION_SETPOINT = IntControlOumanEndpoint(
        name="l1_valve_position_setpoint",
        unit=OumanUnit.PERCENT,
        sensor_endpoint_id="S_92_85",
        control_endpoint_id="S_92_85",
        min_val=0,
        max_val=100,
    )

    CURVE_MINUS_20_TEMP = IntControlOumanEndpoint(
        name="l1_curve_minus_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_61_85",
        control_endpoint_id="@_S_61_85",
        min_val=0,
        max_val=99,
    )

    CURVE_0_TEMP = IntControlOumanEndpoint(
        name="l1_curve_0_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_63_85",
        control_endpoint_id="@_S_63_85",
        min_val=0,
        max_val=99,
    )

    CURVE_20_TEMP = IntControlOumanEndpoint(
        name="l1_curve_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_65_85",
        control_endpoint_id="@_S_65_85",
        min_val=0,
        max_val=99,
    )

    TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l1_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_89_85",
        control_endpoint_id="@_S_89_85",
        min_val=0,
        max_val=90,
    )

    BIG_TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l1_big_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_90_85",
        control_endpoint_id="@_S_90_85",
        min_val=0,
        max_val=90,
    )

    WATER_OUT_MIN_TEMP = IntControlOumanEndpoint(
        name="l1_water_out_minimum_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_54_85",
        control_endpoint_id="@_S_54_85",
        min_val=5,
        max_val=95,
    )

    WATER_OUT_MAX_TEMP = IntControlOumanEndpoint(
        name="l1_water_out_maximum_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_55_85",
        control_endpoint_id="@_S_55_85",
        min_val=5,
        max_val=95,
    )

    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l1_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_134_85",
        control_endpoint_id="@_S_134_85",
        min_val=-4.0,
        max_val=4.0,
    )

    ROOM_TEMPERATURE_FINE_TUNING_WITH_SENSOR = FloatControlOumanEndpoint(
        name="l1_room_temperature_fine_tuning_with_sensor",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_102_85",
        control_endpoint_id="@_S_102_85",
        min_val=-4.0,
        max_val=4.0,
    )


class SystemEndpoints:
    TREND_SAMPLE_INTERVAL = IntControlOumanEndpoint(
        name="trend_sampling_interval",
        unit=OumanUnit.SECOND,
        sensor_endpoint_id="S_26_85",
        control_endpoint_id="@_S_26_85",
        min_val=30,
        max_val=21600,
    )

    HOME_AWAY_MODE = EnumControlOumanEndpoint(
        name="home_away_mode",
        unit=OumanUnit.ENUM,
        sensor_endpoint_id="S_135_85",
        control_endpoint_ids=["S_135_85", "S_222_85"],
        response_endpoint_ids=["S_222_85"],
        enum_type=HomeAwayControl,
    )
