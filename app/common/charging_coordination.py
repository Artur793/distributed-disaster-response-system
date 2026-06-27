from dataclasses import dataclass, field, asdict
from threading import RLock


@dataclass
class ChargingParticipant:

    vehicle_id: str

    vehicle_state: str = "IDLE"

    ra_state: str = "RELEASED"

    lamport: int = 0

    battery_percent: int = 100

    waiting_for: list[str] = field(default_factory=list)

    deferred_replies: list[str] = field(default_factory=list)

    last_update: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ChargingCoordinationState:

    def __init__(self):

        self._lock = RLock()

        self.resource_id = "charging-station-1-slot-1"

        self.current_holder: str | None = None

        self.waiting_vehicles: list[str] = []

        self.participants: dict[str, ChargingParticipant] = {}

        self.safety_violation = False

        self.last_update = ""

    def update_participant(
        self,
        *,
        vehicle_id: str,
        vehicle_state: str,
        ra_state: str,
        lamport: int,
        battery_percent: int,
        waiting_for: list[str],
        deferred_replies: list[str],
        timestamp: str,
    ):

        with self._lock:

            participant = ChargingParticipant(

                vehicle_id=vehicle_id,

                vehicle_state=vehicle_state,

                ra_state=ra_state,

                lamport=lamport,

                battery_percent=battery_percent,

                waiting_for=list(waiting_for),

                deferred_replies=list(deferred_replies),

                last_update=timestamp,
            )

            self.participants[vehicle_id] = participant

            self.last_update = timestamp

            self._recalculate()

    def _recalculate(self):

        holders = []

        waiting = []

        for participant in self.participants.values():

            if participant.ra_state == "HELD":
                holders.append(participant.vehicle_id)

            elif participant.ra_state == "WANTED":
                waiting.append(
                    (
                        participant.lamport,
                        participant.vehicle_id,
                    )
                )

        waiting.sort()

        self.waiting_vehicles = [
            vehicle_id
            for _, vehicle_id in waiting
        ]

        if len(holders) == 1:

            self.current_holder = holders[0]

            self.safety_violation = False

        elif len(holders) == 0:

            self.current_holder = None

            self.safety_violation = False

        else:

            self.current_holder = ",".join(holders)

            self.safety_violation = True

            print(
                "\n====================================="
            )
            print("SAFETY VIOLATION DETECTED")
            print(
                "Multiple vehicles are in HELD state."
            )
            print(
                f"Holders: {holders}"
            )
            print(
                "=====================================\n"
            )

    def get_status(self) -> dict:

        with self._lock:

            return {

                "resource_id": self.resource_id,

                "current_holder": self.current_holder,

                "waiting_vehicles": list(
                    self.waiting_vehicles
                ),

                "participants": [

                    participant.to_dict()

                    for participant

                    in sorted(

                        self.participants.values(),

                        key=lambda p: p.vehicle_id,

                    )

                ],

                "safety_violation": self.safety_violation,

                "last_update": self.last_update,

            }