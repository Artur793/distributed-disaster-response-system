from app.control_center.tcpserversocket import startsocket
from app.control_center.dispatcher import DispatchCoordinator
from app.common.state import SystemState
from app.common.mapgenerator import generate_default_map

state = SystemState()
print("server is starting ... ")

default_map = generate_default_map()

state.set_map(default_map)

# Assignment and status refresh are asynchronous so POST /incident only
# records work and does not block while waiting for a reachable idle vehicle.
coordinator = DispatchCoordinator(state)
coordinator.start()

startsocket(state)
