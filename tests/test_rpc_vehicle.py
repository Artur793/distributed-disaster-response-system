from app.vehicles.rpc_server import BaseVehicle
from app.rpc.generated import mission_pb2

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