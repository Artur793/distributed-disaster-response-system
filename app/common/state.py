from threading import RLock

from app.common.models import Incident, Mission, Position, Sensor, Vehicle
from app.common.map import IslandMap
from app.common.charging_coordination import ChargingCoordinationState

class SystemState:
    def __init__(self):
        # REST requests and the RPC coordinator access this state concurrently.
        self._lock = RLock()
        self.vehicles: dict[str, Vehicle] = {}
        self.sensors: dict[str, Sensor] = {}
        self.incidents: dict[str, Incident] = {}
        self.missions: dict[str, Mission] = {}
        self.map: IslandMap | None = None
        # ============================================================
            # Aufgabe 4
            # Ricart / Agrawala charging coordination state
        # ============================================================

        self.charging_coordination = ChargingCoordinationState()

    def register_vehicle(self, vehicle: Vehicle) -> bool:
        with self._lock:
            if vehicle.id in self.vehicles:
                return False
            self.vehicles[vehicle.id] = vehicle
            return True

    def register_sensor(self, sensor: Sensor) -> bool:
        with self._lock:
            if sensor.id in self.sensors:
                return False
            self.sensors[sensor.id] = sensor
            return True

    def add_incident(self, incident: Incident) -> bool:
        with self._lock:
            if incident.id in self.incidents:
                return False
            self.incidents[incident.id] = incident
            return True

    def add_mission(self, mission: Mission) -> bool:
        with self._lock:
            if mission.id in self.missions:
                return False
            self.missions[mission.id] = mission
            return True

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        with self._lock:
            return self.vehicles.get(vehicle_id)

    def get_sensor(self, sensor_id: str) -> Sensor | None:
        with self._lock:
            return self.sensors.get(sensor_id)

    def get_incident(self, incident_id: str) -> Incident | None:
        with self._lock:
            return self.incidents.get(incident_id)

    def get_mission(self, mission_id: str) -> Mission | None:
        with self._lock:
            return self.missions.get(mission_id)

    def set_map(self, island_map: IslandMap) -> None:
        with self._lock:
            self.map = island_map

    def get_map(self) -> IslandMap | None:
        with self._lock:
            return self.map

    def get_map_dict(self) -> dict | None:  # Helper function for GET /map
        with self._lock:
            if self.map is None:
                return None
            return self.map.to_dict()

    def source_exists(self, source_id: str) -> bool:
        with self._lock:
            return source_id in self.vehicles or source_id in self.sensors

    def get_open_incidents(self) -> list[dict]:
        with self._lock:
            return [
                incident.to_dict()
                for incident in self.incidents.values()
                if incident.status == "open"
            ]

    def remove_incident(self, incident_id: str) -> bool:
        with self._lock:
            if incident_id not in self.incidents:
                return False
            del self.incidents[incident_id]
            return True

    def waiting_missions(self) -> list[Mission]:
        with self._lock:
            return [
                mission
                for mission in self.missions.values()
                if mission.status == "WAITING_FOR_VEHICLE"
            ]

    def vehicles_for_status_poll(self) -> list[Vehicle]:
        with self._lock:
            # Poll non-idle vehicles too: ERROR/COMPLETED vehicles may later
            # report IDLE and become eligible for a new assignment.
            return list(self.vehicles.values())

    def idle_vehicles(self, vehicle_type: str) -> list[Vehicle]:
        with self._lock:
            return [
                vehicle
                for vehicle in self.vehicles.values()
                if vehicle.vehicle_type.value == vehicle_type
                and vehicle.status == "IDLE"
            ]

    def assign_mission(self, mission_id: str, vehicle_id: str) -> None:
        with self._lock:
            mission = self.missions[mission_id]
            vehicle = self.vehicles[vehicle_id]
            mission.assigned_vehicle_id = vehicle_id
            mission.status = "ASSIGNED"
            mission.progress = 0
            mission.result_message = None
            vehicle.assigned_mission_id = mission_id
            vehicle.status = "ASSIGNED"
            vehicle.progress = 0
            vehicle.result_message = None

    def fail_mission(self, mission_id: str, result_message: str) -> None:
        with self._lock:
            mission = self.missions[mission_id]
            mission.status = "ERROR"
            mission.assigned_vehicle_id = None
            mission.progress = 0
            mission.result_message = result_message

    def update_vehicle_status(
        self,
        vehicle_id: str,
        vehicle_status: str,
        progress: int,
        result_message: str,
        position: Position | None = None,
    ) -> None:
        with self._lock:
            vehicle = self.vehicles[vehicle_id]
            vehicle.status = vehicle_status
            vehicle.progress = progress
            vehicle.result_message = result_message or None
            if position is not None:
                vehicle.position = position
            mission_id = vehicle.assigned_mission_id

            if mission_id is None:
                return

            mission = self.missions[mission_id]

            if vehicle_status == "COMPLETED":
                mission.status = "COMPLETED"
                mission.progress = progress
                mission.result_message = result_message or None
                self.incidents[mission.incident_id].status = "resolved"
            elif vehicle_status == "ERROR":
                # A vehicle error does not fail the incident permanently:
                # release the mission so another compatible vehicle can retry.
                mission.status = "WAITING_FOR_VEHICLE"
                mission.assigned_vehicle_id = None
                mission.progress = 0
                mission.result_message = result_message or None
                vehicle.assigned_mission_id = None
            elif vehicle_status in {"ASSIGNED", "BUSY"}:
                mission.status = vehicle_status
                mission.progress = progress
                mission.result_message = result_message or None
            elif vehicle_status == "IDLE":
                # IDLE is the only state that makes this vehicle selectable
                # again. Keep completed mission history while the vehicle
                # resets its own progress for future work.
                if mission.status != "COMPLETED":
                    mission.status = "WAITING_FOR_VEHICLE"
                    mission.assigned_vehicle_id = None
                    mission.progress = 0
                    mission.result_message = result_message or None
                vehicle.assigned_mission_id = None

    def get_status(self) -> dict:
        with self._lock:
            return {
                "map_loaded": self.map is not None,
                "vehicle_count": len(self.vehicles),
                "sensor_count": len(self.sensors),
                "incident_count": len(self.incidents),
                "mission_count": len(self.missions),
                "vehicles": [vehicle.to_dict() for vehicle in self.vehicles.values()],
                "sensors": [sensor.to_dict() for sensor in self.sensors.values()],
                "incidents": [incident.to_dict() for incident in self.incidents.values()],
                "missions": [mission.to_dict() for mission in self.missions.values()],
                "charging_coordination": self.get_charging_status(),
            }

    # ============================================================
    # Aufgabe 4
        # Charging Coordination
    # ============================================================

    def update_charging_status(

        self,

        payload: dict,

    ) -> None:

        self.charging_coordination.update_participant(

            vehicle_id=payload["vehicle_id"],

            vehicle_state=payload["vehicle_state"],

            ra_state=payload["ra_state"],

            lamport=payload["lamport"],

            battery_percent=payload["battery_percent"],

            waiting_for=payload.get("waiting_for", []),

            deferred_replies=payload.get(
                "deferred_replies",
                [],
            ),

            timestamp=payload.get(
                "sent_at",
                "",
            ),

        )


    def get_charging_status(self) -> dict:

        return self.charging_coordination.get_status()