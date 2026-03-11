"""Web support form handler for the Customer Success FTE."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

router = APIRouter(prefix="/support", tags=["support-form"])


class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    subject: Optional[str] = None
    category: str  # 'general', 'technical', 'billing', 'feedback', 'bug_report'
    message: str
    priority: Optional[str] = "medium"
    channel: str = "web"
    attachment: Optional[str] = None
    attachments: list[str] = Field(default_factory=list)

    @staticmethod
    def _is_allowed_attachment(url: str) -> bool:
        allowed_domains = {
            "drive.google.com",
            "docs.google.com",
            "dropbox.com",
            "onedrive.live.com",
            "1drv.ms",
            "box.com",
        }
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        hostname = parsed.netloc.lower().split(":")[0]
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname in allowed_domains or any(
            hostname.endswith(f".{domain}") for domain in allowed_domains
        )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("channel")
    @classmethod
    def channel_must_be_valid(cls, v: str) -> str:
        valid_channels = ["web", "email", "whatsapp"]
        if v not in valid_channels:
            raise ValueError(f"Channel must be one of: {valid_channels}")
        return v

    @field_validator("email")
    @classmethod
    def email_must_be_present_for_email_channels(
        cls, v: Optional[EmailStr], info: ValidationInfo
    ) -> Optional[EmailStr]:
        channel = (info.data or {}).get("channel", "web")
        # Only require email for web and email channels, not whatsapp
        if channel in {"web", "email"} and not v:
            raise ValueError("Email is required for web or email support")
        return v

    @field_validator("subject")
    @classmethod
    def subject_must_be_present_for_email_channels(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        channel = (info.data or {}).get("channel", "web")
        # Only require subject for web and email channels, not whatsapp
        if channel in {"web", "email"} and (not v or len(v.strip()) < 5):
            raise ValueError("Subject must be at least 5 characters")
        return v.strip() if v else v

    @field_validator("phone")
    @classmethod
    def phone_required_for_whatsapp(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        channel = (info.data or {}).get("channel", "web")
        if channel == "whatsapp" and (not v or len(v.strip()) < 7):
            raise ValueError("WhatsApp number must be at least 7 characters")
        return v.strip() if v else v

    @field_validator("message")
    @classmethod
    def message_must_have_content(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v.strip()

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v: str) -> str:
        valid_categories = ["general", "technical", "billing", "feedback", "bug_report"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v

    @field_validator("attachment")
    @classmethod
    def attachment_must_be_allowlisted(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if not cls._is_allowed_attachment(v):
            raise ValueError("Attachment link must be from an approved provider")
        return v

    @field_validator("attachments")
    @classmethod
    def attachments_must_be_allowlisted(cls, v: list[str]) -> list[str]:
        for link in v:
            if not cls._is_allowed_attachment(link):
                raise ValueError("Attachment links must be from approved providers")
        return v


class SupportFormResponse(BaseModel):
    """Response model for form submission."""

    ticket_id: str
    message: str
    estimated_response_time: str


@router.post("/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission):
    """
    Handle support form submission.

    This endpoint:
    1. Validates the submission
    2. Creates a ticket in the system
    3. Publishes to Kafka for agent processing
    4. Returns confirmation to user
    """
    # Debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug(f"Received submission: channel={submission.channel}, email={submission.email}, phone={submission.phone}")
    
    ticket_id = str(uuid.uuid4())

    # Map channel to internal channel name
    channel_map = {
        "web": "web_form",
        "email": "email",
        "whatsapp": "whatsapp",
    }
    internal_channel = channel_map.get(submission.channel, "web_form")

    message_data = {
        "channel": internal_channel,
        "channel_message_id": ticket_id,
        "customer_email": submission.email,
        "customer_name": submission.name,
        "customer_phone": submission.phone,
        "subject": submission.subject,
        "content": submission.message,
        "category": submission.category,
        "priority": submission.priority,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "form_version": "1.0",
            "attachments": [
                *([submission.attachment] if submission.attachment else []),
                *submission.attachments,
            ],
            "channel_selected": submission.channel,
        },
    }

    # Publish to Kafka
    from kafka_client import get_kafka_producer, TOPICS

    producer = await get_kafka_producer()
    await producer.publish(TOPICS["tickets_incoming"], message_data)

    return SupportFormResponse(
        ticket_id=ticket_id,
        message="Thank you for contacting us! Our AI assistant will respond shortly.",
        estimated_response_time="Usually within 5 minutes",
    )


@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    from database.queries import get_ticket_by_id

    ticket = await get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_id": ticket_id,
        "status": ticket["status"],
        "created_at": str(ticket["created_at"]),
    }
