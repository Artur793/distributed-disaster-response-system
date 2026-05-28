import threading
import time

import grpc

from app.rpc.generated import mission_pb2
from app.rpc.generated import mission_pb2_grpc

from app.vehicles.rpc_server import (
    BaseVehicle,
    run_rpc_server,
)


class StressDrone(BaseVehicle):

    def __init__(self):

        super().__init__(
            vehicle_id="stress-drone",
            vehicle_type="drone",
        )

        self.position = {
            "x": 0,
            "y": 0,
        }

    def execute_mission(self):

        self.state = mission_pb2.BUSY

        time.sleep(0.05)

        self.progress = 100

        self.state = mission_pb2.COMPLETED

        self.result_message = "Mission completed"

    def is_compatible(self, request):

        return True


def start_rpc_server():

    vehicle = StressDrone()

    thread = threading.Thread(
        target=run_rpc_server,
        args=(vehicle, 50052),
        daemon=True,
    )

    thread.start()

    time.sleep(1)


def worker(index, results):

    mission = mission_pb2.Mission(
        mission_id=f"mission-{index}",
        incident_id=f"incident-{index}",
        incident_type="PERSON_DETECTED",
        target_position=mission_pb2.Position(
            x=index,
            y=index,
        ),
        priority=1,
        assigned_vehicle_id="stress-drone",
        area_type=mission_pb2.LAND,
    )

    try:

        with grpc.insecure_channel("localhost:50052") as channel:

            stub = mission_pb2_grpc.VehicleServiceStub(channel)

            acknowledgement = stub.AssignMission(
                mission,
                timeout=2.0,
            )

            results.append(acknowledgement.accepted)

    except grpc.RpcError:

        results.append(False)


def test_rpc_mission_flow_stress():

    start_rpc_server()

    results = []

    threads = []

    start = time.perf_counter()

    for i in range(50):

        thread = threading.Thread(
            target=worker,
            args=(i, results),
        )

        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    end = time.perf_counter()

    total_time_ms = (end - start) * 1000

    accepted = results.count(True)

    print(f"REAL_RPC_STRESS_TOTAL_TIME: {total_time_ms:.2f} ms")

    print(f"ACCEPTED_MISSIONS: {accepted}")

    assert accepted >= 1

    assert total_time_ms < 5000