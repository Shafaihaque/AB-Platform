"""Fires simulated events against the ingest service to populate ClickHouse with test data."""
import random
import concurrent.futures
import requests

INGEST_URL = "http://localhost:8080/events"

EXPERIMENT_ID = input("Experiment ID: ").strip()
CONTROL_ID = input("Control variant ID: ").strip()
VARIANT_A_ID = input("Variant A variant ID: ").strip()

# Control converts at 40%, variant_a at 55%
VARIANTS = [
    {"id": CONTROL_ID, "name": "control", "conversion_rate": 0.40},
    {"id": VARIANT_A_ID, "name": "variant_a", "conversion_rate": 0.55},
]

def seed_user(args):
    variant, i = args
    user_id = f"seed_user_{variant['name']}_{i}"
    requests.post(INGEST_URL, json={
        "experiment_id": EXPERIMENT_ID,
        "variant_id": variant["id"],
        "user_id": user_id,
        "event_type": "exposure",
    })
    if random.random() < variant["conversion_rate"]:
        requests.post(INGEST_URL, json={
            "experiment_id": EXPERIMENT_ID,
            "variant_id": variant["id"],
            "user_id": user_id,
            "event_type": "conversion",
        })

tasks = [(variant, i) for variant in VARIANTS for i in range(500)]
print(f"Seeding {len(tasks)} users concurrently...")

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    executor.map(seed_user, tasks)

print("Done. Wait a few seconds then check /results.")
