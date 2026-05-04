from app.control_center.tcpserversocket import startsocket
from app.common.state import SystemState

state = SystemState()

print("server is starting ... ")
startsocket(state)
