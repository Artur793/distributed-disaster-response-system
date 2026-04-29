from app.common.models import Vehicle, Sensor, Incident
from app.common.map import IslandMap


class SystemState:
    def __init__(self):
        self.vehicles: dict[str, Vehicle] = {}
        self.sensors: dict[str, Sensor] = {}
        self.incidents: dict[str, Incident] = {}
        self.map: IslandMap | None = None

    def register_vehicle(self, vehicle: Vehicle) -> bool:
        if vehicle.id in self.vehicles:
            return False
        self.vehicles[vehicle.id] = vehicle
        return True

    def register_sensor(self, sensor: Sensor) -> bool:
        if sensor.id in self.sensors:
            return False
        self.sensors[sensor.id] = sensor
        return True

    def add_incident(self, incident: Incident) -> bool:
        if incident.id in self.incidents:
            return False
        self.incidents[incident.id] = incident
        return True

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        return self.vehicles.get(vehicle_id)

    def get_sensor(self, sensor_id: str) -> Sensor | None:
        return self.sensors.get(sensor_id)

    def get_incident(self, incident_id: str) -> Incident | None:
        return self.incidents.get(incident_id)

    def set_map(self, island_map: IslandMap) -> None:
        self.map = island_map

    def get_map(self) -> IslandMap | None:
        return self.map

    def get_map_dict(self) -> dict | None:  # Helper function for GET /map
        if self.map is None:
            return None
        return self.map.to_dict()

    def source_exists(self, source_id: str) -> bool:
        return source_id in self.vehicles or source_id in self.sensors

    def get_open_incidents(self) -> list[dict]:
        return [
            incident.to_dict()
            for incident in self.incidents.values()
            if incident.status == "open"
        ]

    def remove_incident(self, incident_id: str) -> bool:
        if incident_id not in self.incidents:
            return False
        del self.incidents[incident_id]
        return True

    def get_status(self) -> dict:
        return {
            "map_loaded": self.map is not None,
            "vehicle_count": len(self.vehicles),
            "sensor_count": len(self.sensors),
            "incident_count": len(self.incidents),
            "vehicles": [vehicle.to_dict() for vehicle in self.vehicles.values()],
            "sensors": [sensor.to_dict() for sensor in self.sensors.values()],
            "incidents": [incident.to_dict() for incident in self.incidents.values()],
        }