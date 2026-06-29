import pytest

from app.common.map import InfrastructureType, TileType
from app.common.mapgenerator import generate_default_map
from app.vehicles.rpc_server import BaseVehicle
from app.vehicles.charging_coordinator import (
    VehicleChargingConfig,
    VehicleChargingCoordinator,
)
from app.rpc.generated import mission_pb2


pytestmark = pytest.mark.no_control_center


class DummyVehicle(BaseVehicle):
    def execute_mission(self):
        pass

class WaterOnlyVehicle(BaseVehicle):

    def execute_mission(self):
        pass

    def is_compatible(self, request):
        return request.area_type == mission_pb2.WATER

def create_request():
    return mission_pb2.Mission(
        mission_id="mission-1",
        incident_id="incident-1",
        incident_type="person_detected",
        priority=1,
    )


def test_vehicle_accepts_mission_when_idle():
    vehicle = DummyVehicle("rover-1", "rover")

    response = vehicle.AssignMission(
        create_request(),
        None,
    )

    assert response.accepted is True
    assert vehicle.state == mission_pb2.ASSIGNED


def test_vehicle_rejects_second_mission_when_busy():
    vehicle = DummyVehicle("rover-1", "rover")

    request = create_request()

    first = vehicle.AssignMission(request, None)
    second = vehicle.AssignMission(request, None)

    assert first.accepted is True
    assert second.accepted is False


def test_vehicle_rejects_mission_while_waiting_for_charging():
    vehicle = DummyVehicle("rover-1", "rover")
    vehicle.charging_coordinator = VehicleChargingCoordinator(
        VehicleChargingConfig(
            vehicle_id="rover-1",
            participants=["rover-1", "rover-2"],
            battery_initial_percent=15,
        )
    )
    vehicle.charging_coordinator.start_request()

    response = vehicle.AssignMission(
        create_request(),
        None,
    )

    assert response.accepted is False
    assert response.message == "Vehicle is coordinating charging"


def test_rover_charging_route_uses_only_allowed_tiles():
    vehicle = DummyVehicle("rover-1", "rover")
    vehicle.position = {"x": 10, "y": 10}
    target = {"x": 9, "y": 6}
    island_map = generate_default_map()

    route = vehicle.calculate_route_to_position(target)

    assert route is not None
    assert route[-1].x == target["x"]
    assert route[-1].y == target["y"]
    for position in route:
        cell = island_map.cells[position.y][position.x]
        assert (
            cell.tile_type == TileType.LAND
            or cell.infrastructure == InfrastructureType.BRIDGE
        )


def test_vehicle_rejects_incompatible_mission():

    vehicle = WaterOnlyVehicle(
        "boat-1",
        "boat",
    )

    request = mission_pb2.Mission(
        mission_id="mission-1",
        incident_id="incident-1",
        incident_type="person_detected",
        priority=1,
        area_type=mission_pb2.LAND,
    )

    response = vehicle.AssignMission(
        request,
        None,
    )

    assert response.accepted is False
