
import time
import threading

from app.common.models import (
    Incident,
    IncidentType,
    Mission,
    Position,
    Vehicle,
    VehicleType,
)

from app.common.state import SystemState


def simulate_vehicle_execution(state, vehicle_id, mission_id):

    time.sleep(0.05)

    state.update_vehicle_status(
        vehicle_id,
        "COMPLETED",
        90,
        "mission completed",
    )


def test_end_to_end_mission_flow_latency():

    state = SystemState()

    vehicle = Vehicle(
        id="drone-1",
        vehicle_type=VehicleType.DRONE,
        rpc_host="localhost",
        rpc_port=50051,
    )

    state.register_vehicle(vehicle)

    incident = Incident(
        id="incident-1",
        incident_type=IncidentType.PERSON_DETECTED,
        source_id="camera-1",
        message="Person detected",
        position=Position(10, 12),
        priority=1,
    )

    state.add_incident(incident)

    mission = Mission(
        id="mission-1",
        incident_id=incident.id,
        incident_type=IncidentType.PERSON_DETECTED,
        target_position=Position(10, 12),
        priority=1,
        area_type="LAND",
    )

    state.add_mission(mission)

    start = time.perf_counter()

    state.assign_mission(
        mission.id,
        vehicle.id,
    )

    worker = threading.Thread(
        target=simulate_vehicle_execution,
        args=(state, vehicle.id, mission.id),
    )

    worker.start()
    worker.join()

    end = time.perf_counter()

    latency_ms = (end - start) * 1000

    updated_mission = state.get_mission(mission.id)
    updated_incident = state.get_incident(incident.id)

    print(f"END_TO_END_MISSION_FLOW_LATENCY: {latency_ms:.2f} ms")

    assert updated_mission.status == "COMPLETED"

    assert updated_incident.status == "resolved"

    assert latency_ms < 500