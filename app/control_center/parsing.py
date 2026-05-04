def recv_full_request(sock, buffer):  # prototype ##### , had to be done with some better way
    
    chunk = sock.recv(4096)   # one time because , one request at a time
    if not chunk:
        return None, None, buffer

    buffer += chunk

    # Need at least headers
    if b"\r\n\r\n" not in buffer:
        return None, None, buffer

    header_part, rest = buffer.split(b"\r\n\r\n", 1)
    headers_text = header_part.decode(errors="ignore")

    # Extract Content-Length
    content_length = 0
    for line in headers_text.split("\r\n"):
        if line.lower().startswith("content-length"):
            content_length = int(line.split(":")[1].strip())

    # remaining full body
    if len(rest) < content_length:
        return None, None, buffer

    body = rest[:content_length]
    remaining = rest[content_length:]

    body_text = body.decode(errors="ignore")

    return headers_text, body_text, remaining


def parsingrequest(headers_text, body_text):

    request_line = headers_text.split("\r\n")[0]
    method, path, _ = request_line.split()  # separating method and path from the request header

    if method == "POST" and path == "/vehicles":
        status = "201 Created"
        response_body = "Vehicle registered\n" + body_text

    elif method == "POST" and path == "/sensors":
        status = "200 OK"
        response_body = "Sensor data stored\n" + body_text

    elif method == "GET" and path == "/map":
        status = "200 OK"
        response_body = "Here is the map"

    elif method == "GET" and path == "/status":
        status = "200 OK"
        response_body = "ALL GOOD"

    else:
        return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Length: 9\r\n\r\n"
            "Not Found"
        )

    response = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        "\r\n"
        f"{response_body}"
        )
    return response 