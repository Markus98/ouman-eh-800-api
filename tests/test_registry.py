import pytest

from ouman_eh_800_api.const import OumanUnit
from ouman_eh_800_api.endpoint import NumberOumanEndpoint
from ouman_eh_800_api.registry import (
    L1BaseEndpoints,
    L1NoRoomSensor,
    L1RoomSensor,
    L2BaseEndpoints,
    OumanRegistry,
    OumanRegistrySet,
    SystemEndpoints,
)

# =============================================================================
# Test fixtures - custom registries for testing validation
# =============================================================================


class TestRegistryA(OumanRegistry):
    ENDPOINT_1 = NumberOumanEndpoint(
        name="test_endpoint_1",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_TEST_1",
    )
    ENDPOINT_2 = NumberOumanEndpoint(
        name="test_endpoint_2",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_TEST_2",
    )


class TestRegistryB(OumanRegistry):
    ENDPOINT_3 = NumberOumanEndpoint(
        name="test_endpoint_3",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_TEST_3",
    )


class TestRegistryConflicting(OumanRegistry):
    """Registry with an endpoint that conflicts with TestRegistryA"""

    ENDPOINT_CONFLICT = NumberOumanEndpoint(
        name="test_endpoint_conflict",
        unit=OumanUnit.PERCENT,
        sensor_endpoint_id="S_TEST_1",  # Same as TestRegistryA.ENDPOINT_1
    )


class TestRegistryChild(TestRegistryA):
    """Child registry that inherits from TestRegistryA and overrides ENDPOINT_1"""

    ENDPOINT_1 = NumberOumanEndpoint(
        name="test_endpoint_1_override",
        unit=OumanUnit.PERCENT,
        sensor_endpoint_id="S_TEST_1_OVERRIDE",
    )

    ENDPOINT_4 = NumberOumanEndpoint(
        name="test_endpoint_4",
        unit=OumanUnit.CELSIUS,
        sensor_endpoint_id="S_TEST_4",
    )


# =============================================================================
# Tests for OumanRegistrySet.__post_init__
# =============================================================================


def test_registry_set_valid_single_registry():
    """Creating a registry set with a single valid registry should succeed."""
    registry_set = OumanRegistrySet([SystemEndpoints])

    assert SystemEndpoints in registry_set.registries
    assert len(registry_set.endpoints) > 0


def test_registry_set_valid_multiple_registries():
    """Creating a registry set with multiple non-conflicting registries should succeed."""
    registry_set = OumanRegistrySet([TestRegistryA, TestRegistryB])

    assert TestRegistryA in registry_set.registries
    assert TestRegistryB in registry_set.registries
    assert len(registry_set.endpoints) == 3


def test_registry_set_duplicate_registry_raises():
    """Passing the same registry multiple times should raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OumanRegistrySet([SystemEndpoints, SystemEndpoints])

    assert "Multiple of the same registry" in str(exc_info.value)


def test_registry_set_conflicting_endpoint_ids_raises():
    """Passing registries with conflicting sensor_endpoint_ids should raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        OumanRegistrySet([TestRegistryA, TestRegistryConflicting])

    assert "Conflicting endpoint IDs" in str(exc_info.value)


def test_registry_set_empty_registries():
    """Creating a registry set with an empty list should succeed."""
    registry_set = OumanRegistrySet([])

    assert len(registry_set.registries) == 0
    assert len(registry_set.endpoints) == 0


# =============================================================================
# Tests for OumanRegistrySet properties
# =============================================================================


def test_registry_set_endpoints_property():
    """The endpoints property should return all endpoints from all registries."""
    registry_set = OumanRegistrySet([TestRegistryA, TestRegistryB])

    endpoints = registry_set.endpoints

    assert len(endpoints) == 3
    assert TestRegistryA.ENDPOINT_1 in endpoints
    assert TestRegistryA.ENDPOINT_2 in endpoints
    assert TestRegistryB.ENDPOINT_3 in endpoints


def test_registry_set_sensor_endpoint_ids_property():
    """The sensor_endpoint_ids property should return all sensor IDs."""
    registry_set = OumanRegistrySet([TestRegistryA, TestRegistryB])

    sensor_ids = registry_set.sensor_endpoint_ids

    assert len(sensor_ids) == 3
    assert "S_TEST_1" in sensor_ids
    assert "S_TEST_2" in sensor_ids
    assert "S_TEST_3" in sensor_ids


