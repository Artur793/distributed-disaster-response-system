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
    charging_rate_percent_per_second: int = 10
    reply_timeout_seconds: int = 10

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
        self.deferred_replies: set[str] = set()
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
            charging_rate_percent_per_second=_int_env(
                "CHARGING_RATE_PERCENT_PER_SECOND",
                10,
            ),
            reply_timeout_seconds=_int_env(
                "RA_REPLY_TIMEOUT_SECONDS",
                10,
            ),
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
