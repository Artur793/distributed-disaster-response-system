from app.control_center.routes import handle_request


def recv_full_request(sock, buffer):  # prototype ##### , had to be done with some better way
    
    chunk = sock.recv(4096)   # one time because , one request at a time
    if not chunk:
        raise ConnectionResetError

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


def parse_headers(headers_text: str) -> dict[str, str]:
    lines = headers_text.split("\r\n")[1:]
    headers = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    return headers


def reason_phrase(status_code: int) -> str:
    reasons = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        500: "Internal Server Error",
    }
    return reasons.get(status_code, "OK")


def parsing_request(headers_text: str, body_text: str, state) -> bytes:

    request_line = headers_text.split("\r\n")[0]
    method, path, _ = request_line.split()  # Parse request line

    headers = parse_headers(headers_text) # Parse headers into dict

    status_code, response_headers, response_body = handle_request(method, path, headers, body_text, state) # Router call

    # Structure full raw HTTP response
    body_bytes = response_body.encode("utf-8")
    reason = reason_phrase(status_code)

    response = f"HTTP/1.1 {status_code} {reason}\r\n"

    for key, value in response_headers.items():
        response += f"{key}: {value}\r\n"

    response += f"Content-Length: {len(body_bytes)}\r\n"    # Use body_bytes to avoid problems with non-ASCII characters
    response += "Connection: close\r\n"
    response += "\r\n"

    return response.encode("utf-8") + body_bytes
