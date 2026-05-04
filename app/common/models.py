from dataclasses import dataclass, asdict
from enum import Enum


class VehicleType(str, Enum):
    DRONE = "drone"
    ROVER = "rover"
    BOAT = "boat"


class SensorType(str, Enum):
    CAMERA = "camera"
    WATER = "water"
    VIBRATION = "vibration"


class IncidentType(str, Enum):
    WATER_LEVEL_ALERT = "water_level_alert"
    VIBRATION_ALERT = "vibration_alert"
    PERSON_DETECTED = "person_detected"


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Vehicle:
    id: str     # Better readability in the future (e.g. rover-1 rather than 173621)
    vehicle_type: VehicleType
    position: Position | None = None
    status: str = "registered"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["vehicle_type"] = self.vehicle_type.value
        return data


@dataclass
class Sensor:
    id: str
    sensor_type: SensorType
    position: Position | None = None
    status: str = "registered"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["sensor_type"] = self.sensor_type.value
        return data


@dataclass
class Incident:
    id: str
    incident_type: IncidentType
    source_id: str
    message: str
    position: Position | None = None
    priority: int = 1
    status: str = "open"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["incident_type"] = self.incident_type.value
        return data