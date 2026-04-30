import socket
import time
s = socket.socket()
s.connect(("control-center", 8080))

xml_body = """<?xml version="1.0" encoding="UTF-8"?>
<vehicle>
    <name>Scout-Alpha</name>
    <type>drone</type>
    <location>
        <x>5</x>
        <y>12</y>
    </location>
</vehicle>
"""

request = (
    "POST /vehicles HTTP/1.1\r\n"
    "Host: control-center\r\n"
    "Content-Type: application/xml\r\n"
    f"Content-Length: {len(xml_body.encode())}\r\n"
    "\r\n"
    + xml_body
)
request1 = (
    "GET /map HTTP/1.1\r\n"
    "Host: control-center\r\n"
    "\r\n"
)
s.send(request1.encode())
print(s.recv(4096).decode())
s.send(request.encode())
print(s.recv(4096).decode())

