import requests
from process_acquisition import snapshot


def api_request(ip_url: str):
    response = requests.get(ip_url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data.get("country")
    print("failed to fetch data")
    return None

def api_worker(q):
    while True:
        pid, remote_ip, remote_port = q.get()

        api_request_str = f"http://ip-api.com/json/{remote_ip}"
        result = api_request(api_request_str)

        if result is not None:
            print(pid, remote_ip, result)

        q.task_done()