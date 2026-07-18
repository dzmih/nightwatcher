import ipaddress
import json
import os
import time

import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "ip_cache.json")
EVENTS_FILE = os.path.join(BASE_DIR, "events.json")

ip_cache = {}
events = []

def load_json(path):
    if not os.path.exists(path):
        return []

    for _ in range(5):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            time.sleep(0.1)

    return []


def save_json(path, data):
    temp_path = f"{path}.tmp"
    indent = 2 if path == CACHE_FILE else None

    for _ in range(5):
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=indent)
            os.replace(temp_path, path)
            return
        except OSError:
            time.sleep(0.1)

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=indent)
    except OSError:
        pass


def load_cache():
    global ip_cache

    cached = load_json(CACHE_FILE)
    if isinstance(cached, dict):
        ip_cache = cached
        return

    events = load_json(EVENTS_FILE)
    if not isinstance(events, list):
        return

    for event in events:
        ip = event.get("ip")
        if not ip or ip in ip_cache:
            continue

        ip_cache[ip] = {
            "country": event.get("country"),
            "lat": event.get("lat"),
            "lon": event.get("lon"),
            "city": event.get("city"),
            "query": ip,
            "org": event.get("org", ""),
            "as": event.get("as", ""),
            "isp": event.get("isp", "")
        }

    if ip_cache:
        save_json(CACHE_FILE, ip_cache)


def is_private_ip(ip):
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return True

    return address.is_private or address.is_loopback


def api_request(ip_url, events):
    try:
        response = requests.get(ip_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    return {
        "country": data.get("country"),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "city": data.get("city"),
        "query": data.get("query"),
        "org": data.get("org"),
        "as": data.get("as"),
        "isp": data.get("isp")
    }


def api_worker(queue):
    load_cache()
    events = load_json(EVENTS_FILE)

    while True:
        pid, remote_ip, remote_port = queue.get()

        try:
            result = ip_cache.get(remote_ip)

            if result is None and is_private_ip(remote_ip):
                result = {
                    "country": None,
                    "lat": None,
                    "lon": None,
                    "city": None,
                    "query": remote_ip
                }

            if result is None:
                time.sleep(0.5)
                result = api_request(f"http://ip-api.com/json/{remote_ip}")

            if result is None:
                continue

            if remote_ip not in ip_cache:
                ip_cache[remote_ip] = result

            event = {
                "id": time.time_ns(),
                "pid": pid,
                "ip": remote_ip,
                "port": remote_port,
                "country": result.get("country"),
                "city": result.get("city"),
                "lat": result.get("lat"),
                "lon": result.get("lon"),
                "as": result.get("as"),
                "isp": result.get("isp"),
                "org": result.get("org")
            }

            if not isinstance(events, list):
                events = []

            events.append(event)
        finally:
            queue.task_done()

def sync(events):
    while True:
        time.sleep(5)
        save_json(EVENTS_FILE, events)


