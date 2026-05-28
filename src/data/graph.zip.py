import requests
import csv
import io
import zipfile
import sys
import time

# Fix binary output on Windows (Python opens sys.stdout in text mode by default)
if hasattr(sys.stdout, 'buffer'):
    stdout = sys.stdout.buffer
else:
    stdout = sys.stdout

# New Piveau API base URL
BASE = "https://www.data.gv.at/api/hub/repo"

def get_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# Fetch application URIs
print("Fetching application list...", file=sys.stderr)
app_uris = get_json(f"{BASE}/resources/applications") # file contains list of application URIs
app_ids = [uri.strip().split("/")[-1] for uri in app_uris if uri.strip()] # extract application IDs from URIs
print(f"Found {len(app_ids)} applications.", file=sys.stderr)

# Fetch each application JSON
applications = []
dataset_ids = set()

for i, app_id in enumerate(app_ids):
    try:
        data = get_json(f"{BASE}/resources/applications/{app_id}")

        # find the main application node in @graph
        graph = data.get("@graph", [])
        app_node = next((n for n in graph if n.get("@type") == "http://dcat-ap.at/Application"), None)
        if not app_node:
            app_node = next((n for n in graph if "dct:title" in n), None)
        if not app_node:
            continue

        # extract title
        title_raw = app_node.get("dct:title", app_id)
        if isinstance(title_raw, dict):
            title = title_raw.get("@value", app_id)
        elif isinstance(title_raw, list):
            title = next((t.get("@value", app_id) for t in title_raw if isinstance(t, dict)), app_id)
        else:
            title = str(title_raw)

        # extract dataset IDs from dcat:servesDataset
        serves = app_node.get("dcat:servesDataset", [])
        if isinstance(serves, dict):
            serves = [serves]

        app_dataset_ids = []
        for entry in serves:
            uri = entry.get("@id", "")
            ds_id = uri.strip().split("/")[-1]
            if ds_id:
                app_dataset_ids.append(ds_id)
                dataset_ids.add(ds_id)

        applications.append({"id": app_id, "title": f"Application: {title}", "dataset_ids": app_dataset_ids})

        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(app_ids)} applications...", file=sys.stderr)

    except Exception as e:
        print(f"Warning: skipping application {app_id}: {e}", file=sys.stderr)

    finally:
        time.sleep(0.1)  # be polite to the server

# Fetch each dataset JSON
print(f"Fetching {len(dataset_ids)} datasets...", file=sys.stderr)
datasets = {}

for i, ds_id in enumerate(dataset_ids):
    try:
        data = get_json(f"{BASE}/datasets/{ds_id}?locale=de")
        time.sleep(0.1)  # be polite to the server
        graph = data.get("@graph", [])

        title = ds_id
        for node in graph:
            t = node.get("dct:title", "")
            if isinstance(t, dict):
                title = t.get("@value", ds_id)
                break
            elif isinstance(t, list):
                title = next((x.get("@value", ds_id) for x in t if isinstance(x, dict)), ds_id)
                break
            elif isinstance(t, str) and t:
                title = t
                break

        datasets[ds_id] = f"Dataset: {title}"

        if (i + 1) % 50 == 0:
            print(f"Fetched {i + 1}/{len(dataset_ids)} datasets...", file=sys.stderr)

    except Exception as e:
        print(f"Warning: skipping dataset {ds_id}: {e}", file=sys.stderr)

    finally:
        time.sleep(0.1)  # be polite to the server

# Compute connection counts
app_connection_counts = {app["id"]: len(app["dataset_ids"]) for app in applications}
dataset_connection_counts = {ds_id: 0 for ds_id in datasets}
for app in applications:
    for ds_id in app["dataset_ids"]:
        if ds_id in dataset_connection_counts:
            dataset_connection_counts[ds_id] += 1

# Assemble CSVs in correct format for D3 force-directed graph
nodes_buf = io.StringIO()
nodes_writer = csv.writer(nodes_buf)
nodes_writer.writerow(["id", "group", "title", "connections"])
for app in applications:
    nodes_writer.writerow([app["id"], "Application", app["title"], app_connection_counts[app["id"]]])
for ds_id, ds_title in datasets.items():
    nodes_writer.writerow([ds_id, "Dataset", ds_title, dataset_connection_counts.get(ds_id, 0)])

links_buf = io.StringIO()
links_writer = csv.writer(links_buf)
links_writer.writerow(["source", "target", "value"])
for app in applications:
    for ds_id in app["dataset_ids"]:
        if ds_id in datasets:
            links_writer.writerow([app["id"], ds_id, 1])

# Assemble ZIP file
print("Writing output ZIP...", file=sys.stderr)
zip_buf = io.BytesIO()
with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("formattedNodes.csv", nodes_buf.getvalue())
    zf.writestr("formattedLinks.csv", links_buf.getvalue())

stdout.write(zip_buf.getvalue())
print("Done.", file=sys.stderr)