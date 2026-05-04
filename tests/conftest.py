import socket
import subprocess
import sys
import time

import pytest


HOST = "127.0.0.1"
PORT = 8080


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
def control_center_server():
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