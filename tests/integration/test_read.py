"""Read-only integration tests against a real Ouman EH-800 device.

These tests only query the device; they never write. Safe to run against
a live heating system.

Run with `make integration` (or `pytest -s tests/integration/`) to see the
printed endpoint → value dumps for visual debugging.
"""

from collections.abc import Mapping

import pytest

from ouman_eh_800_api.client import OumanEh800Client
from ouman_eh_800_api.endpoint import (
    EnumControlOumanEndpoint,
    NumberOumanEndpoint,
    OumanEndpoint,
)
from ouman_eh_800_api.registry import (
    L1BaseEndpoints,
    L1ConstantTempMode,
    L1FivePointCurve,
    L1NoRoomSensor,
    L1RoomSensor,
    L1ThreePointCurve,
    L2BaseEndpoints,
    L2FivePointCurve,
    L2NoRoomSensor,
    L2RoomSensor,
    L2ThreePointCurve,
    OumanRegistry,
    OumanRegistrySet,
    RelayL1ValvePosition,
    RelayPumpSummerStop,
    RelayTempDifference,
    RelayTemperature,
    RelayTimeProgram,
    SystemEndpoints,
)

ALL_REGISTRIES: list[type[OumanRegistry]] = [
    SystemEndpoints,
    L1BaseEndpoints,
    L1ThreePointCurve,
    L1FivePointCurve,
    L1NoRoomSensor,
    L1RoomSensor,
    L1ConstantTempMode,
    L2BaseEndpoints,
    L2ThreePointCurve,
    L2FivePointCurve,
    L2NoRoomSensor,
    L2RoomSensor,
    RelayPumpSummerStop,
    RelayTemperature,
    RelayTempDifference,
    RelayL1ValvePosition,
    RelayTimeProgram,
]

pytestmark = pytest.mark.integration


def _print_values(title: str, values: Mapping[OumanEndpoint, object]) -> None:
    print(f"\n--- {title} ({len(values)} endpoints) ---")
    if not values:
        print("  (empty)")
        return
    name_w = max(len(e.name) for e in values)
    id_w = max(len(e.sensor_endpoint_id) for e in values)
    for endpoint, value in values.items():
        unit = f" {endpoint.unit.value}" if endpoint.unit else ""
        print(
            f"  {endpoint.name:<{name_w}}  "
            f"{endpoint.sensor_endpoint_id:<{id_w}}  "
            f"= {value!r}{unit}"
        )


def _assert_values_match_registry(
    values: Mapping[OumanEndpoint, object], registry_set: OumanRegistrySet
) -> None:
    """Every endpoint in the registry set should have a value, parsed to the
    expected type."""
    _print_values(", ".join(r.__name__ for r in registry_set.registries), values)
    for endpoint in registry_set.endpoints:
        assert endpoint in values, f"Missing value for {endpoint.name}"
        value = values[endpoint]
        if isinstance(endpoint, EnumControlOumanEndpoint):
            assert isinstance(value, endpoint.enum_type), (
                f"{endpoint.name}: expected {endpoint.enum_type}, got {type(value)}"
            )
        elif isinstance(endpoint, NumberOumanEndpoint):
            assert isinstance(value, float), (
                f"{endpoint.name}: expected float, got {type(value)}"
            )
        else:
            assert isinstance(value, str), (
                f"{endpoint.name}: expected str, got {type(value)}"
            )


async def test_client_can_log_in_and_out(client: OumanEh800Client) -> None:
    """The `client` fixture handles login/logout. Reaching this point proves
    the handshake works end-to-end."""
    # Do one trivial request to confirm the session is usable.
    alarms = await client.get_alarms()
    print(f"\nalarms: {alarms!r}")
    assert isinstance(alarms, dict)


@pytest.mark.parametrize("registry", ALL_REGISTRIES, ids=lambda r: r.__name__)
async def test_get_registry_values(
    client: OumanEh800Client, registry: type[OumanRegistry]
) -> None:
    registry_set = OumanRegistrySet([registry])
    values = await client.get_values(registry_set)
    _assert_values_match_registry(values, registry_set)


async def test_get_is_l2_installed_returns_bool(client: OumanEh800Client) -> None:
    result = await client.get_is_l2_installed()
    print(f"\nis_l2_installed: {result!r}")
    assert isinstance(result, bool)


async def test_get_is_l1_room_sensor_installed_returns_bool(
    client: OumanEh800Client,
) -> None:
    result = await client.get_is_l1_room_sensor_installed()
    print(f"\nis_l1_room_sensor_installed: {result!r}")
    assert isinstance(result, bool)


async def test_get_is_l2_room_sensor_installed_returns_bool(
    client: OumanEh800Client,
) -> None:
    result = await client.get_is_l2_room_sensor_installed()
    print(f"\nis_l2_room_sensor_installed: {result!r}")
    assert isinstance(result, bool)


async def test_get_active_registries_matches_hardware(
    client: OumanEh800Client,
) -> None:
    registry_set = await client.get_active_registries()
    registries = set(registry_set.registries)
    print(f"\nactive registries: {[r.__name__ for r in registry_set.registries]}")

    assert SystemEndpoints in registries
    assert L1BaseEndpoints in registries

    l1_three = L1ThreePointCurve in registries
    l1_five = L1FivePointCurve in registries
    assert l1_three != l1_five, "Exactly one L1 curve fragment must be active"

    l1_no_sensor = L1NoRoomSensor in registries
    l1_sensor = L1RoomSensor in registries
    assert l1_no_sensor != l1_sensor, "Exactly one L1 sensor fragment must be active"
    assert l1_sensor == await client.get_is_l1_room_sensor_installed()

    if await client.get_is_l2_installed():
        assert L2BaseEndpoints in registries
        assert (L2ThreePointCurve in registries) != (L2FivePointCurve in registries)
        l2_no_sensor = L2NoRoomSensor in registries
        l2_sensor = L2RoomSensor in registries
        assert l2_no_sensor != l2_sensor
        assert l2_sensor == await client.get_is_l2_room_sensor_installed()
    else:
        assert L2BaseEndpoints not in registries
        assert L2ThreePointCurve not in registries
        assert L2FivePointCurve not in registries
        assert L2NoRoomSensor not in registries
        assert L2RoomSensor not in registries


async def test_get_values_with_active_registries(client: OumanEh800Client) -> None:
    """Full end-to-end flow: detect installed hardware, then fetch all values
    for active registries in a single request."""
    registry_set = await client.get_active_registries()
    values = await client.get_values(registry_set)
    _assert_values_match_registry(values, registry_set)


async def test_get_alarms_returns_mapping(client: OumanEh800Client) -> None:
    alarms = await client.get_alarms()
    print(f"\nalarms: {alarms!r}")
    assert isinstance(alarms, dict)
    for key, value in alarms.items():
        assert isinstance(key, str)
        assert isinstance(value, str)
