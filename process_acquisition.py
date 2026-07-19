import time

import psutil


def snapshot():
    connections = set()

    for connection in psutil.net_connections(kind="tcp"):
        if not connection.raddr or connection.status != "ESTABLISHED":
            continue

        remote_ip, remote_port = connection.raddr
        connections.add((connection.pid, remote_ip, remote_port))

    return connections


def process_acquisition(queue):
    seen = set()

    while True:
        current = snapshot()

        for connection in current - seen:
            queue.put(connection)

        seen = current
        time.sleep(1)
