"""Playtomic API fetching: venues and availability."""

import requests  # type: ignore

API_BASE = "https://api.playtomic.io/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SPORT_ID = "PADEL"
WARSAW_LAT = 52.2297
WARSAW_LON = 21.0122
RADIUS_METERS = 50000


def fetch_all_venues():
    """Fetch all padel venues in Warsaw area."""
    r = requests.get(f"{API_BASE}/tenants", params={
        "coordinate": f"{WARSAW_LAT},{WARSAW_LON}",
        "sport_id": SPORT_ID,
        "radius": RADIUS_METERS,
        "size": 200,
    }, headers=HEADERS)
    r.raise_for_status()

    result = []
    for v in r.json():
        resource_map = {}
        for res in v.get("resources", []):
            if res.get("sport_id") == SPORT_ID and res.get("is_active"):
                resource_map[res["resource_id"]] = {
                    "name": res.get("name", "Unknown court"),
                    "type": res.get("properties", {}).get("resource_type", ""),
                    "size": res.get("properties", {}).get("resource_size", ""),
                }
        result.append({
            "tenant_id": v["tenant_id"],
            "tenant_name": v.get("tenant_name", "Unknown"),
            "city": v.get("address", {}).get("city", ""),
            "street": v.get("address", {}).get("street", ""),
            "resource_map": resource_map,
        })
    return result


def fetch_venues(venue_ids):
    """Fetch venue info only for configured tenant IDs."""
    all_venues = fetch_all_venues()
    return [v for v in all_venues if v["tenant_id"] in venue_ids]


def fetch_availability(tenant_id, date):
    """Fetch availability for a single venue on a single day."""
    start_min = f"{date.strftime('%Y-%m-%d')}T00:00:00"
    start_max = f"{date.strftime('%Y-%m-%d')}T23:59:59"

    r = requests.get(f"{API_BASE}/availability", params={
        "sport_id": SPORT_ID,
        "tenant_id": tenant_id,
        "start_min": start_min,
        "start_max": start_max,
    }, headers=HEADERS)
    r.raise_for_status()
    return r.json()
