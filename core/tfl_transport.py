"""
TfL Unified API integration
Handles Lines, Stops, and Arrivals for educational use
"""

import requests
from config import get_tfl_config  # importa la funzione che legge la chiave dal .env

CFG = get_tfl_config()
BASE_URL = "https://api.tfl.gov.uk"

def get_lines():
    """Fetch all Tube lines"""
    url = f"{BASE_URL}/Line/Mode/tube"
    params = {"app_key": CFG["app_key"]} if CFG["app_key"] else {}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return [x.get("name") for x in r.json()]

def search_stops(query="Oxford Circus"):
    """Search stops by name"""
    url = f"{BASE_URL}/StopPoint/Search"
    params = {"query": query, "modes": "tube,bus"}
    if CFG["app_key"]:
        params["app_key"] = CFG["app_key"]
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return [m.get("name") for m in data.get("matches", [])][:5]

def get_arrivals(stop_id="940GZZLUKSX"):
    """Get arrivals for a given StopPoint ID"""
    url = f"{BASE_URL}/StopPoint/{stop_id}/Arrivals"
    params = {"app_key": CFG["app_key"]} if CFG["app_key"] else {}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    arr = r.json()
    arr.sort(key=lambda a: a.get("timeToStation", 10**9))
    return [
        {
            "line": a.get("lineName"),
            "destination": a.get("destinationName"),
            "mins": a.get("timeToStation", 0) // 60
        } for a in arr[:5]
    ]
