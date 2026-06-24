import os
import json
import urllib.request
from datetime import datetime, timezone

# GPU models to track (Ornn API identifiers)
GPUS = [
    {"name": "H100 SXM",  "label": "H100 SXM ",  "emoji": "🟢"},
    {"name": "H200",       "label": "H200     ",  "emoji": "🔵"},
    {"name": "B200",       "label": "B200     ",  "emoji": "🟣"},
    {"name": "A100 SXM4",  "label": "A100 SXM4",  "emoji": "⚪"},
    {"name": "RTX 5090",   "label": "RTX 5090 ",  "emoji": "🟡"},
]

BASE_URL = "https://api.ornnai.com/api/gpu/{}/index-history"
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def fetch_latest_price(gpu_name: str) -> float | None:
    url = BASE_URL.format(urllib.parse.quote(gpu_name))
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("success") and data.get("data"):
                return data["data"][-1]["index_value"]
    except Exception as e:
        print(f"Error fetching {gpu_name}: {e}")
    return None


def build_slack_message(prices: dict) -> dict:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    lines = [f"📊 *OCPI Daily GPU Price Index* — {today}"]
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for gpu in GPUS:
        price = prices.get(gpu["name"])
        if price is not None:
            lines.append(f"{gpu['emoji']}  *{gpu['label']}*   `${price:.2f} / hr`")
        else:
            lines.append(f"{gpu['emoji']}  *{gpu['label']}*   `N/A`")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("_Source: <https://index.ornn.com|index.ornn.com>_")

    return {"text": "\n".join(lines)}


def post_to_slack(payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Slack response: {resp.status}")


if __name__ == "__main__":
    import urllib.parse

    print("Fetching GPU prices from Ornn...")
    prices = {}
    for gpu in GPUS:
        price = fetch_latest_price(gpu["name"])
        prices[gpu["name"]] = price
        status = f"${price:.2f}/hr" if price else "FAILED"
        print(f"  {gpu['name']}: {status}")

    payload = build_slack_message(prices)
    print("\nPosting to Slack...")
    post_to_slack(payload)
    print("Done!")
