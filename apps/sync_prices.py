import json
from pathlib import Path
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # Fallback if not available; will keep UTC string

from .updateprice import make_request


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
NEW_JSON = DATA_DIR / "new.json"
CURRENT_JSON = DATA_DIR / "Prices_Current.json"
PREVIOUS_JSON = DATA_DIR / "Prices_Previous.json"

META_FIELDS = {
    "created",
    "last_modified",
    "day",
    "month",
    "year",
    "hour",
    "minute",
    "second",
    "weekday",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: dict):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parse_created(dt_str: str):
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, "%B %d, %Y %H:%M")
    except Exception:
        return None


def utc_to_tehran_string(dt_str: str) -> str | None:
    """Convert a naive UTC-like string "%B %d, %Y %H:%M" to Asia/Tehran local time string.
    If zoneinfo is unavailable or parsing fails, return original or None.
    """
    if not dt_str:
        return None
    if ZoneInfo is None:
        return dt_str
    try:
        # Parse as naive, then set UTC and convert
        dt_naive = datetime.strptime(dt_str, "%B %d, %Y %H:%M")
        dt_utc = dt_naive.replace(tzinfo=ZoneInfo("UTC"))
        dt_tehran = dt_utc.astimezone(ZoneInfo("Asia/Tehran"))
        return dt_tehran.strftime("%B %d, %Y %H:%M")
    except Exception:
        return dt_str


def update_flow():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    resp_json = make_request()
    if not resp_json:
        print("Request failed!")
        return False

    # 1) Write new.json
    dump_json(NEW_JSON, resp_json)

    # 2) Merge into Prices_Current.json for keys that exist
    current = load_json(CURRENT_JSON)
    updated = False
    for key in list(current.keys()):
        if key in resp_json:
            new_value = resp_json[key]
            # Convert last_modified (UTC) to Tehran before saving into current
            if key == "last_modified":
                converted_value = utc_to_tehran_string(new_value)
                new_value = converted_value if converted_value else new_value
            if current.get(key) != new_value:
                current[key] = new_value
                updated = True
    if updated:
        dump_json(CURRENT_JSON, current)

    # 3) Refresh Prices_Previous.json if its 'last_modified' is not yesterday relative to CURRENT 'last_modified'
    prev = load_json(PREVIOUS_JSON)
    curr_last_modified_dt = parse_created(current.get("last_modified"))
    prev_last_modified_dt = parse_created(prev.get("last_modified"))
    needs_refresh = True
    if curr_last_modified_dt and prev_last_modified_dt:
        needs_refresh = prev_last_modified_dt.date() != (
            curr_last_modified_dt.date() - timedelta(days=1))

    if needs_refresh and prev:
        changed = False
        for key in list(prev.keys()):
            if key in META_FIELDS:
                continue
            if key in current and prev.get(key) != current.get(key):
                prev[key] = current[key]
                changed = True
        if changed:
            dump_json(PREVIOUS_JSON, prev)

    print("Sync flow finished.")
    return True


if __name__ == "__main__":
    update_flow()
