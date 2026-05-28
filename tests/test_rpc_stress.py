import threading
import time

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

    time.sleep(0.01)

    state.update_vehicle_status(
        vehicle_id,
        "COMPLETED",
        95,
        "mission completed",
    )


def worker(state, index):

    incident = Incident(
        id=f"incident-{index}",
        incident_type=IncidentType.PERSON_DETECTED,
        source_id=f"camera-{index}",
        message="Person detected",
        position=Position(index, index),
        priority=1,
    )

    state.add_incident(incident)

    mission = Mission(
        id=f"mission-{index}",
        incident_id=incident.id,
        incident_type=IncidentType.PERSON_DETECTED,
        target_position=Position(index, index),
        priority=1,
        area_type="LAND",
    )

    state.add_mission(mission)

    vehicle_id = f"drone-{index}"

    vehicle = Vehicle(
        id=vehicle_id,
        vehicle_type=VehicleType.DRONE,
        rpc_host="localhost",
        rpc_port=50051 + index,
    )

    state.register_vehicle(vehicle)

    state.assign_mission(
        mission.id,
        vehicle.id,
    )

    simulate_vehicle_execution(
        state,
        vehicle.id,
        mission.id,
    )


def test_rpc_mission_flow_stress():

    state = SystemState()

    threads = []

    start = time.perf_counter()

    for i in range(50):

        t = threading.Thread(
            target=worker,
            args=(state, i),
        )

        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    end = time.perf_counter()

    total_time_ms = (end - start) * 1000

    completed = 0

    for mission in state.missions.values():

        if mission.status == "COMPLETED":
            completed += 1

    print(f"RPC_STRESS_TOTAL_TIME: {total_time_ms:.2f} ms")
    print(f"COMPLETED_MISSIONS: {completed}")

    assert completed == 50

    assert total_time_ms < 5000