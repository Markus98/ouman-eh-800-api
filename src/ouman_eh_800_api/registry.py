from collections.abc import Generator, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property

from .const import HomeAwayControl, OperationMode, OumanUnit
from .endpoint import (
    EnumControlOumanEndpoint,
    FloatControlOumanEndpoint,
    IntControlOumanEndpoint,
    NumberOumanEndpoint,
    OumanEndpoint,
)


class OumanRegistry:
    """Base class for endpoint registry definitions.

    Subclasses define endpoints as class attributes.
    """

    @classmethod
    def iterate_endpoints(cls) -> Generator[OumanEndpoint]:
        """Iterate over the OumanEndpoints defined directly on this class."""
        for value in cls.__dict__.values():
            if isinstance(value, OumanEndpoint):
                yield value


@dataclass
class OumanRegistrySet:
    """A collection of registries for querying endpoint values.

    Use this to group registries when calling client.get_values().
    Validates that registries don't have conflicting endpoint IDs.
    """

    registries: Sequence[type[OumanRegistry]]

    def __post_init__(self) -> None:
        if len(self.registries) > len(set(self.registries)):
            raise ValueError("Multiple of the same registry passed")

        if len(self.endpoints) > len(self._sensor_id_endpoint_map):
            raise ValueError("Conflicting endpoint IDs across registries")

    @cached_property
    def endpoints(self) -> Sequence[OumanEndpoint]:
        """All the endpoints in the registry set."""
        return [
            endpoint
            for registry in self.registries
            for endpoint in registry.iterate_endpoints()
        ]

    @cached_property
    def _sensor_id_endpoint_map(self) -> Mapping[str, OumanEndpoint]:
        return {endpoint.sensor_endpoint_id: endpoint for endpoint in self.endpoints}

    @cached_property
    def sensor_endpoint_ids(self) -> Sequence[str]:
        return [endpoint.sensor_endpoint_id for endpoint in self.endpoints]

    def get_endpoint_by_sensor_id(self, id: str) -> OumanEndpoint | None:
        return self._sensor_id_endpoint_map.get(id)


class SystemEndpoints(OumanRegistry):
    """System-wide endpoints for the Ouman EH-800 device."""

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
        unit=None,
        sensor_endpoint_id="S_135_85",
        control_endpoint_ids=("S_135_85", "S_222_85"),
        response_endpoint_ids=("S_222_85",),
        enum_type=HomeAwayControl,
    )

    OUTSIDE_TEMPERATURE = NumberOumanEndpoint(
        name="outside_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_227_85",
    )

    RELAY_CONFIGURATION_TYPE = OumanEndpoint(
        name="relay_configuration_type",
        unit=None,
        sensor_endpoint_id="S_1002_85",
    )

    RELAY_STATUS_TEXT = OumanEndpoint(
        name="relay_status_text",
        unit=None,
        sensor_endpoint_id="S_1004_85",
    )

    L2_INSTALLED_STATUS = OumanEndpoint(
        name="l2_installed_status",
        unit=None,
        sensor_endpoint_id="S_140_85",
    )


class L1BaseEndpoints(OumanRegistry):
    """L1 endpoints that are always queryable regardless of configuration."""

    OPERATION_MODE = EnumControlOumanEndpoint(
        name="l1_operation_mode",
        unit=None,
        sensor_endpoint_id="S_59_85",
        control_endpoint_ids=("S_59_85",),
        response_endpoint_ids=("S_59_85",),
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

    TEMPERATURE_LEVEL_STATUS_TEXT = OumanEndpoint(
        name="l1_temperature_level_status_text",
        unit=None,
        sensor_endpoint_id="S_1000_0",
    )

    CIRCUIT_NAME = OumanEndpoint(
        name="l1_circuit_name",
        unit=None,
        sensor_endpoint_id="S_131_85",
    )

    SUPPLY_WATER_TEMPERATURE = NumberOumanEndpoint(
        name="l1_supply_water_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_259_85",
    )

    VALVE_POSITION = NumberOumanEndpoint(
        name="l1_valve_position",
        unit=OumanUnit.PERCENT,
        sensor_endpoint_id="S_272_85",
    )

    CURVE_SUPPLY_WATER_TEMPERATURE = NumberOumanEndpoint(
        name="l1_curve_supply_water_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_260_85",
    )

    FINE_ADJUSTMENT_EFFECT = NumberOumanEndpoint(
        name="l1_fine_adjustment_effect",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_286_85",
    )

    SUPPLY_WATER_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l1_supply_water_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_275_85",
    )

    ROOM_SENSOR_INSTALLED = OumanEndpoint(
        name="l1_room_sensor_installed",
        unit=None,
        sensor_endpoint_id="S_261_111",
    )


class L1ThreePointCurve(OumanRegistry):
    """L1 3-point heating curve setpoints.

    Mutually exclusive with L1FivePointCurve. Endpoints intentionally share
    `name` with the 5-point counterparts where they overlap (-20, 0, +20).
    """

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


