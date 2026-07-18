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
    while True:
        for connection in snapshot():
            queue.put(connection)

        time.sleep(1)
