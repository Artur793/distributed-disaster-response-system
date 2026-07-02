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


def test_request_to_held_latency():

    durations = []

    for _ in range(ITERATIONS):

        charging = coordinator()

        start = time.perf_counter()

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

        durations.append(
            (time.perf_counter() - start) * 1000
        )

    average = statistics.mean(durations)
    minimum = min(durations)
    maximum = max(durations)

    print("\nRicart/Agrawala Latency")
    print(f"Iterations : {ITERATIONS}")
    print(f"Average    : {average:.4f} ms")
    print(f"Minimum    : {minimum:.4f} ms")
    print(f"Maximum    : {maximum:.4f} ms")

    assert average < 2.0


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