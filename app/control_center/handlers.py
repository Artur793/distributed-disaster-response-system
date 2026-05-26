import json

from app.common.models import (
    Incident,
    IncidentType,
    Mission,
    Position,
    Sensor,
    SensorType,
    Vehicle,
    VehicleType,
)
from app.common.maphtml import render_map_html
from app.common.statueshtml import render_status_html
from app.common.dashboardhtml import render_dashboard_html

def handle_get_status(state):
    return 200, {"Content-Type": "application/json"}, json.dumps(state.get_status())

    # it is already rendering on dashboard . we keep this json for the TEST
    #html = render_status_html(state.get_status())
    #return 200, {"Content-Type": "text/html"}, html


def handle_get_map(state):
    map_data = state.get_map_dict()
    if map_data is None:
        return 404, {"Content-Type": "text/plain"}, "Map not initialized"

    #return 200, {"Content-Type": "application/json"}, json.dumps(map_data)
    html = render_map_html(state.get_map())

    return 200, {"Content-Type": "text/html"}, html

def handle_get_dashboard(state):
    # currently only map
    map_data = state.get_map_dict()
    if map_data is None:
        return 404, {"Content-Type": "text/plain"}, "Dashboard not initialized"

    html = render_dashboard_html(state)

    return 200, {"Content-Type": "text/html"}, html


def handle_post_unit(body: str, state):
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return 400, {"Content-Type": "text/plain"}, "Invalid JSON"

    if "unit" not in data or "id" not in data:
        return 400, {"Content-Type": "text/plain"}, "Missing required fields: id, unit"

    position = None
    if "position" in data:
        pos = data["position"]

        if "x" not in pos or "y" not in pos:
            return 400, {"Content-Type": "text/plain"}, "Position must contain x and y"

        position = Position(x=pos["x"], y=pos["y"])

    if data["unit"] == "vehicle":
        if "vehicle_type" not in data:
            return 400, {"Content-Type": "text/plain"}, "Missing required field: vehicle_type"
        if "rpc_host" not in data or "rpc_port" not in data:
            return 400, {"Content-Type": "text/plain"}, "Missing required fields: rpc_host, rpc_port"
        if not isinstance(data["rpc_host"], str) or not data["rpc_host"]:
            return 400, {"Content-Type": "text/plain"}, "Invalid rpc_host"
        if not isinstance(data["rpc_port"], int) or not 1 <= data["rpc_port"] <= 65535:
            return 400, {"Content-Type": "text/plain"}, "Invalid rpc_port"

        try:
            vehicle = Vehicle(
                id=data["id"],
                vehicle_type=VehicleType(data["vehicle_type"]),
                rpc_host=data["rpc_host"],
                rpc_port=data["rpc_port"],
                position=position,
            )
        except ValueError:
            return 400, {"Content-Type": "text/plain"}, "Invalid vehicle_type"

        if not state.register_vehicle(vehicle):
            return 409, {"Content-Type": "text/plain"}, "Vehicle already exists"

        return 201, {"Content-Type": "application/json"}, json.dumps(vehicle.to_dict())

    if data["unit"] == "sensor":
        if "sensor_type" not in data:
            return 400, {"Content-Type": "text/plain"}, "Missing required field: sensor_type"

        try:
            sensor = Sensor(
                id=data["id"],
                sensor_type=SensorType(data["sensor_type"]),
                position=position,
            )
        except ValueError:
            return 400, {"Content-Type": "text/plain"}, "Invalid sensor_type"

        if not state.register_sensor(sensor):
            return 409, {"Content-Type": "text/plain"}, "Sensor already exists"

        return 201, {"Content-Type": "application/json"}, json.dumps(sensor.to_dict())

    return 400, {"Content-Type": "text/plain"}, "Invalid unit: must be 'vehicle' or 'sensor'"


def handle_post_incident(body: str, state):
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return 400, {"Content-Type": "text/plain"}, "Invalid JSON"

    required_fields = ["id", "incident_type", "source_id", "message", "position"]
    for field in required_fields:
        if field not in data:
            return 400, {"Content-Type": "text/plain"}, f"Missing field: {field}"

    if not state.source_exists(data["source_id"]):
        return 400, {"Content-Type": "text/plain"}, "Unknown source_id"

    pos = data["position"]
    if not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
        return 400, {"Content-Type": "text/plain"}, "Position must contain x and y"
    if not isinstance(pos["x"], int) or not isinstance(pos["y"], int):
        return 400, {"Content-Type": "text/plain"}, "Position coordinates must be integers"

    island_map = state.get_map()
    if island_map is None:
        return 400, {"Content-Type": "text/plain"}, "Map not initialized"
    if not 0 <= pos["x"] < island_map.width or not 0 <= pos["y"] < island_map.height:
        return 400, {"Content-Type": "text/plain"}, "Position outside map"

    position = Position(x=pos["x"], y=pos["y"])
    area_type = island_map.cells[position.y][position.x].tile_type.name

    try:
        incident = Incident(
            id=data["id"],
            incident_type=IncidentType(data["incident_type"]),
            source_id=data["source_id"],
            message=data["message"],
            position=position,
            priority=data.get("priority", 1),
            status=data.get("status", "open"),
        )
    except ValueError:
        return 400, {"Content-Type": "text/plain"}, "Invalid incident_type"

    if not state.add_incident(incident):
        return 409, {"Content-Type": "text/plain"}, "Incident already exists"

    state.add_mission(
        Mission(
            id=incident.id,
            incident_id=incident.id,
            incident_type=incident.incident_type,
            target_position=incident.position,
            priority=incident.priority,
            area_type=area_type,
        )
    )

    return 201, {"Content-Type": "application/json"}, json.dumps(incident.to_dict())
