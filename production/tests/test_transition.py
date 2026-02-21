"""
Transition Tests: Verify agent behavior matches incubation discoveries.
Run these BEFORE deploying to production.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app

BASE_URL = "http://test"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


class TestTransitionFromIncubation:
    """Tests based on edge cases discovered during incubation."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Health check should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "channels" in data

    @pytest.mark.asyncio
    async def test_web_form_submission_validation(self, client):
        """Web form should validate required fields."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "A",  # Too short
                "email": "invalid-email",
                "subject": "Hi",
                "category": "invalid",
                "message": "Short",  # Too short
            },
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_web_form_valid_submission(self, client):
        """Valid web form submission should return ticket ID."""
        response = await client.post(
            "/support/submit",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Help with API",
                "category": "technical",
                "message": "I need help with the API authentication flow",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert data["message"] is not None

    @pytest.mark.asyncio
    async def test_customer_lookup_requires_params(self, client):
        """Customer lookup should require email or phone."""
        response = await client.get("/customers/lookup")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_conversation_not_found(self, client):
        """Non-existent conversation should return 404."""
        response = await client.get("/conversations/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_channel_metrics_endpoint(self, client):
        """Channel metrics endpoint should return without error."""
        response = await client.get("/metrics/channels")
        assert response.status_code == 200


class TestChannelResponseFormatting:
    """Verify channel-specific formatting from incubation templates."""

    def test_email_format(self):
        from agent.formatters import Channel, format_for_channel

        result = format_for_channel("Your password has been reset.", Channel.EMAIL, "TK-001")
        assert "Dear Customer" in result
        assert "Best regards" in result
        assert "TK-001" in result

    def test_whatsapp_format_truncation(self):
        from agent.formatters import Channel, format_for_channel

        long_msg = "x" * 500
        result = format_for_channel(long_msg, Channel.WHATSAPP)
        assert len(result.split("\n\n")[0]) <= 300

    def test_web_format(self):
        from agent.formatters import Channel, format_for_channel

        result = format_for_channel("Issue resolved.", Channel.WEB_FORM, "TK-002")
        assert "TK-002" in result
        assert "support portal" in result
