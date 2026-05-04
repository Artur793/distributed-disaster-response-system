import socket
import json

s = socket.socket()
s.connect(("control-center", 8080))

payload = {
    "id": "vibration-1",
    "unit": "sensor",
    "sensor_type": "vibration",
    "position": {
        "x": 15,
        "y": 18
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