import socket
import subprocess
import sys
import time

import uuid
import pytest


HOST = "127.0.0.1"
PORT = 8080


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_control_center: test does not need the control-center server",
    )


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> None:
    start = time.time()

    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)

    raise RuntimeError(f"Server did not start on {host}:{port} within {timeout} seconds")


@pytest.fixture(scope="session", autouse=True)
def control_center_server(request):
    selected_tests = request.session.items
    if selected_tests and all(
        item.get_closest_marker("no_control_center")
        for item in selected_tests
    ):
        yield
        return

    process = subprocess.Popen(
        [sys.executable, "-m", "app.control_center.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_server(HOST, PORT, timeout=10.0)
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def unique_id():
    def _make(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
    return _make
