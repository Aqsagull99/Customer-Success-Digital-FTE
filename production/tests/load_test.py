"""
Load test for the Customer Success FTE using Locust.

Stage 3 Deliverable: Simulates multi-channel traffic to prove 24/7 readiness.

Usage (interactive UI):
    cd production
    locust -f tests/load_test.py --host=http://localhost:8000

Usage (headless - for CI/CD):
    locust -f tests/load_test.py --host=http://localhost:8000 \
        --headless -u 20 -r 5 --run-time 2m \
        --csv=tests/results/load_test

Usage (quick smoke test):
    locust -f tests/load_test.py --host=http://localhost:8000 \
        --headless -u 5 -r 2 --run-time 30s
"""

import random
import uuid

from locust import HttpUser, between, task, events
from locust.runners import MasterRunner


class WebFormUser(HttpUser):
    """Simulate users submitting support forms (most common channel)."""

    wait_time = between(1, 5)
    weight = 5  # Web form is most common

    @task(3)
    def submit_support_form(self):
        """Submit a new support ticket via web form."""
        categories = ["general", "technical", "billing", "feedback", "bug_report"]
        uid = uuid.uuid4().hex[:8]

        with self.client.post(
            "/support/submit",
            json={
                "name": f"Load Test User {uid}",
                "email": f"loadtest_{uid}@example.com",
                "subject": f"Load Test Query {random.randint(1, 100)}",
                "category": random.choice(categories),
                "message": "This is a load test message to verify system performance under sustained multi-channel traffic.",
            },
            name="/support/submit",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "ticket_id" not in data:
                    response.failure("No ticket_id in response")
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def check_ticket_status(self):
        """Check status of a random ticket."""
        fake_id = str(uuid.uuid4())
        # 404 is expected for random IDs - we just verify the endpoint works
        self.client.get(
            f"/support/ticket/{fake_id}",
            name="/support/ticket/[id]",
        )

    @task(1)
    def submit_with_validation_error(self):
        """Occasionally send invalid data to test error handling."""
        self.client.post(
            "/support/submit",
            json={
                "name": "A",  # Too short
                "email": "invalid",
                "subject": "X",
                "category": "bad",
                "message": "Short",
            },
            name="/support/submit (invalid)",
        )


class EmailSimUser(HttpUser):
    """Simulate Gmail webhook traffic."""

    wait_time = between(5, 15)
    weight = 2

    @task
    def simulate_gmail_webhook(self):
        """Send simulated Gmail Pub/Sub notification."""
        self.client.post(
            "/webhooks/gmail",
            json={
                "message": {
                    "data": "eyJ0ZXN0IjogdHJ1ZX0=",
                    "messageId": f"gmail-{uuid.uuid4().hex[:12]}",
                },
                "subscription": "projects/test/subscriptions/gmail-push",
            },
            name="/webhooks/gmail",
        )


class WhatsAppSimUser(HttpUser):
    """Simulate WhatsApp webhook traffic."""

    wait_time = between(5, 15)
    weight = 2

    @task
    def simulate_whatsapp_webhook(self):
        """Send simulated Twilio WhatsApp webhook."""
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        self.client.post(
            "/webhooks/whatsapp",
            data={
                "MessageSid": f"SM{uuid.uuid4().hex[:32]}",
                "From": f"whatsapp:{phone}",
                "Body": random.choice([
                    "I need help with my account",
                    "How do I reset my password?",
                    "My app is not working",
                    "human",
                    "Can you help me?",
                ]),
                "ProfileName": f"WhatsApp User {random.randint(1, 1000)}",
            },
            name="/webhooks/whatsapp",
        )


class HealthCheckUser(HttpUser):
    """Monitor system health during load test."""

    wait_time = between(3, 10)
    weight = 1

    @task(2)
    def check_health(self):
        """Verify health endpoint under load."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "healthy":
                    response.failure("Status not healthy")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(1)
    def check_metrics(self):
        """Check channel metrics under load."""
        self.client.get("/metrics/channels", name="/metrics/channels")

    @task(1)
    def check_customer_lookup(self):
        """Test customer lookup under load."""
        self.client.get(
            "/customers/lookup",
            params={"email": f"loadtest_{random.randint(1, 100)}@example.com"},
            name="/customers/lookup",
        )
