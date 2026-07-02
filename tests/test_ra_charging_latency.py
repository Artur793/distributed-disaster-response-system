import statistics
import time

import pytest

from app.vehicles.charging_coordinator import (
    VehicleChargingConfig,
    VehicleChargingCoordinator,
)


pytestmark = pytest.mark.no_control_center


ITERATIONS = 500


def coordinator():

    return VehicleChargingCoordinator(

        VehicleChargingConfig(

            vehicle_id="drone-1",

            participants=[

                "drone-1",

                "rover-1",

                "rover-2",

            ],

            battery_initial_percent=15,

        )

    )


import statistics
import time
from unittest.mock import Mock

import pytest

from app.rpc.generated import mission_pb2
from app.vehicles.rpc_server import BaseVehicle
from app.vehicles.charging_coordinator import (
    VehicleChargingCoordinator,
    VehicleChargingConfig,
)


pytestmark = pytest.mark.no_control_center


class DummyVehicle(BaseVehicle):
    def execute_mission(self):
        pass


def create_vehicle():
    vehicle = DummyVehicle("rover-1", "rover")

    vehicle.charging_coordinator = VehicleChargingCoordinator(
        VehicleChargingConfig(
            vehicle_id="rover-1",
            participants=[
                "rover-1",
                "rover-2",
                "drone-1",
            ],
            battery_initial_percent=15,
        )
    )

    vehicle.state = mission_pb2.IDLE

    # Infrastructure required by request_charging_access()
    vehicle.mqtt_client = Mock()

    return vehicle


def test_vehicle_request_to_held_latency(monkeypatch):
    

    iterations = 500
    durations = []

    # Infrastructure only
    monkeypatch.setattr(
        "app.vehicles.rpc_server.publish_json",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        DummyVehicle,
        "publish_telemetry",
        lambda self: None,
    )

    monkeypatch.setattr(
        DummyVehicle,
        "publish_charging_status",
        lambda self: None,
    )

    monkeypatch.setattr(
        DummyVehicle,
        "start_charging_if_held",
        lambda self: None,
    )

    for _ in range(iterations):

        vehicle = create_vehicle()

        start = time.perf_counter()

        vehicle.request_charging_access()

        request_id = vehicle.charging_coordinator.own_request_id

        vehicle.handle_charging_reply(
            {
                "message_id": "reply-1",
                "resource_id": vehicle.charging_coordinator.config.resource_id,
                "sender_id": "rover-2",
                "target_vehicle_id": "rover-1",
                "lamport": 2,
                "request_id": request_id,
            }
        )

        vehicle.handle_charging_reply(
            {
                "message_id": "reply-2",
                "resource_id": vehicle.charging_coordinator.config.resource_id,
                "sender_id": "drone-1",
                "target_vehicle_id": "rover-1",
                "lamport": 3,
                "request_id": request_id,
            }
        )

        end = time.perf_counter()

        assert vehicle.charging_coordinator.is_held()

        durations.append((end - start) * 1000)

    print("\nVehicle Charging Workflow Latency")
    print(f"Iterations : {iterations}")
    print(f"Average    : {statistics.mean(durations):.4f} ms")
    print(f"Minimum    : {min(durations):.4f} ms")
    print(f"Maximum    : {max(durations):.4f} ms")


def test_finish_charging_latency():

    durations = []

    for _ in range(ITERATIONS):

        charging = coordinator()

        request = charging.start_request()

        charging.receive_reply(
            message_id="reply-1",
            request_id=request.request_id,
            sender_id="rover-1",
            target_vehicle_id="drone-1",
            lamport=2,
        )

        charging.receive_reply(
            message_id="reply-2",
            request_id=request.request_id,
            sender_id="rover-2",
            target_vehicle_id="drone-1",
            lamport=3,
        )

        start = time.perf_counter()

        charging.finish_charging()

        durations.append(
            (time.perf_counter() - start) * 1000
        )

    average = statistics.mean(durations)

    print("\nCharging Release Latency")
    print(f"Average : {average:.4f} ms")

    assert average < 1.0