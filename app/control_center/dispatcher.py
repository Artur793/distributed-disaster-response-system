import threading
from collections import deque

from app.common.map import InfrastructureType, IslandMap, MapCell, TileType
from app.common.models import IncidentType, Mission, Position, Vehicle
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
            candidates = self.state.idle_vehicles(vehicle_type)
            if not candidates:
                continue

            route_found = False
            for vehicle in candidates:
                route = self._calculate_route(vehicle, mission)
                if route is None:
                    continue

                route_found = True
                if self._try_assign(mission, vehicle, route):
                    break
            else:
                # An RPC failure for a reachable vehicle is retried later.
                # ERROR is reserved for work no currently idle candidate can reach.
                if not route_found:
                    self.state.fail_mission(
                        mission.id,
                        "No valid route to incident",
                    )

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

    def _calculate_route(
        self,
        vehicle: Vehicle,
        mission: Mission,
    ) -> list[Position] | None:
        island_map = self.state.get_map()
        if island_map is None or vehicle.position is None:
            return None

        return self._shortest_route(
            island_map,
            vehicle.vehicle_type.value,
            vehicle.position,
            mission.target_position,
        )

    @staticmethod
    def _shortest_route(
        island_map: IslandMap,
        vehicle_type: str,
        start: Position,
        target: Position,
    ) -> list[Position] | None:
        start_coordinates = (start.x, start.y)
        target_coordinates = (target.x, target.y)
        if not DispatchCoordinator._inside_map(island_map, start_coordinates):
            return None
        if not DispatchCoordinator._inside_map(island_map, target_coordinates):
            return None

        start_cell = island_map.cells[start.y][start.x]
        target_cell = island_map.cells[target.y][target.x]
        if not DispatchCoordinator._can_traverse(vehicle_type, start_cell):
            return None
        if not DispatchCoordinator._can_traverse(vehicle_type, target_cell):
            return None

        # Records the previous tile for every visited tile, allowing the
        # shortest route to be reconstructed backwards once target is found.
        parents: dict[tuple[int, int], tuple[int, int] | None] = {
            start_coordinates: None,
        }
        # BFS checks tiles in arrival order
        queue = deque([start_coordinates])
        directions = ((0, -1), (0, 1), (1, 0), (-1, 0))

        while queue:
            current = queue.popleft()
            if current == target_coordinates:
                break

            # Only orthogonal neighbors are considered: no diagonal travel.
            for x_offset, y_offset in directions:
                next_coordinates = (
                    current[0] + x_offset,
                    current[1] + y_offset,
                )
                # Ignore tiles that were already visited to avoid other equal or longer paths
                if next_coordinates in parents:
                    continue
                if not DispatchCoordinator._inside_map(island_map, next_coordinates):
                    continue

                next_cell = island_map.cells[next_coordinates[1]][next_coordinates[0]]
                if not DispatchCoordinator._can_traverse(vehicle_type, next_cell):
                    continue

                parents[next_coordinates] = current
                queue.append(next_coordinates)

        # In case the target couldn't be found:
        if target_coordinates not in parents:
            return None

        # The vehicle already occupies its starting tile, so only subsequent
        # tiles are transmitted for visible movement.
        route = []
        cursor = target_coordinates
        while cursor != start_coordinates:
            route.append(Position(x=cursor[0], y=cursor[1]))
            cursor = parents[cursor]
        route.reverse()
        return route

    @staticmethod
    def _inside_map(
        island_map: IslandMap,
        coordinates: tuple[int, int],
    ) -> bool:
        x, y = coordinates
        return 0 <= x < island_map.width and 0 <= y < island_map.height

    @staticmethod
    def _can_traverse(vehicle_type: str, cell: MapCell) -> bool:
        if vehicle_type == "drone":
            return True
        if vehicle_type == "boat":
            return cell.tile_type == TileType.WATER
        if vehicle_type == "rover":
            return (
                cell.tile_type == TileType.LAND
                or cell.infrastructure == InfrastructureType.BRIDGE
            )
        return False

    def _try_assign(
        self,
        mission: Mission,
        vehicle: Vehicle,
        route: list[Position],
    ) -> bool:
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
            route=[
                mission_pb2.Position(x=position.x, y=position.y)
                for position in route
            ],
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
