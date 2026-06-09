import requests
import json
import sys
import os
import subprocess

BASE = "https://www.data.gv.at/api/hub/repo"
CACHE_FILE = "src/.observablehq/cache/data/app_ids.json"
GRAPH_CACHE = "src/.observablehq/cache/data/graph.zip"

def get_current_ids():
    r = requests.get(f"{BASE}/resources/applications", timeout=30)
    r.raise_for_status()
    return set(uri.strip().split("/")[-1] for uri in r.json() if uri.strip())

def get_cached_ids():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE) as f:
        return set(json.load(f))

def save_ids(ids):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(list(ids), f)

def run_loader():
    # Remove graph cache so Observable reruns the loader
    if os.path.exists(GRAPH_CACHE):
        os.remove(GRAPH_CACHE)
    # Run the data loader directly and write output to the cache
    os.makedirs(os.path.dirname(GRAPH_CACHE), exist_ok=True)
    result = subprocess.run(
        ["python", "src/data/graph.zip.py"],
        capture_output=False,
        stdout=open(GRAPH_CACHE, "wb"),
        stderr=sys.stderr
    )
    if result.returncode != 0:
        print("Error: data loader failed.", file=sys.stderr)
        sys.exit(1)

current_ids = get_current_ids()
cached_ids = get_cached_ids()

if cached_ids is None:
    print("No cache found — running full data loader.", file=sys.stderr)
    save_ids(current_ids)
    run_loader()
elif current_ids != cached_ids:
    added = current_ids - cached_ids
    removed = cached_ids - current_ids
    print(f"Changes detected: {len(added)} added, {len(removed)} removed — rerunning loader.", file=sys.stderr)
    save_ids(current_ids)
    run_loader()
else:
    print("No changes detected — skipping data reload.", file=sys.stderr)