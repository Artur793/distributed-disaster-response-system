from app.common.models import Vehicle, Sensor, Incident


class SystemState:
    def __init__(self):
        self.vehicles: dict[str, Vehicle] = {}
        self.sensors: dict[str, Sensor] = {}
        self.incidents: dict[str, Incident] = {}

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

    def get_status(self) -> dict:
        return {
            "vehicle_count": len(self.vehicles),
            "sensor_count": len(self.sensors),
            "incident_count": len(self.incidents),
            "vehicles": [vehicle.to_dict() for vehicle in self.vehicles.values()],
            "sensors": [sensor.to_dict() for sensor in self.sensors.values()],
            "incidents": [incident.to_dict() for incident in self.incidents.values()],
        }