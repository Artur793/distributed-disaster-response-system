import os
from dataclasses import dataclass, field
from threading import RLock


RESOURCE_ID = "charging-station-1-slot-1"


class ChargingRAState:
    RELEASED = "RELEASED"
    WANTED = "WANTED"
    HELD = "HELD"


@dataclass(frozen=True)
class VehicleChargingConfig:
    vehicle_id: str
    participants: list[str]
    resource_id: str = RESOURCE_ID
    battery_initial_percent: int = 100
    battery_low_threshold: int = 20
    battery_drain_percent_per_incident: int = 30
    charging_rate_percent_per_second: int = 10
    reply_timeout_seconds: int = 10
    charging_station_x: int = 9
    charging_station_y: int = 6

    @property
    def enabled(self) -> bool:
        return self.vehicle_id in self.participants

    @property
    def other_participants(self) -> list[str]:
        return [
            participant
            for participant in self.participants
            if participant != self.vehicle_id
        ]

    @property
    def charging_station_position(self) -> dict:
        return {
            "x": self.charging_station_x,
            "y": self.charging_station_y,
        }


@dataclass
class ChargingSnapshot:
    vehicle_id: str
    resource_id: str
    ra_state: str
    lamport: int
    battery_percent: int
    waiting_for: list[str] = field(default_factory=list)
    deferred_replies: list[str] = field(default_factory=list)
    own_request_id: str | None = None
    own_request_priority: tuple[int, str] | None = None

    @property
    def needs_periodic_status(self) -> bool:
        return self.ra_state in {
            ChargingRAState.WANTED,
            ChargingRAState.HELD,
        }


@dataclass(frozen=True)
class ChargingRequest:
    request_id: str
    lamport: int
    battery_percent: int


class RequestDecision:
    IGNORE = "IGNORE"
    REPLY = "REPLY"
    DEFER = "DEFER"