class L1FivePointCurve(OumanRegistry):
    """L1 5-point heating curve setpoints.

    Mutually exclusive with L1ThreePointCurve. The device exposes one set
    or the other based on the Heating curve type setting (manual p.30).
    Endpoints intentionally share `name` with their 3-point counterparts
    where they overlap (-20, 0, +20).
    """

    CURVE_MINUS_20_TEMP = IntControlOumanEndpoint(
        name="l1_curve_minus_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_67_85",
        control_endpoint_id="@_S_67_85",
        min_val=0,
        max_val=99,
    )

    CURVE_MINUS_10_TEMP = IntControlOumanEndpoint(
        name="l1_curve_minus_10_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_69_85",
        control_endpoint_id="@_S_69_85",
        min_val=0,
        max_val=99,
    )

    CURVE_0_TEMP = IntControlOumanEndpoint(
        name="l1_curve_0_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_71_85",
        control_endpoint_id="@_S_71_85",
        min_val=0,
        max_val=99,
    )

    CURVE_10_TEMP = IntControlOumanEndpoint(
        name="l1_curve_10_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_73_85",
        control_endpoint_id="@_S_73_85",
        min_val=0,
        max_val=99,
    )

    CURVE_20_TEMP = IntControlOumanEndpoint(
        name="l1_curve_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_75_85",
        control_endpoint_id="@_S_75_85",
        min_val=0,
        max_val=99,
    )


class L1NoRoomSensor(OumanRegistry):
    """L1 endpoints exposed when no room sensor is installed.

    Mutually exclusive with L1RoomSensor. Endpoints intentionally share
    `name` with their L1RoomSensor counterparts where they overlap
    (TEMPERATURE_DROP, BIG_TEMPERATURE_DROP, ROOM_TEMPERATURE_FINE_TUNING)
    — the user-facing setting is conceptually the same; only the
    underlying control axis differs (supply-water-°C drop without a
    sensor, room-temp-°C drop with one).
    """

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

    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l1_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_134_85",
        control_endpoint_id="@_S_134_85",
        min_val=-4.0,
        max_val=4.0,
    )


class L1RoomSensor(OumanRegistry):
    """L1 endpoints exposed when a room sensor is installed.

    Mutually exclusive with L1NoRoomSensor.
    """

    TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l1_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_87_85",
        control_endpoint_id="@_S_87_85",
        min_val=0,
        max_val=90,
    )

    BIG_TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l1_big_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_88_85",
        control_endpoint_id="@_S_88_85",
        min_val=0,
        max_val=90,
    )

    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l1_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_102_85",
        control_endpoint_id="@_S_102_85",
        min_val=-4.0,
        max_val=4.0,
    )

    ROOM_TEMPERATURE_SETPOINT_USER = IntControlOumanEndpoint(
        name="l1_room_temperature_setpoint_user",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_81_85",
        control_endpoint_id="@_S_81_85",
        min_val=5,
        max_val=50,
    )

    ROOM_SENSOR_POTENTIOMETER = NumberOumanEndpoint(
        name="l1_room_sensor_potentiometer",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_274_85",
    )

    ROOM_TEMPERATURE = NumberOumanEndpoint(
        name="l1_room_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_261_85",
    )

    DELAYED_ROOM_TEMPERATURE = NumberOumanEndpoint(
        name="l1_delayed_room_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_262_85",
    )

    ROOM_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l1_room_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_278_85",
    )


class L1ConstantTempMode(OumanRegistry):
    """L1 endpoints exposed when the heating mode is constant temperature
    controller (manual p.27-28). Additive on top of L1BaseEndpoints; not
    auto-detected — caller opt-in via OumanRegistrySet composition."""

    CONSTANT_TEMP_SETPOINT = IntControlOumanEndpoint(
        name="l1_constant_temp_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_127_85",
        control_endpoint_id="@_S_127_85",
        min_val=0,
        max_val=95,
    )


class L2BaseEndpoints(OumanRegistry):
    """L2 endpoints that are always queryable when L2 is enabled.

    Note: The endpoints in this registry have not been verified against
    a device with L2 hardware installed.
    """

    OPERATION_MODE = EnumControlOumanEndpoint(
        name="l2_operation_mode",
        unit=None,
        sensor_endpoint_id="S_146_85",
        control_endpoint_ids=("S_146_85",),
        response_endpoint_ids=("S_146_85",),
        enum_type=OperationMode,
    )

    VALVE_POSITION_SETPOINT = IntControlOumanEndpoint(
        name="l2_valve_position_setpoint",
        unit=OumanUnit.PERCENT,
        sensor_endpoint_id="S_179_85",
        control_endpoint_id="S_179_85",
        min_val=0,
        max_val=100,
    )

    WATER_OUT_MIN_TEMP = IntControlOumanEndpoint(
        name="l2_water_out_minimum_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_141_85",
        control_endpoint_id="@_S_141_85",
        min_val=5,
        max_val=95,
    )

    WATER_OUT_MAX_TEMP = IntControlOumanEndpoint(
        name="l2_water_out_maximum_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_142_85",
        control_endpoint_id="@_S_142_85",
        min_val=5,
        max_val=95,
    )

    TEMPERATURE_LEVEL_STATUS_TEXT = OumanEndpoint(
        name="l2_temperature_level_status_text",
        unit=None,
        sensor_endpoint_id="S_1001_0",
    )

    CIRCUIT_NAME = OumanEndpoint(
        name="l2_circuit_name",
        unit=None,
        sensor_endpoint_id="S_218_85",
    )

    SUPPLY_WATER_TEMPERATURE = NumberOumanEndpoint(
        name="l2_supply_water_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_293_85",
    )

    VALVE_POSITION = NumberOumanEndpoint(
        name="l2_valve_position",
        unit=OumanUnit.PERCENT,
        sensor_endpoint_id="S_306_85",
    )

    CURVE_SUPPLY_WATER_TEMPERATURE = NumberOumanEndpoint(
        name="l2_curve_supply_water_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_294_85",
    )

    DELAYED_OUTDOOR_TEMPERATURE_EFFECT = NumberOumanEndpoint(
        name="l2_delayed_outdoor_temperature_effect",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_292_85",
    )

    SUPPLY_WATER_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l2_supply_water_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_310_85",
    )

    ROOM_SENSOR_INSTALLED = OumanEndpoint(
        name="l2_room_sensor_installed",
        unit=None,
        sensor_endpoint_id="S_295_111",
    )


