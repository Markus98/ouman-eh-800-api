from functools import lru_cache
from typing import Generator, Mapping, Sequence

from .const import HomeAwayControl, OperationMode, OumanUnit
from .endpoint import (
    EnumControlOumanEndpoint,
    FloatControlOumanEndpoint,
    IntControlOumanEndpoint,
    NumberOumanEndpoint,
    OumanEndpoint,
)


class OumanRegistry:
    @classmethod
    def iterate_endpoints(cls) -> Generator[OumanEndpoint, None, None]:
        """Iterate over all OumanEndpoints in this class and its
        parents. Subclass definitions override parent class
        definitions."""
        seen_keys = set()
        for base in cls.mro():
            for key, value in base.__dict__.items():
                # Avoid yielding the same endpoint twice if overridden
                if key not in seen_keys and isinstance(value, OumanEndpoint):
                    seen_keys.add(key)
                    yield value

    @classmethod
    @lru_cache(maxsize=1)
    def get_sensor_endpoint_ids(cls) -> Sequence[str]:
        """Get all sensor endpoint IDs in this registry"""
        return [endpoint.sensor_endpoint_id for endpoint in cls.iterate_endpoints()]

    @classmethod
    @lru_cache(maxsize=1)
    def _sensor_id_endpoint_map(cls) -> Mapping[str, OumanEndpoint]:
        return {
            endpoint.sensor_endpoint_id: endpoint
            for endpoint in cls.iterate_endpoints()
        }

    @classmethod
    def get_endpoint_by_sensor_id(cls, sensor_endpoint_id: str) -> OumanEndpoint | None:
        """Get an endpoint based on it's sensor_endpoint_id"""
        return cls._sensor_id_endpoint_map().get(sensor_endpoint_id)


class SystemEndpoints(OumanRegistry):
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


class L1Endpoints(OumanRegistry):
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

    HEATING_SHUTDOWN_STATUS = OumanEndpoint(
        name="l1_heating_shutdown_status",
        unit=None,
        sensor_endpoint_id="S_0_0",
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

    SUPPLY_WATER_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l1_supply_water_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_275_85",
    )

    # TODO: make this into an enum endpoint when we know what other
    # values are possible besides "off"
    ROOM_SENSOR_INSTALLED = OumanEndpoint(
        name="l1_room_sensor_installed",
        unit=None,
        sensor_endpoint_id="S_261_111",
    )


# NOTE: Functionality not verified.
class L1EndpointsWithRoomSensor(L1Endpoints):
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

    ROOM_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l1_room_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_278_85",
    )

    # NOTE: This overrides the one in L1Endpoints since the control
    # endpoint is different when a room sensor is installed.
    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l1_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_102_85",
        control_endpoint_id="@_S_102_85",
        min_val=-4.0,
        max_val=4.0,
    )


# NOTE: L2 functionality not verified
class L2Endpoints(OumanRegistry):
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

    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l2_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_221_85",
        control_endpoint_id="@_S_221_85",
        min_val=-4.0,
        max_val=4.0,
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

    SUPPLY_WATER_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l2_supply_water_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_310_85",
    )

    # TODO: make this into an enum endpoint when we know what other
    # values are possible besides "off"
    ROOM_SENSOR_INSTALLED = OumanEndpoint(
        name="l2_room_sensor_installed",
        unit=None,
        sensor_endpoint_id="S_295_111",
    )


class L2EndpointsWithRoomSensor(L2Endpoints):
    ROOM_SENSOR_POTENTIOMETER = NumberOumanEndpoint(
        name="l2_room_sensor_potentiometer",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_307_85",
    )

    ROOM_TEMPERATURE = NumberOumanEndpoint(
        name="l2_room_temperature",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_295_85",
    )

    ROOM_TEMPERATURE_SETPOINT = NumberOumanEndpoint(
        name="l2_room_temperature_setpoint",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_313_85",
    )

    # NOTE: This overrides the one in L2Endpoints since the control
    # endpoint is different when a room sensor is installed.
    ROOM_TEMPERATURE_FINE_TUNING = FloatControlOumanEndpoint(
        name="l2_room_temperature_fine_tuning",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_189_85",
        control_endpoint_id="@_S_189_85",
        min_val=-4.0,
        max_val=4.0,
    )
