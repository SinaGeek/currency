import requests
import json
import re
from pathlib import Path


def make_request():
    # URL for the request
    url = "https://www.bonbast.com/json"

    # Headers equivalent to the JavaScript fetch headers
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": "st_bb=0", "Referer": "https://www.bonbast.com/",
    }
    # Get the dynamic param from the website - this is required!
    print("Fetching dynamic parameter from website...")

    # Get the parameter from website - no fallbacks, no retries
    param_get = requests.get("https://www.bonbast.com")
    param_get.raise_for_status()

    # Extract the dynamic param using regex
    param_match = re.search(r'param:\s*"([^"]+)"', param_get.text)

    if not param_match:
        raise Exception("Could not find dynamic parameter in website response")

    dynamic_param = param_match.group(1)
    print(f"✅ Successfully extracted dynamic param: {dynamic_param}")

    # Request body data using the dynamic param
    data = f"param={dynamic_param}"

    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=data)

        # Check if request was successful
        response.raise_for_status()

        # Return parsed JSON directly (minimal change requested)
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


if __name__ == "__main__":
    print("Making request to bonbast.com...")
    result_json = make_request()

    if result_json:
        print("Response (JSON):")
        print(json.dumps(result_json, indent=2))
        print(f"\nRequest completed successfully!")
    else:
        print("Request failed!")
