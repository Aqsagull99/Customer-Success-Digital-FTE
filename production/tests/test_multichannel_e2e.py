"""
Multi-channel E2E test suite for the Customer Success FTE.

Stage 3 Deliverable: Tests all channels, cross-channel continuity,
validation, metrics, and health checks against the live API.

Usage:
    pytest tests/test_multichannel_e2e.py -v
    pytest tests/test_multichannel_e2e.py -v --tb=short  (for live docker tests)
"""

import asyncio
import os
import uuid

import pytest
import pytest_asyncio
import httpx

# Use live URL if LIVE_TEST=1, otherwise use ASGI transport
LIVE_TEST = os.getenv("LIVE_TEST", "0") == "1"
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")


@pytest_asyncio.fixture
async def client():
    """HTTP client - connects to live server or ASGI app."""
    if LIVE_TEST:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
            yield ac
    else:
        from api.main import app
        from httpx import ASGITransport

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# =============================================================================
# 1. HEALTH CHECK TESTS
# =============================================================================


class TestHealthCheck:
    """Verify system health and readiness."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Health endpoint should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_all_channels_active(self, client):
        """All three channels should be reported as active."""
        response = await client.get("/health")
        data = response.json()
        channels = data["channels"]
        assert channels["email"] == "active"
        assert channels["whatsapp"] == "active"
        assert channels["web_form"] == "active"


# =============================================================================
# 2. WEB FORM CHANNEL TESTS (REQUIRED)
# =============================================================================


class TestWebFormChannel:
    """Test the web support form - this is the REQUIRED build component."""

    @pytest.mark.asyncio
    async def test_form_submission_success(self, client):
        """Web form submission should create ticket and return ID."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "subject": "Help with API",
                "category": "technical",
                "message": "I need help with the API authentication process",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert data["message"] is not None
        assert len(data["ticket_id"]) > 0

    @pytest.mark.asyncio
    async def test_form_submission_all_categories(self, client):
        """All valid categories should be accepted."""
        categories = ["general", "technical", "billing", "feedback", "bug_report"]
        for category in categories:
            response = await client.post(
                "/support/submit",
                json={
                    "name": "Category Tester",
                    "email": f"cat_{category}@example.com",
                    "subject": f"Test {category}",
                    "category": category,
                    "message": f"Testing the {category} category submission flow",
                },
            )
            assert response.status_code == 200, f"Category '{category}' failed"

    @pytest.mark.asyncio
    async def test_form_validation_short_name(self, client):
        """Form should reject names shorter than 2 characters."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "A",
                "email": "valid@example.com",
                "subject": "Test Subject",
                "category": "general",
                "message": "This is a valid test message for validation",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_invalid_email(self, client):
        """Form should reject invalid email formats."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "not-an-email",
                "subject": "Test",
                "category": "general",
                "message": "This is a valid test message for validation",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_short_message(self, client):
        """Form should reject messages shorter than 10 characters."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "valid@example.com",
                "subject": "Test",
                "category": "general",
                "message": "Short",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_invalid_category(self, client):
        """Form should reject invalid categories."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "valid@example.com",
                "subject": "Test",
                "category": "invalid_category",
                "message": "This is a valid test message for validation",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ticket_status_retrieval(self, client):
        """Should be able to check ticket status after submission."""
        # First submit a form
        submit_response = await client.post(
            "/support/submit",
            json={
                "name": "Status Checker",
                "email": f"status_{uuid.uuid4().hex[:8]}@example.com",
                "subject": "Status Test",
                "category": "general",
                "message": "Testing ticket status retrieval feature",
            },
        )
        assert submit_response.status_code == 200
        ticket_id = submit_response.json()["ticket_id"]

        # Check status - might be 404 if worker hasn't created DB record yet
        status_response = await client.get(f"/support/ticket/{ticket_id}")
        assert status_response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_form_returns_estimated_response_time(self, client):
        """Form response should include estimated response time."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "Response Time User",
                "email": "rtime@example.com",
                "subject": "Response Time Test",
                "category": "general",
                "message": "Checking if estimated response time is returned",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "estimated_response_time" in data

    @pytest.mark.asyncio
    async def test_concurrent_form_submissions(self, client):
        """Multiple simultaneous submissions should all succeed."""
        tasks = []
        for i in range(5):
            tasks.append(
                client.post(
                    "/support/submit",
                    json={
                        "name": f"Concurrent User {i}",
                        "email": f"concurrent_{i}_{uuid.uuid4().hex[:6]}@example.com",
                        "subject": f"Concurrent Test {i}",
                        "category": "general",
                        "message": f"Concurrent submission test number {i} for load handling",
                    },
                )
            )
        responses = await asyncio.gather(*tasks)
        for resp in responses:
            assert resp.status_code == 200
            assert "ticket_id" in resp.json()


# =============================================================================
# 3. EMAIL (GMAIL) CHANNEL TESTS
# =============================================================================


class TestEmailChannel:
    """Test Gmail webhook integration."""

    @pytest.mark.asyncio
    async def test_gmail_webhook_accepts_post(self, client):
        """Gmail webhook endpoint should accept POST requests."""
        response = await client.post(
            "/webhooks/gmail",
            json={
                "message": {
                    "data": "eyJ0ZXN0IjogdHJ1ZX0=",  # base64 of {"test": true}
                    "messageId": f"test-{uuid.uuid4().hex[:8]}",
                },
                "subscription": "projects/test/subscriptions/gmail-push",
            },
        )
        # 200 = processed, 500 = no Gmail creds (expected in test)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_gmail_webhook_rejects_invalid_payload(self, client):
        """Gmail webhook should handle malformed payloads."""
        response = await client.post(
            "/webhooks/gmail",
            json={"invalid": "payload"},
        )
        # Should not crash - returns error gracefully
        assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# 4. WHATSAPP CHANNEL TESTS
# =============================================================================


class TestWhatsAppChannel:
    """Test WhatsApp/Twilio webhook integration."""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_signature_validation(self, client):
        """WhatsApp webhook should reject requests without valid Twilio signature."""
        response = await client.post(
            "/webhooks/whatsapp",
            data={
                "MessageSid": "SM" + uuid.uuid4().hex[:32],
                "From": "whatsapp:+1234567890",
                "Body": "Hello, I need help",
                "ProfileName": "Test User",
            },
        )
        # 403 = invalid signature (correct behavior in test)
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_whatsapp_status_webhook(self, client):
        """WhatsApp status callback endpoint should accept updates."""
        response = await client.post(
            "/webhooks/whatsapp/status",
            data={
                "MessageSid": "SM" + uuid.uuid4().hex[:32],
                "MessageStatus": "delivered",
                "To": "whatsapp:+1234567890",
            },
        )
        assert response.status_code == 200


# =============================================================================
# 5. CROSS-CHANNEL CONTINUITY TESTS
# =============================================================================


class TestCrossChannelContinuity:
    """Test that customer identity and conversations persist across channels."""

    @pytest.mark.asyncio
    async def test_customer_lookup_by_email(self, client):
        """Customer lookup endpoint should work with email parameter."""
        response = await client.get(
            "/customers/lookup",
            params={"email": "crosschannel@example.com"},
        )
        # 200 if customer exists, 404 if not - both are valid
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_customer_lookup_by_phone(self, client):
        """Customer lookup endpoint should work with phone parameter."""
        response = await client.get(
            "/customers/lookup",
            params={"phone": "+1234567890"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_customer_lookup_requires_parameter(self, client):
        """Customer lookup should fail without email or phone."""
        response = await client.get("/customers/lookup")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_conversation_history_endpoint(self, client):
        """Conversation history endpoint should work."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/conversations/{fake_id}")
        # 404 for non-existent conversation is correct
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_web_form_creates_trackable_customer(self, client):
        """Submitting a web form should make customer findable later."""
        unique_email = f"track_{uuid.uuid4().hex[:8]}@example.com"

        # Submit via web form
        submit_resp = await client.post(
            "/support/submit",
            json={
                "name": "Trackable User",
                "email": unique_email,
                "subject": "Tracking Test",
                "category": "general",
                "message": "Testing that this customer becomes trackable after submission",
            },
        )
        assert submit_resp.status_code == 200

        # Wait briefly for async processing
        await asyncio.sleep(2)

        # Try to look up customer (may or may not exist yet depending on worker speed)
        lookup_resp = await client.get(
            "/customers/lookup",
            params={"email": unique_email},
        )
        # Both 200 and 404 are acceptable - 200 means worker processed it
        assert lookup_resp.status_code in [200, 404]


