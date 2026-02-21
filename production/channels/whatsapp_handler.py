"""WhatsApp channel integration via Twilio for the Customer Success FTE."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import Request
from twilio.request_validator import RequestValidator
from twilio.rest import Client


class WhatsAppHandler:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.validator = RequestValidator(self.auth_token)
        else:
            self.client = None
            self.validator = None

    async def validate_webhook(self, request: Request) -> bool:
        """Validate incoming Twilio webhook signature."""
        if not self.validator:
            return False
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        form_data = await request.form()
        params = dict(form_data)
        return self.validator.validate(url, params, signature)

    async def process_webhook(self, form_data: dict) -> dict:
        """Process incoming WhatsApp message from Twilio webhook."""
        return {
            "channel": "whatsapp",
            "channel_message_id": form_data.get("MessageSid"),
            "customer_phone": form_data.get("From", "").replace("whatsapp:", ""),
            "content": form_data.get("Body", ""),
            "received_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "num_media": form_data.get("NumMedia", "0"),
                "profile_name": form_data.get("ProfileName"),
                "wa_id": form_data.get("WaId"),
                "status": form_data.get("SmsStatus"),
            },
        }

    async def send_message(self, to_phone: str, body: str) -> dict:
        """Send WhatsApp message via Twilio."""
        if not self.client:
            return {"channel_message_id": None, "delivery_status": "not_configured"}

        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        message = self.client.messages.create(
            body=body,
            from_=self.whatsapp_number,
            to=to_phone,
        )

        return {
            "channel_message_id": message.sid,
            "delivery_status": message.status,
        }

    def format_response(self, response: str, max_length: int = 1600) -> list[str]:
        """Format and split response for WhatsApp (max 1600 chars per message)."""
        if len(response) <= max_length:
            return [response]

        messages = []
        while response:
            if len(response) <= max_length:
                messages.append(response)
                break

            break_point = response.rfind(". ", 0, max_length)
            if break_point == -1:
                break_point = response.rfind(" ", 0, max_length)
            if break_point == -1:
                break_point = max_length

            messages.append(response[: break_point + 1].strip())
            response = response[break_point + 1 :].strip()

        return messages
