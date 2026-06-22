import json
import time
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


BASE_URL = "http://localhost:8000"
PAYLOAD_FILE = Path(__file__).parent / "test_webhooks.json"
MAX_WORKERS = 20


def send_webhook(webhook: dict) -> dict:
    gateway = webhook["gateway"]
    url = f"{BASE_URL}/webhooks/{gateway}"

    started_at = time.time()

    try:
        response = requests.post(
            url,
            json=webhook,
            timeout=20,
        )

        elapsed_ms = round((time.time() - started_at) * 1000, 2)

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return {
            "gateway": gateway,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "response": response_body,
        }

    except Exception as error:
        return {
            "gateway": gateway,
            "status_code": None,
            "elapsed_ms": None,
            "error": str(error),
        }


def get_app_status(result: dict) -> str:
    response = result.get("response")

    if isinstance(response, dict):
        return response.get("status", "unknown")

    if result.get("error"):
        return "request_error"

    return "unknown"


def main():
    with open(PAYLOAD_FILE, "r", encoding="utf-8") as file:
        webhooks = json.load(file)

    print(f"Enviando {len(webhooks)} webhooks...")
    print(f"Concorrência: {MAX_WORKERS} threads")

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(send_webhook, webhook)
            for webhook in webhooks
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            app_status = get_app_status(result)

            print(
                f"[{result['gateway']}] "
                f"http={result['status_code']} "
                f"status={app_status} "
                f"tempo={result['elapsed_ms']}ms"
            )

    status_counter = Counter(get_app_status(result) for result in results)

    print("\nResumo:")
    print(f"total_payloads: {len(results)}")

    print("\nexpected_distribution:")
    print(
        f"valid_approved_unique_in_lead_events: "
        f"{status_counter.get('accepted', 0)}"
    )
    print(
        f"dlq_decrypt_failed: "
        f"{status_counter.get('decrypt_failed', 0)}"
    )
    print(
        f"dlq_schema_failed: "
        f"{status_counter.get('schema_failed', 0)}"
    )
    print(
        f"duplicates_natural_key: "
        f"{status_counter.get('duplicate', 0)}"
    )
    print(
        f"non_approved_discarded: "
        f"{status_counter.get('discarded', 0)}"
    )

    unknown = status_counter.get("unknown", 0)
    request_error = status_counter.get("request_error", 0)

    if unknown or request_error:
        print("\nother:")
        print(f"unknown: {unknown}")
        print(f"request_error: {request_error}")


if __name__ == "__main__":
    main()