"""Scanning: fetch availability for all venues and parse results."""

import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests  # type: ignore

from api import fetch_availability

WEEKS_AHEAD = 2
DELAY_BETWEEN_REQUESTS = 0.1


def parse_price(price_str):
    """Split '140 PLN' into (140.0, 'PLN')."""
    if not price_str:
        return None, None
    match = re.match(r"([\d.]+)\s*(\w+)", str(price_str))
    if match:
        return float(match.group(1)), match.group(2)
    return None, None


def scan_venues(venues):
    """Fetch availability for all configured venues, return list of slot dicts."""
    today = datetime.now().date()
    end_date = today + timedelta(weeks=WEEKS_AHEAD)
    days = [today + timedelta(days=d) for d in range((end_date - today).days)]

    total_requests = len(venues) * len(days)
    request_count = 0

    rows = []
    for v in venues:
        print(f"    {v['tenant_name']}...", end="", flush=True)
        venue_slots = 0
        for day in days:
            request_count += 1
            day_str = day.strftime("%Y-%m-%d")
            try:
                availability = fetch_availability(v["tenant_id"], day)
            except requests.RequestException as e:
                print(f"\n  [ERROR] {v['tenant_name']} on {day_str}: {e}")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                continue

            for resource in availability:
                resource_id = resource.get("resource_id", "")
                court_info = v["resource_map"].get(resource_id, {})
                court_name = court_info.get("name", resource_id)
                court_type = court_info.get("type", "")

                for slot in resource.get("slots", []):
                    raw_time = slot.get("start_time", "")
                    if raw_time:
                        utc_dt = datetime.strptime(
                            f"{day_str} {raw_time}", "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=ZoneInfo("UTC"))
                        local_dt = utc_dt.astimezone(ZoneInfo("Europe/Warsaw"))
                        local_time = local_dt.strftime("%H:%M:%S")
                        local_date = local_dt.strftime("%Y-%m-%d")
                        local_weekday = local_dt.strftime("%A")
                    else:
                        local_time = raw_time
                        local_date = day_str
                        local_weekday = day.strftime("%A")

                    amount, currency = parse_price(slot.get("price", ""))
                    duration = slot.get("duration", "")

                    rows.append({
                        "venue": v["tenant_name"],
                        "city": v["city"],
                        "address": v["street"],
                        "court": court_name,
                        "court_type": court_type,
                        "date": local_date,
                        "weekday": local_weekday,
                        "start_time": local_time,
                        "duration_min": int(duration) if duration else None,
                        "price_amount": amount,
                        "price_currency": currency,
                    })
                    venue_slots += 1

            time.sleep(DELAY_BETWEEN_REQUESTS)

        print(f" {venue_slots} slots ({request_count}/{total_requests} requests)")

    return rows
