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
    rpc_host: str       # Vehicles register their RPC endpoint so the control center does not
    rpc_port: int       # depend on fixed Docker service names or ports.
    position: Position | None = None
    status: str = "IDLE"
    assigned_mission_id: str | None = None
    progress: int = 0
    result_message: str | None = None

    @property
    def rpc_address(self) -> str:
        return f"{self.rpc_host}:{self.rpc_port}"

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
    position: Position
    priority: int = 1
    status: str = "open"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["incident_type"] = self.incident_type.value
        return data


@dataclass
class Mission:
    # Mission and Incident IDs are the same
    id: str
    incident_id: str
    incident_type: IncidentType
    target_position: Position
    priority: int
    area_type: str
    assigned_vehicle_id: str | None = None
    progress: int = 0
    status: str = "WAITING_FOR_VEHICLE"
    result_message: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["incident_type"] = self.incident_type.value
        return data
