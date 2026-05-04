import socket
import json

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "rover-1",
    "unit": "vehicle",
    "vehicle_type": "rover",
    "position": {
        "x": 8,
        "y": 15
    }
}

body = json.dumps(payload)

request = (
    "POST /unit HTTP/1.1\r\n"
    "Host: control-center\r\n"
    "Content-Type: application/json\r\n"
    f"Content-Length: {len(body.encode())}\r\n"
    "\r\n"
    + body
)

s.send(request.encode())
print(s.recv(4096).decode())