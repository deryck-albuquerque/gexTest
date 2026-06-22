import json
import random
from pathlib import Path

from locust import HttpUser, task, between


PAYLOAD_FILE = Path("tests/test_webhooks.json")


class WebhookUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        with open(PAYLOAD_FILE, "r", encoding="utf-8") as file:
            self.webhooks = json.load(file)

    @task
    def send_random_webhook(self):
        webhook = random.choice(self.webhooks)

        gateway = webhook["gateway"]

        self.client.post(
            f"/webhooks/{gateway}",
            json=webhook,
            name=f"POST /webhooks/{gateway}",
            timeout=15
        )