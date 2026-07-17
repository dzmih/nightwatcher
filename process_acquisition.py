import time
import psutil

def snapshot():
    current = set()
    for c in psutil.net_connections(kind="tcp"):
        if not c.raddr or c.status != "ESTABLISHED":
            continue
        remote_ip, remote_port = c.raddr
        current.add((c.pid, remote_ip, remote_port))
    return current

def process_acquisition(q):
    seen = set()
    while True:
        current = set()

        for c in psutil.net_connections(kind="tcp"):
            if not c.raddr or c.status != "ESTABLISHED":
                continue

            remote_ip, remote_port = c.raddr
            connection = (c.pid, remote_ip, remote_port)
            current.add(connection)

            if connection not in seen:
                try:
                    process = psutil.Process(c.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process = f"PID {c.pid}"

                q.put((c.pid, remote_ip, remote_port))

        seen = current
        time.sleep(1)

if __name__ == "__main__":
    process_acquisition()