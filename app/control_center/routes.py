from app.control_center.handlers import (
    handle_get_status,
    handle_get_map,
    handle_post_unit,
    handle_post_incident,
    handle_get_dashboard,
)

# Decides which handler to call based on method + path
def handle_request(method: str, path: str, headers: dict[str, str], body: str, state):
    if path == "/status":
        if method != "GET":
            return 405, {"Content-Type": "text/plain"}, "Method Not Allowed"
        return handle_get_status(state)

    if path == "/map":
        if method != "GET":
            return 405, {"Content-Type": "text/plain"}, "Method Not Allowed"
        return handle_get_map(state)

    if path == "/unit":
        if method != "POST":
            return 405, {"Content-Type": "text/plain"}, "Method Not Allowed"
        return handle_post_unit(body, state)

    if path == "/incident":
        if method != "POST":
            return 405, {"Content-Type": "text/plain"}, "Method Not Allowed"
        return handle_post_incident(body, state)
    
    if path == "/dashboard":
        if method != "GET":
            return 405, {"Content-Type": "text/plain"}, "Method Not Allowed"
        return handle_get_dashboard(state)

    return 404, {"Content-Type": "text/plain"}, "Not Found"