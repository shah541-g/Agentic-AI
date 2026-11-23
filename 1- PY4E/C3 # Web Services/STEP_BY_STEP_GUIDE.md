# Step-by-Step Guide: Building Resilient Agent API Clients 🛠️

> **Target Files:**
> - Day 5: [`Tasks/m0-d05-api client.py`](Tasks/m0-d05-api%20client.py)
> - Day 6: [`Tasks/m0-d06-robust api.py`](Tasks/m0-d06-robust%20api.py)
>
> **Key Objective:** Build a production-ready, fault-tolerant HTTP client capable of interacting with REST APIs, handling network instability, and implementing exponential backoff.

---

## 🏗️ Step 1: Formulating Query Parameters & Basic Client (`m0-d05`)

### Problem
Raw string concatenation (`url + "?lat=" + lat + "&lon=" + lon`) causes malformed URLs when query parameters contain spaces, slashes, or special characters.

### Solution
Use `urllib.parse.urlencode()`:

```python
from urllib import request, parse, error
import json

service_url = "https://api.open-meteo.com/v1/forecast"

# Safe parameter mapping
params = {
    "latitude": "31.5204",
    "longitude": "74.3587",
    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"
}

# Formulates: ?latitude=31.5204&longitude=74.3587&current=temperature_2m%2Crelative_humidity_2m%2Cwind_speed_10m
full_url = f"{service_url}?{parse.urlencode(params)}"
print(f"Retrieving: {full_url}")

try:
    with request.urlopen(full_url) as response:
        raw_data = response.read().decode("utf-8")
        parsed_json = json.loads(raw_data)
        print(json.dumps(parsed_json, indent=4))
except error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")
except json.JSONDecodeError as e:
    print(f"Failed to parse server response as JSON: {e}")
```

---

## 🏗️ Step 2: Designing the Robust Client Class (`m0-d06`)

An enterprise agent requires a reusable class that encapsulates retries, authorization headers, custom user agents, and backoff calculations.

### Class Architecture
```python
from urllib import request, parse, error
import os
import json
import random
import time

class APIClient:
    def __init__(self, max_retries: int = 5, api_key: str = None):
        self.max_retries = max_retries
        self.api_key = api_key

    def get(self, url: str, params: dict = None) -> dict:
        # Formulate query string
        if params:
            url = f"{url}?{parse.urlencode(params)}"

        # Configure secure headers
        headers = {
            "Accept": "application/json",
            "User-Agent": "RobustAPIClient/1.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
```

---

## 🏗️ Step 3: Implementing Retry Logic & Exponential Backoff

Inside the `.get()` method, loop over attempts:

```python
        for attempt in range(self.max_retries):
            req = request.Request(url=url, headers=headers, method="GET")
            
            try:
                # Set a strict socket timeout (10 seconds) to prevent hanging
                with request.urlopen(req, timeout=10) as response:
                    print(f"[Attempt {attempt + 1}] Success: HTTP {response.status}")
                    data = response.read().decode("utf-8")
                    return json.loads(data)

            except error.HTTPError as e:
                print(f"[Attempt {attempt + 1}] HTTP Error: {e.code} {e.reason}")
                
                # Check if the error is transient/retryable
                is_retryable = (e.code == 429 or 500 <= e.code <= 599)
                if not is_retryable or attempt == self.max_retries - 1:
                    print("Non-retryable error or maximum attempts exceeded.")
                    raise

                # Check if the server specified a wait time in headers
                retry_after = e.headers.get("Retry-After")
                if retry_after:
                    wait_seconds = int(retry_after)
                else:
                    # Exponential backoff formula with jitter
                    wait_seconds = (2 ** attempt) + random.uniform(0.1, 1.0)

                print(f"Throttled or server busy. Retrying in {wait_seconds:.2f} seconds...")
                time.sleep(wait_seconds)

            except error.URLError as e:
                print(f"[Attempt {attempt + 1}] Network/DNS Error: {e.reason}")
                if attempt == self.max_retries - 1:
                    raise
                wait_seconds = (2 ** attempt) + random.uniform(0.1, 1.0)
                print(f"Network glitch. Retrying in {wait_seconds:.2f} seconds...")
                time.sleep(wait_seconds)
```

---

## 🧪 Testing the Client

Run the script from your terminal:

```bash
python "Tasks/m0-d06-robust api.py"
```

### Expected Output:
```text
Response Status: 200
{
    "latitude": 31.52,
    "longitude": 74.36,
    "current": {
        "time": "2026-11-23T08:30",
        "temperature_2m": 22.4,
        "relative_humidity_2m": 45,
        "wind_speed_10m": 7.2
    }
}
```

---

## 💡 Key Agentic Engineering Takeaways

1. **Never Fail Open on Unknown Errors:** If an API responds with `401 Unauthorized` or `404 Not Found`, retrying 5 times will not fix the issue—it will waste API quota and delay the user. Fail immediately on $4xx$ (except 429).
2. **Jitter Prevents The Thundering Herd Problem:** If 100 agent instances fail simultaneously, exponential backoff without jitter causes all 100 instances to retry at exact second boundaries ($2\text{s}, 4\text{s}, 8\text{s}$), crashing the API again. Random jitter breaks the synchronization.
3. **Strict Timeouts:** Always pass `timeout=10` to `urlopen()`. Unbounded sockets can hang an agent thread forever if a remote server stops transmitting packets midway.
