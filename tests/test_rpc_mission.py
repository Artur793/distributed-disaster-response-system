from app.common.models import (
    IncidentType,
    Mission,
    Position,
    Vehicle,
    VehicleType,
)
from app.common.state import SystemState


def test_assign_mission_updates_vehicle_and_mission():
    state = SystemState()

    vehicle = Vehicle(
        id="rover-1",
        vehicle_type=VehicleType.ROVER,
        rpc_host="localhost",
        rpc_port=50051,
    )

    mission = Mission(
        id="mission-1",
        incident_id="incident-1",
        incident_type=IncidentType.VIBRATION_ALERT,
        target_position=Position(1, 1),
        priority=1,
        area_type="LAND",
    )

    state.register_vehicle(vehicle)
    state.add_mission(mission)

    state.assign_mission("mission-1", "rover-1")

    updated_vehicle = state.get_vehicle("rover-1")
    updated_mission = state.get_mission("mission-1")

    assert updated_vehicle.assigned_mission_id == "mission-1"
    assert updated_vehicle.status == "ASSIGNED"

    assert updated_mission.assigned_vehicle_id == "rover-1"
    assert updated_mission.status == "ASSIGNED"


def test_vehicle_becomes_idle_again():
    state = SystemState()

    vehicle = Vehicle(
        id="rover-1",
        vehicle_type=VehicleType.ROVER,
        rpc_host="localhost",
        rpc_port=50051,
    )

    state.register_vehicle(vehicle)

    state.update_vehicle_status(
        "rover-1",
        "ERROR",
        50,
        "motor issue",
    )

    assert state.idle_vehicles("rover") == []

    state.update_vehicle_status(
        "rover-1",
        "IDLE",
        100,
        "recovered",
    )

    idle = state.idle_vehicles("rover")

    assert len(idle) == 1
    assert idle[0].id == "rover-1"