def test_registry_set_get_endpoint_by_sensor_id():
    """get_endpoint_by_sensor_id should return the correct endpoint."""
    registry_set = OumanRegistrySet([TestRegistryA, TestRegistryB])

    endpoint = registry_set.get_endpoint_by_sensor_id("S_TEST_1")

    assert endpoint == TestRegistryA.ENDPOINT_1


def test_registry_set_get_endpoint_by_sensor_id_not_found():
    """get_endpoint_by_sensor_id should return None for unknown IDs."""
    registry_set = OumanRegistrySet([TestRegistryA])

    endpoint = registry_set.get_endpoint_by_sensor_id("UNKNOWN_ID")

    assert endpoint is None


# =============================================================================
# Tests for real registry combinations
# =============================================================================


def test_registry_set_system_and_l1_base():
    """SystemEndpoints and L1BaseEndpoints should not conflict."""
    registry_set = OumanRegistrySet([SystemEndpoints, L1BaseEndpoints])

    assert len(registry_set.endpoints) > 0
    assert SystemEndpoints.OUTSIDE_TEMPERATURE in registry_set.endpoints
    assert L1BaseEndpoints.OPERATION_MODE in registry_set.endpoints


def test_registry_set_l1_and_l2_bases():
    """L1BaseEndpoints and L2BaseEndpoints should not conflict."""
    registry_set = OumanRegistrySet([L1BaseEndpoints, L2BaseEndpoints])

    assert len(registry_set.endpoints) > 0


# =============================================================================
# Tests for OumanRegistry.iterate_endpoints (inheritance and overriding)
# =============================================================================


def test_iterate_endpoints_returns_all_endpoints():
    """iterate_endpoints should return all endpoints defined in the registry."""
    endpoints = list(TestRegistryA.iterate_endpoints())

    assert len(endpoints) == 2
    assert TestRegistryA.ENDPOINT_1 in endpoints
    assert TestRegistryA.ENDPOINT_2 in endpoints


def test_iterate_endpoints_child_includes_parent_endpoints():
    """iterate_endpoints on child should include inherited parent endpoints."""
    endpoints = list(TestRegistryChild.iterate_endpoints())

    # Should have: overridden ENDPOINT_1, inherited ENDPOINT_2, new ENDPOINT_4
    assert len(endpoints) == 3
    assert TestRegistryA.ENDPOINT_2 in endpoints
    assert TestRegistryChild.ENDPOINT_4 in endpoints


def test_iterate_endpoints_child_overrides_parent_endpoint():
    """iterate_endpoints on child should use child's version of overridden endpoints."""
    endpoints = list(TestRegistryChild.iterate_endpoints())

    # Should contain the child's ENDPOINT_1, not the parent's
    assert TestRegistryChild.ENDPOINT_1 in endpoints
    assert TestRegistryA.ENDPOINT_1 not in endpoints

    # Verify the override has the new sensor_endpoint_id
    endpoint_1 = next(e for e in endpoints if e.name == "test_endpoint_1_override")
    assert endpoint_1.sensor_endpoint_id == "S_TEST_1_OVERRIDE"


def test_l1_no_room_sensor_and_room_sensor_share_drop_names():
    """L1NoRoomSensor and L1RoomSensor define endpoints with the same `name`
    but different sensor IDs (TEMPERATURE_DROP, BIG_TEMPERATURE_DROP,
    ROOM_TEMPERATURE_FINE_TUNING). The shared name is intentional — the
    user-facing setting is conceptually one thing per circuit."""
    no_sensor_drop = L1NoRoomSensor.TEMPERATURE_DROP
    room_sensor_drop = L1RoomSensor.TEMPERATURE_DROP

    assert no_sensor_drop.name == room_sensor_drop.name == "l1_temperature_drop"
    assert no_sensor_drop.sensor_endpoint_id == "S_89_85"
    assert room_sensor_drop.sensor_endpoint_id == "S_87_85"


def test_l1_room_sensor_has_room_specific_endpoints():
    """L1RoomSensor exposes endpoints that have no L1NoRoomSensor counterpart."""
    names = {e.name for e in L1RoomSensor.iterate_endpoints()}

    assert "l1_room_temperature" in names
    assert "l1_room_temperature_setpoint" in names
    assert "l1_room_sensor_potentiometer" in names
    assert "l1_delayed_room_temperature" in names
    assert "l1_room_temperature_setpoint_user" in names