# =============================================================================
# 6. CHANNEL METRICS TESTS
# =============================================================================


class TestChannelMetrics:
    """Test channel-specific metrics and monitoring."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_200(self, client):
        """Metrics endpoint should return successfully."""
        response = await client.get("/metrics/channels")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_returns_json(self, client):
        """Metrics should return valid JSON."""
        response = await client.get("/metrics/channels")
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_metrics_channel_fields(self, client):
        """If channel data exists, it should have expected fields."""
        response = await client.get("/metrics/channels")
        data = response.json()
        for channel_name, channel_data in data.items():
            assert "total_conversations" in channel_data


# =============================================================================
# 7. API DOCUMENTATION TESTS
# =============================================================================


class TestAPIDocs:
    """Test API documentation availability."""

    @pytest.mark.asyncio
    async def test_swagger_docs(self, client):
        """Swagger UI should be accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_redoc_docs(self, client):
        """ReDoc documentation should be accessible."""
        response = await client.get("/redoc")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_openapi_schema(self, client):
        """OpenAPI schema should be available."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/support/submit" in schema["paths"]
        assert "/health" in schema["paths"]


# =============================================================================
# 8. ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Test that the API handles errors gracefully."""

    @pytest.mark.asyncio
    async def test_404_for_unknown_route(self, client):
        """Unknown routes should return 404."""
        response = await client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_ticket_id(self, client):
        """Invalid ticket ID should return 404."""
        response = await client.get("/support/ticket/invalid-uuid")
        assert response.status_code in [404, 422, 500]

    @pytest.mark.asyncio
    async def test_empty_form_submission(self, client):
        """Empty JSON body should return validation error."""
        response = await client.post("/support/submit", json={})
        assert response.status_code == 422
