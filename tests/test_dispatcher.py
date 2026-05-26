import pytest

from app.common.models import Incident, IncidentType, Mission, Position, Vehicle, VehicleType
from app.common.state import SystemState
from app.control_center.dispatcher import DispatchCoordinator


@pytest.mark.parametrize(
    ("incident_type", "area_type", "expected_vehicle_type"),
    [
        (IncidentType.PERSON_DETECTED, "LAND", "rover"),
        (IncidentType.PERSON_DETECTED, "WATER", "boat"),
        (IncidentType.VIBRATION_ALERT, "LAND", "rover"),
        (IncidentType.WATER_LEVEL_ALERT, "WATER", "drone"),
    ],
)
def test_required_vehicle_type(
    incident_type,
    area_type,
    expected_vehicle_type,
):
    mission = Mission(
        id="incident-1",
        incident_id="incident-1",
        incident_type=incident_type,
        target_position=Position(1, 1),
        priority=1,
        area_type=area_type,
    )

    assert DispatchCoordinator._required_vehicle_type(mission) == expected_vehicle_type


def configured_state() -> SystemState:
    state = SystemState()
    state.register_vehicle(
        Vehicle(
            id="rover-1",
            vehicle_type=VehicleType.ROVER,
            rpc_host="vehicle-rover",
            rpc_port=50051,
        )
    )
    state.add_incident(
        Incident(
            id="incident-1",
            incident_type=IncidentType.VIBRATION_ALERT,
            source_id="sensor-1",
            message="Damaged route",
            position=Position(2, 2),
        )
    )
    state.add_mission(
        Mission(
            id="incident-1",
            incident_id="incident-1",
            incident_type=IncidentType.VIBRATION_ALERT,
            target_position=Position(2, 2),
            priority=1,
            area_type="LAND",
        )
    )
    state.assign_mission("incident-1", "rover-1")
    return state


def test_error_requeues_mission_until_vehicle_reports_idle():
    state = configured_state()

    state.update_vehicle_status("rover-1", "ERROR", 30, "Motor fault")

    mission = state.get_mission("incident-1")
    assert mission.status == "WAITING_FOR_VEHICLE"
    assert mission.assigned_vehicle_id is None
    assert state.idle_vehicles("rover") == []

    state.update_vehicle_status("rover-1", "IDLE", 0, "")

    assert [vehicle.id for vehicle in state.idle_vehicles("rover")] == ["rover-1"]


def test_completed_mission_resolves_incident_and_releases_vehicle_on_idle():
    state = configured_state()

    state.update_vehicle_status("rover-1", "COMPLETED", 100, "Done")

    assert state.get_mission("incident-1").status == "COMPLETED"
    assert state.get_incident("incident-1").status == "resolved"
    assert state.idle_vehicles("rover") == []

    state.update_vehicle_status("rover-1", "IDLE", 0, "")

    assert [vehicle.id for vehicle in state.idle_vehicles("rover")] == ["rover-1"]
    mission = state.get_mission("incident-1")
    assert mission.progress == 100
    assert mission.result_message == "Done"
