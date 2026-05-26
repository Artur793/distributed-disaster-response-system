import threading

from app.common.models import IncidentType, Mission, Vehicle
from app.common.state import SystemState


def load_rpc_modules():
    import grpc

    from app.rpc.generated import mission_pb2, mission_pb2_grpc

    return grpc, mission_pb2, mission_pb2_grpc


class DispatchCoordinator:
    def __init__(self, state: SystemState, retry_seconds: float = 3.0):
        self.state = state
        self.retry_seconds = retry_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run,
            name="mission-dispatcher",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            # Refresh availability first, then try waiting work against the
            # latest vehicle states. Unassigned work is retried indefinitely.
            self.poll_vehicle_statuses()
            self.dispatch_waiting_missions()
            self._stop_event.wait(self.retry_seconds)

    def dispatch_waiting_missions(self) -> None:
        for mission in self.state.waiting_missions():
            vehicle_type = self._required_vehicle_type(mission)
            for vehicle in self.state.idle_vehicles(vehicle_type):
                if self._try_assign(mission, vehicle):
                    break

    def poll_vehicle_statuses(self) -> None:
        try:
            grpc, mission_pb2, mission_pb2_grpc = load_rpc_modules()
        except ImportError:
            return

        for vehicle in self.state.vehicles_for_status_poll():
            try:
                with grpc.insecure_channel(vehicle.rpc_address) as channel:
                    stub = mission_pb2_grpc.VehicleServiceStub(channel)
                    reply = stub.GetVehicleStatus(
                        mission_pb2.VehicleStatusRequest(vehicle_id=vehicle.id),
                        timeout=2.0,
                    )
            except grpc.RpcError:
                continue

            state_name = mission_pb2.VehicleState.Name(reply.state)
            if state_name == "VEHICLE_STATE_UNKNOWN":
                continue
            self.state.update_vehicle_status(
                vehicle.id,
                state_name,
                reply.progress_percent,
                reply.result,
            )

    @staticmethod
    def _required_vehicle_type(mission: Mission) -> str:
        # Current milestone maps incidents directly to existing vehicle types;
        # specialized sub-roles can be added after RPC integration is stable.
        if mission.incident_type == IncidentType.WATER_LEVEL_ALERT:
            return "drone"
        if mission.incident_type == IncidentType.VIBRATION_ALERT:
            return "rover"
        if mission.area_type == "WATER":
            return "boat"
        return "rover"

    def _try_assign(self, mission: Mission, vehicle: Vehicle) -> bool:
        try:
            grpc, mission_pb2, mission_pb2_grpc = load_rpc_modules()
        except ImportError:
            return False

        request = mission_pb2.Mission(
            mission_id=mission.id,
            incident_id=mission.incident_id,
            incident_type=mission.incident_type.value,
            target_position=mission_pb2.Position(
                x=mission.target_position.x,
                y=mission.target_position.y,
            ),
            priority=mission.priority,
            assigned_vehicle_id=vehicle.id,
            area_type=getattr(mission_pb2, mission.area_type),
        )

        try:
            with grpc.insecure_channel(vehicle.rpc_address) as channel:
                stub = mission_pb2_grpc.VehicleServiceStub(channel)
                acknowledgement = stub.AssignMission(request, timeout=2.0)
        except grpc.RpcError:
            return False

        if not acknowledgement.accepted:
            return False

        self.state.assign_mission(mission.id, vehicle.id)
        return True