class VehicleChargingCoordinator:
    """Vehicle-local Ricart/Agrawala state for the charging slot."""

    def __init__(self, config: VehicleChargingConfig):
        self.config = config
        self._lock = RLock()

        self.ra_state = ChargingRAState.RELEASED
        self.lamport = 0
        self.battery_percent = config.battery_initial_percent

        self.own_request_id: str | None = None
        self.own_request_priority: tuple[int, str] | None = None
        self.waiting_for: set[str] = set()
        self.deferred_replies: dict[str, str] = {}
        self.seen_message_ids: set[str] = set()
        self.seen_request_ids: set[str] = set()
        self.last_timeout_warning_at = 0.0

    @classmethod
    def from_environment(cls, vehicle_id: str) -> "VehicleChargingCoordinator":
        participants = _parse_csv_env("RA_PARTICIPANTS")
        config = VehicleChargingConfig(
            vehicle_id=vehicle_id,
            participants=participants,
            battery_initial_percent=_int_env(
                "BATTERY_INITIAL_PERCENT",
                100,
            ),
            battery_low_threshold=_int_env("BATTERY_LOW_THRESHOLD", 20),
            battery_drain_percent_per_incident=_int_env(
                "BATTERY_DRAIN_PERCENT_PER_INCIDENT",
                30,
            ),
            charging_rate_percent_per_second=_int_env(
                "CHARGING_RATE_PERCENT_PER_SECOND",
                10,
            ),
            reply_timeout_seconds=_int_env(
                "RA_REPLY_TIMEOUT_SECONDS",
                10,
            ),
            charging_station_x=_int_env("CHARGING_STATION_X", 9),
            charging_station_y=_int_env("CHARGING_STATION_Y", 6),
        )
        return cls(config)

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def needs_charging(self) -> bool:
        with self._lock:
            return (
                self.enabled
                and self.ra_state == ChargingRAState.RELEASED
                and self.battery_percent < self.config.battery_low_threshold
            )

    def start_request(self) -> ChargingRequest | None:
        with self._lock:
            if (
                not self.enabled
                or self.ra_state != ChargingRAState.RELEASED
            ):
                return None

            self.lamport += 1
            self.ra_state = ChargingRAState.WANTED
            self.own_request_id = (
                f"{self.config.vehicle_id}-{self.lamport}"
            )
            self.own_request_priority = (
                self.lamport,
                self.config.vehicle_id,
            )
            self.waiting_for = set(self.config.other_participants)
            self.deferred_replies.clear()
            self.seen_request_ids.add(self.own_request_id)

            if not self.waiting_for:
                self.ra_state = ChargingRAState.HELD

            return ChargingRequest(
                request_id=self.own_request_id,
                lamport=self.lamport,
                battery_percent=self.battery_percent,
            )

    def current_request(self) -> ChargingRequest | None:
        with self._lock:
            if (
                self.ra_state != ChargingRAState.WANTED
                or self.own_request_id is None
                or self.own_request_priority is None
            ):
                return None

            return ChargingRequest(
                request_id=self.own_request_id,
                lamport=self.own_request_priority[0],
                battery_percent=self.battery_percent,
            )

    def receive_request(
        self,
        *,
        message_id: str,
        request_id: str,
        sender_id: str,
        lamport: int,
    ) -> str:
        with self._lock:
            if (
                not self.enabled
                or sender_id == self.config.vehicle_id
                or message_id in self.seen_message_ids
                or request_id in self.seen_request_ids
            ):
                return RequestDecision.IGNORE

            self.seen_message_ids.add(message_id)
            self.seen_request_ids.add(request_id)
            self.lamport = max(self.lamport, lamport) + 1

            incoming_priority = (lamport, sender_id)
            own_has_priority = (
                self.own_request_priority is not None
                and self.own_request_priority < incoming_priority
            )

            if (
                self.ra_state == ChargingRAState.HELD
                or (
                    self.ra_state == ChargingRAState.WANTED
                    and own_has_priority
                )
            ):
                self.deferred_replies[sender_id] = request_id
                return RequestDecision.DEFER

            return RequestDecision.REPLY

    def receive_reply(
        self,
        *,
        message_id: str,
        request_id: str,
        sender_id: str,
        target_vehicle_id: str,
        lamport: int,
    ) -> bool:
        with self._lock:
            if (
                not self.enabled
                or target_vehicle_id != self.config.vehicle_id
                or message_id in self.seen_message_ids
            ):
                return False

            self.seen_message_ids.add(message_id)
            self.lamport = max(self.lamport, lamport) + 1

            if (
                self.ra_state != ChargingRAState.WANTED
                or request_id != self.own_request_id
            ):
                return False

            self.waiting_for.discard(sender_id)

            if not self.waiting_for:
                self.ra_state = ChargingRAState.HELD
                return True

            return False

    def is_held(self) -> bool:
        with self._lock:
            return self.ra_state == ChargingRAState.HELD

    def charge_one_tick(self) -> int:
        with self._lock:
            self.battery_percent = min(
                100,
                (
                    self.battery_percent
                    + self.config.charging_rate_percent_per_second
                ),
            )
            return self.battery_percent

    def drain_battery_for_incident(self) -> int:
        with self._lock:
            if not self.enabled:
                return self.battery_percent

            self.battery_percent = max(
                0,
                (
                    self.battery_percent
                    - self.config.battery_drain_percent_per_incident
                ),
            )
            return self.battery_percent

    def is_fully_charged(self) -> bool:
        with self._lock:
            return self.battery_percent >= 100

    def finish_charging(self) -> list[tuple[str, str]]:
        with self._lock:
            deferred = sorted(self.deferred_replies.items())
            self.ra_state = ChargingRAState.RELEASED
            self.own_request_id = None
            self.own_request_priority = None
            self.waiting_for.clear()
            self.deferred_replies.clear()
            self.last_timeout_warning_at = 0.0
            return deferred

    def should_log_timeout_warning(self, now: float) -> bool:
        with self._lock:
            if (
                self.ra_state != ChargingRAState.WANTED
                or not self.waiting_for
            ):
                return False

            if (
                now - self.last_timeout_warning_at
                < self.config.reply_timeout_seconds
            ):
                return False

            self.last_timeout_warning_at = now
            return True

    def next_lamport(self) -> int:
        with self._lock:
            self.lamport += 1
            return self.lamport

    def observe_lamport(self, received_lamport: int) -> int:
        with self._lock:
            self.lamport = max(self.lamport, received_lamport) + 1
            return self.lamport

    def own_request_has_priority(
        self,
        incoming_lamport: int,
        incoming_vehicle_id: str,
    ) -> bool:
        with self._lock:
            if self.own_request_priority is None:
                return False
            incoming_priority = (incoming_lamport, incoming_vehicle_id)
            return self.own_request_priority < incoming_priority

    def snapshot(self) -> ChargingSnapshot:
        with self._lock:
            return ChargingSnapshot(
                vehicle_id=self.config.vehicle_id,
                resource_id=self.config.resource_id,
                ra_state=self.ra_state,
                lamport=self.lamport,
                battery_percent=self.battery_percent,
                waiting_for=sorted(self.waiting_for),
                deferred_replies=sorted(self.deferred_replies),
                own_request_id=self.own_request_id,
                own_request_priority=self.own_request_priority,
            )


def _parse_csv_env(name: str) -> list[str]:
    raw_value = os.getenv(name, "")
    return [
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    ]


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)
