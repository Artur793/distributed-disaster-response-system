import pytest

from app.vehicles.charging_coordinator import (
    ChargingRAState,
    RequestDecision,
    VehicleChargingConfig,
    VehicleChargingCoordinator,
)


pytestmark = pytest.mark.no_control_center


def coordinator(vehicle_id: str) -> VehicleChargingCoordinator:
    return VehicleChargingCoordinator(
        VehicleChargingConfig(
            vehicle_id=vehicle_id,
            participants=["drone-1", "rover-1", "rover-2"],
            battery_initial_percent=15,
        )
    )


def test_start_request_sets_wanted_and_waiting_for_other_participants():
    charging = coordinator("drone-1")

    request = charging.start_request()
    snapshot = charging.snapshot()

    assert request is not None
    assert request.request_id == "drone-1-1"
    assert request.lamport == 1
    assert snapshot.ra_state == ChargingRAState.WANTED
    assert snapshot.waiting_for == ["rover-1", "rover-2"]
    assert snapshot.battery_percent == 15


def test_receive_request_replies_when_released_and_ignores_duplicate():
    charging = coordinator("drone-1")

    first_decision = charging.receive_request(
        message_id="rover-1-msg-1",
        request_id="rover-1-1",
        sender_id="rover-1",
        lamport=1,
    )
    duplicate_decision = charging.receive_request(
        message_id="rover-1-msg-1",
        request_id="rover-1-1",
        sender_id="rover-1",
        lamport=1,
    )

    assert first_decision == RequestDecision.REPLY
    assert duplicate_decision == RequestDecision.IGNORE


def test_current_request_keeps_original_lamport_while_wanted():
    charging = coordinator("drone-1")
    original = charging.start_request()
    charging.receive_request(
        message_id="rover-1-msg-1",
        request_id="rover-1-2",
        sender_id="rover-1",
        lamport=2,
    )

    retry = charging.current_request()

    assert retry is not None
    assert retry.request_id == original.request_id
    assert retry.lamport == original.lamport


def test_receive_request_defers_when_own_request_has_priority():
    charging = coordinator("drone-1")
    charging.start_request()

    decision = charging.receive_request(
        message_id="rover-1-msg-1",
        request_id="rover-1-2",
        sender_id="rover-1",
        lamport=2,
    )
    snapshot = charging.snapshot()

    assert decision == RequestDecision.DEFER
    assert snapshot.deferred_replies == ["rover-1"]


def test_receive_reply_enters_held_after_all_replies_arrive():
    charging = coordinator("drone-1")
    request = charging.start_request()

    first_entered = charging.receive_reply(
        message_id="rover-1-reply-1",
        request_id=request.request_id,
        sender_id="rover-1",
        target_vehicle_id="drone-1",
        lamport=3,
    )
    second_entered = charging.receive_reply(
        message_id="rover-2-reply-1",
        request_id=request.request_id,
        sender_id="rover-2",
        target_vehicle_id="drone-1",
        lamport=4,
    )
    snapshot = charging.snapshot()

    assert first_entered is False
    assert second_entered is True
    assert snapshot.ra_state == ChargingRAState.HELD
    assert snapshot.waiting_for == []


def test_finish_charging_releases_and_returns_deferred_replies():
    charging = coordinator("drone-1")
    request = charging.start_request()
    charging.receive_reply(
        message_id="rover-1-reply-1",
        request_id=request.request_id,
        sender_id="rover-1",
        target_vehicle_id="drone-1",
        lamport=3,
    )
    charging.receive_reply(
        message_id="rover-2-reply-1",
        request_id=request.request_id,
        sender_id="rover-2",
        target_vehicle_id="drone-1",
        lamport=4,
    )
    charging.receive_request(
        message_id="rover-1-msg-1",
        request_id="rover-1-5",
        sender_id="rover-1",
        lamport=5,
    )

    deferred = charging.finish_charging()
    snapshot = charging.snapshot()

    assert deferred == [("rover-1", "rover-1-5")]
    assert snapshot.ra_state == ChargingRAState.RELEASED
    assert snapshot.waiting_for == []
    assert snapshot.deferred_replies == []


def test_drain_battery_for_incident_uses_configured_amount_and_clamps():
    charging = VehicleChargingCoordinator(
        VehicleChargingConfig(
            vehicle_id="drone-1",
            participants=["drone-1"],
            battery_initial_percent=50,
            battery_drain_percent_per_incident=30,
        )
    )

    first_percent = charging.drain_battery_for_incident()
    second_percent = charging.drain_battery_for_incident()

    assert first_percent == 20
    assert second_percent == 0
