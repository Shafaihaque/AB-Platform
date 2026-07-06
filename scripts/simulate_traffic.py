"""Simulates realistic traffic across all running experiments."""
import random
import concurrent.futures
import requests

API_URL = "http://localhost:8000"
INGEST_URL = "http://localhost:8080"
USERS_PER_VARIANT = 300

# rates based on industry benchmarks
VARIANT_RATES: dict[str, float] = {
    "control": 0.35,
    "sign_in": 0.38,
    "get_started": 0.48,
    "nudge": 0.55,
}


def fetch_running_experiments():
    """Returns all running experiments with their variants."""
    experiments = requests.get(f"{API_URL}/experiments").json()
    running = [e for e in experiments if e["status"] == "running"]
    result = []
    for exp in running:
        variants = requests.get(f"{API_URL}/experiments/{exp['id']}/variants").json()
        result.append({"experiment": exp, "variants": variants})
    return result


def seed_user(args):
    experiment_id, variant, user_index = args
    user_id = f"sim_{experiment_id[:8]}_{variant['name']}_{user_index}"
    requests.post(f"{INGEST_URL}/events", json={
        "experiment_id": experiment_id,
        "variant_id": variant["id"],
        "user_id": user_id,
        "event_type": "exposure",
    })
    rate = VARIANT_RATES.get(variant["name"], 0.40)
    if random.random() < rate:
        requests.post(f"{INGEST_URL}/events", json={
            "experiment_id": experiment_id,
            "variant_id": variant["id"],
            "user_id": user_id,
            "event_type": "conversion",
        })


def main():
    print("Fetching running experiments...")
    experiments = fetch_running_experiments()

    if not experiments:
        print("No running experiments found.")
        return

    tasks = []
    for entry in experiments:
        exp = entry["experiment"]
        variants = entry["variants"]
        print(f"  → {exp['name']} ({len(variants)} variants, {USERS_PER_VARIANT} users each)")
        for variant in variants:
            for i in range(USERS_PER_VARIANT):
                tasks.append((exp["id"], variant, i))

    print(f"\nSimulating {len(tasks)} users concurrently...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(seed_user, tasks)

    print("Done. Check /results for updated stats.")


if __name__ == "__main__":
    main()
