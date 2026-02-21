"""Web support form handler for the Customer Success FTE."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

router = APIRouter(prefix="/support", tags=["support-form"])


class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""

    name: str
    email: EmailStr
    subject: str
    category: str  # 'general', 'technical', 'billing', 'feedback', 'bug_report'
    message: str
    priority: Optional[str] = "medium"
    attachments: Optional[list[str]] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

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
    ticket_id = str(uuid.uuid4())

    message_data = {
        "channel": "web_form",
        "channel_message_id": ticket_id,
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "content": submission.message,
        "category": submission.category,
        "priority": submission.priority,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "form_version": "1.0",
            "attachments": submission.attachments or [],
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
