import threading
import time

import grpc

from app.rpc.generated import mission_pb2
from app.rpc.generated import mission_pb2_grpc

from app.vehicles.rpc_server import (
    BaseVehicle,
    run_rpc_server,
)


class TDrone(BaseVehicle):

    def __init__(self):

        super().__init__(
            vehicle_id="drone-1",
            vehicle_type="drone",
        )

        self.position = {
            "x": 0,
            "y": 0,
        }

    def execute_mission(self):

        self.state = mission_pb2.BUSY

        for i in range(0, 101, 20):

            self.progress = i

            time.sleep(0.05)

        self.state = mission_pb2.COMPLETED

        self.result_message = "Mission completed"

    def is_compatible(self, request):

        return True


def start_rpc_server():

    vehicle = TDrone()

    thread = threading.Thread(
        target=run_rpc_server,
        args=(vehicle, 50051),
        daemon=True,
    )

    thread.start()

    time.sleep(1)

    return vehicle


def test_end_to_end_mission_flow_latency():

    start_rpc_server()

    mission = mission_pb2.Mission(
        mission_id="mission-1",
        incident_id="incident-1",
        incident_type="PERSON_DETECTED",
        target_position=mission_pb2.Position(
            x=10,
            y=12,
        ),
        priority=1,
        assigned_vehicle_id="drone-1",
        area_type=mission_pb2.LAND,
    )

    start = time.perf_counter()

    with grpc.insecure_channel("localhost:50051") as channel:

        stub = mission_pb2_grpc.VehicleServiceStub(channel)

        acknowledgement = stub.AssignMission(
            mission,
            timeout=2.0,
        )

    end = time.perf_counter()

    latency_ms = (end - start) * 1000

    print(f"REAL_RPC_ASSIGNMENT_LATENCY: {latency_ms:.2f} ms")

    assert acknowledgement.accepted is True

    assert latency_ms < 500