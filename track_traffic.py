import os
import requests
import json

TOKEN = os.getenv("TRAFFIC_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
DATA_FILE = "traffic_history.json"

def fetch_data():
    v_url = f"https://github.com"
    c_url = f"https://github.com"
    print(f"DEBUG - Views URL: {v_url}")
    print(f"DEBUG - Clones URL: {c_url}")
    return requests.get(v_url, headers=HEADERS).json().get('views', []), requests.get(c_url, headers=HEADERS).json().get('clones', [])

def update():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: history = json.load(f)
    else:
        history = {"views": {}, "clones": {}}

    views, clones = fetch_data()

    for day in views:
        history["views"][day['timestamp'][:10]] = {"count": day['count'], "uniques": day['uniques']}
    for day in clones:
        history["clones"][day['timestamp'][:10]] = {"count": day['count'], "uniques": day['uniques']}

    with open(DATA_FILE, "w") as f: json.dump(history, f, indent=2)

if __name__ == "__main__":
    update()
