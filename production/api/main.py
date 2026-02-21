"""FastAPI application for the Customer Success FTE."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from channels.web_form_handler import router as web_form_router
from database.queries import close_db_pool, get_channel_metrics
from kafka_client import TOPICS, get_kafka_producer

app = FastAPI(
    title="Customer Success FTE API",
    description="24/7 AI-powered customer support across Email, WhatsApp, and Web",
    version="2.0.0",
)

# CORS for web form
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include web form router
app.include_router(web_form_router)

# Initialize handlers
gmail_handler = GmailHandler()
whatsapp_handler = WhatsAppHandler()


@app.on_event("startup")
async def startup():
    await get_kafka_producer()


@app.on_event("shutdown")
async def shutdown():
    from kafka_client import _producer

    if _producer:
        await _producer.stop()
    await close_db_pool()


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channels": {
            "email": "active",
            "whatsapp": "active",
            "web_form": "active",
        },
    }


# Gmail webhook endpoint
@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Gmail push notifications via Pub/Sub."""
    try:
        body = await request.json()
        messages = await gmail_handler.process_notification(body)

        producer = await get_kafka_producer()
        for message in messages:
            background_tasks.add_task(
                producer.publish,
                TOPICS["tickets_incoming"],
                message,
            )

        return {"status": "processed", "count": len(messages)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WhatsApp webhook endpoint (Twilio)
@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp messages via Twilio webhook."""
    if not await whatsapp_handler.validate_webhook(request):
        raise HTTPException(status_code=403, detail="Invalid signature")

    form_data = await request.form()
    message = await whatsapp_handler.process_webhook(dict(form_data))

    producer = await get_kafka_producer()
    background_tasks.add_task(
        producer.publish,
        TOPICS["tickets_incoming"],
        message,
    )

    # Return TwiML response (empty = no immediate reply, agent will respond)
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


# WhatsApp status callback
@app.post("/webhooks/whatsapp/status")
async def whatsapp_status_webhook(request: Request):
    """Handle WhatsApp message status updates (delivered, read, etc.)."""
    form_data = await request.form()
    # Log status update
    return {"status": "received"}


# Conversation history endpoint
@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get full conversation history with cross-channel context."""
    from database.queries import load_conversation_messages

    history = await load_conversation_messages(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": history}


# Customer lookup endpoint
@app.get("/customers/lookup")
async def lookup_customer(email: str = None, phone: str = None):
    """Look up customer by email or phone across all channels."""
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Provide email or phone")

    from database.queries import find_customer_by_email, find_customer_by_phone

    customer = None
    if email:
        customer = await find_customer_by_email(email)
    if not customer and phone:
        customer = await find_customer_by_phone(phone)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return dict(customer)


# Channel metrics endpoint
@app.get("/metrics/channels")
async def get_metrics():
    """Get performance metrics by channel."""
    metrics = await get_channel_metrics()
    return {row["channel"]: row for row in metrics}
