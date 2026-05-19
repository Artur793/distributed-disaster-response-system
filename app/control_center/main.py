from app.control_center.tcpserversocket import startsocket
from app.common.state import SystemState
from app.common.mapgenerator import generate_default_map

state = SystemState()
print("server is starting ... ")

default_map = generate_default_map()

state.set_map(default_map)

startsocket(state)
