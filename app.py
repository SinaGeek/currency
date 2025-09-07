import requests
import json
import re
import os
import shutil
from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# --- Configuration ---
DATA_DIR = 'data'
CURRENT_PRICES_FILE = os.path.join(DATA_DIR, 'Prices_Current.json')
PREVIOUS_DAY_FILE = os.path.join(DATA_DIR, 'Prices_Previous.json')
NEW_PRICES_FILE = os.path.join(DATA_DIR, 'new.json')

app = Flask(__name__)

# --- Data Fetching ---


def make_request():
    try:
        url = "https://www.bonbast.com/json"
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "st_bb=0", "Referer": "https://www.bonbast.com/",
        }
        param_get = requests.get("https://www.bonbast.com", timeout=15)
        param_get.raise_for_status()
        param_match = re.search(r'param:\s*"([^"]+)"', param_get.text)
        if not param_match:
            raise Exception("Could not find dynamic parameter")
        dynamic_param = param_match.group(1)
        data = f"param={dynamic_param}"
        response = requests.post(url, headers=headers, data=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making request: {e}")
        return None

# --- Daily snapshot function ---


def save_daily_snapshot():
    if os.path.exists(CURRENT_PRICES_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        shutil.copyfile(CURRENT_PRICES_FILE, PREVIOUS_DAY_FILE)
        print(
            f"✅ Daily snapshot saved: '{PREVIOUS_DAY_FILE}' has been updated.")
    else:
        print("⚠️ Snapshot skipped: Current prices file not found.")

# --- Minute-by-minute update logic ---


def update_current_prices():
    print("⏰ Running minute-by-minute price update...")
    new_data_raw = make_request()
    if not new_data_raw:
        print("⚠️ Failed to fetch new data. Current prices file remains unchanged.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(NEW_PRICES_FILE, 'w') as f:
        json.dump(new_data_raw, f, indent=4)

    try:
        with open(CURRENT_PRICES_FILE, 'r') as f:
            current_prices = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        current_prices = {}

    updated = False
    for key, new_value in new_data_raw.items():
        try:
            float(new_value)
            current_prices[key] = new_value
            updated = True
        except (ValueError, TypeError):
            continue

    if updated:
        with open(CURRENT_PRICES_FILE, 'w') as f:
            json.dump(current_prices, f, indent=4)
        print("✅ Current prices file updated with all valid values from raw data.")

# --- Flask Routes ---


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/prices')
def get_prices():
    try:
        with open(CURRENT_PRICES_FILE, 'r') as f:
            current_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Current prices not available."}), 500
    try:
        with open(PREVIOUS_DAY_FILE, 'r') as f:
            previous_day_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        previous_day_data = {}

    return jsonify({"current": current_data, "previous": previous_day_data})

# --- NEW: Endpoint to get only current prices ---


@app.route('/get')
def get_current_prices():
    """A simple endpoint to get only the current prices."""
    try:
        with open(CURRENT_PRICES_FILE, 'r') as f:
            current_data = json.load(f)
        return jsonify(current_data)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Current prices file not found or is invalid."}), 404


@app.route('/trigger-update', methods=['POST'])
def trigger_update():
    print("🔵 Manual update triggered by button.")
    update_current_prices()
    return jsonify({"message": "Update process completed."})


# --- Main Execution Block ---
if __name__ == '__main__':
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(func=update_current_prices,
                      trigger="interval", minutes=1)
    scheduler.add_job(func=save_daily_snapshot,
                      trigger='cron', hour=0, minute=0)
    scheduler.start()

    print("🚀 Performing initial price update on startup...")
    os.makedirs(DATA_DIR, exist_ok=True)
    update_current_prices()

    app.run(debug=True, use_reloader=False)
