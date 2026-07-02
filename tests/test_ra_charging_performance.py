import statistics
import time

import pytest

from app.common.charging_coordination import ChargingCoordinationState


pytestmark = pytest.mark.no_control_center


ITERATIONS = 10000


def test_update_participant_performance():

    state = ChargingCoordinationState()

    durations = []

    for i in range(ITERATIONS):

        start = time.perf_counter()

        state.update_participant(
            vehicle_id=f"drone-{i % 3}",
            vehicle_state="BUSY",
            ra_state="WANTED",
            lamport=i,
            battery_percent=15,
            waiting_for=["rover-1"],
            deferred_replies=[],
            timestamp="2026-06-30T12:00:00Z",
        )

        durations.append(
            (time.perf_counter() - start) * 1000
        )

    average = statistics.mean(durations)
    minimum = min(durations)
    maximum = max(durations)

    print("\nCharging State Update Performance")
    print(f"Iterations : {ITERATIONS}")
    print(f"Average    : {average:.4f} ms")
    print(f"Minimum    : {minimum:.4f} ms")
    print(f"Maximum    : {maximum:.4f} ms")

    assert average < 1.0


def test_get_status_performance():

    state = ChargingCoordinationState()

    for i in range(3):

        state.update_participant(
            vehicle_id=f"vehicle-{i}",
            vehicle_state="BUSY",
            ra_state="WANTED",
            lamport=i,
            battery_percent=18,
            waiting_for=[],
            deferred_replies=[],
            timestamp="2026-06-30T12:00:00Z",
        )

    durations = []

    for _ in range(ITERATIONS):

        start = time.perf_counter()

        state.get_status()

        durations.append(
            (time.perf_counter() - start) * 1000
        )

    average = statistics.mean(durations)

    print("\nCharging Status Retrieval Performance")
    print(f"Average : {average:.4f} ms")

    assert average < 1.0