class L2ThreePointCurve(OumanRegistry):
    """L2 3-point heating curve setpoints.

    Mutually exclusive with L2FivePointCurve. Shares `name` with the
    5-point counterparts where they overlap (-20, 0, +20).
    """

    CURVE_MINUS_20_TEMP = IntControlOumanEndpoint(
        name="l2_curve_minus_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_148_85",
        control_endpoint_id="@_S_148_85",
        min_val=0,
        max_val=99,
    )

    CURVE_0_TEMP = IntControlOumanEndpoint(
        name="l2_curve_0_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_150_85",
        control_endpoint_id="@_S_150_85",
        min_val=0,
        max_val=99,
    )

    CURVE_20_TEMP = IntControlOumanEndpoint(
        name="l2_curve_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_152_85",
        control_endpoint_id="@_S_152_85",
        min_val=0,
        max_val=99,
    )


class L2FivePointCurve(OumanRegistry):
    """L2 5-point heating curve setpoints.

    Mutually exclusive with L2ThreePointCurve.
    """

    CURVE_MINUS_20_TEMP = IntControlOumanEndpoint(
        name="l2_curve_minus_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_154_85",
        control_endpoint_id="@_S_154_85",
        min_val=0,
        max_val=99,
    )

    CURVE_MINUS_10_TEMP = IntControlOumanEndpoint(
        name="l2_curve_minus_10_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_156_85",
        control_endpoint_id="@_S_156_85",
        min_val=0,
        max_val=99,
    )

    CURVE_0_TEMP = IntControlOumanEndpoint(
        name="l2_curve_0_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_158_85",
        control_endpoint_id="@_S_158_85",
        min_val=0,
        max_val=99,
    )

    CURVE_10_TEMP = IntControlOumanEndpoint(
        name="l2_curve_10_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_160_85",
        control_endpoint_id="@_S_160_85",
        min_val=0,
        max_val=99,
    )

    CURVE_20_TEMP = IntControlOumanEndpoint(
        name="l2_curve_20_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_162_85",
        control_endpoint_id="@_S_162_85",
        min_val=0,
        max_val=99,
    )


class L2NoRoomSensor(OumanRegistry):
    """L2 endpoints exposed when no room sensor is installed.

    Mutually exclusive with L2RoomSensor.
    """

    TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l2_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_176_85",
        control_endpoint_id="@_S_176_85",
        min_val=0,
        max_val=90,
    )

    BIG_TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l2_big_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_177_85",
        control_endpoint_id="@_S_177_85",
        min_val=0,
        max_val=90,
    )

    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l2_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_221_85",
        control_endpoint_id="@_S_221_85",
        min_val=-4.0,
        max_val=4.0,
    )


class L2RoomSensor(OumanRegistry):
    """L2 endpoints exposed when a room sensor is installed.

    Mutually exclusive with L2NoRoomSensor.
    """

    TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l2_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_174_85",
        control_endpoint_id="@_S_174_85",
        min_val=0,
        max_val=90,
    )

    BIG_TEMPERATURE_DROP = IntControlOumanEndpoint(
        name="l2_big_temperature_drop",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_175_85",
        control_endpoint_id="@_S_175_85",
        min_val=0,
        max_val=90,
    )

    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l2_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_189_85",
        control_endpoint_id="@_S_189_85",
        min_val=-4.0,
        max_val=4.0,
    )

    ROOM_TEMPERATURE_SETPOINT_USER = IntControlOumanEndpoint(
        name="l2_room_temperature_setpoint_user",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_168_85",
        control_endpoint_id="@_S_168_85",
        min_val=5,
        max_val=50,
    )

    ROOM_TEMPERATURE = NumberOumanEndpoint(
        name="l2_room_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_295_85",
    )

    DELAYED_ROOM_TEMPERATURE = NumberOumanEndpoint(
        name="l2_delayed_room_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_296_85",
    )

    ROOM_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l2_room_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_313_85",
    )
