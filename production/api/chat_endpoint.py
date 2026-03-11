"""Chat API endpoint for real-time AI responses."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    ai_response: str


# In-memory conversation store (replace with database in production)
conversations: dict[str, list[dict]] = {}


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(data: ChatMessage):
    """
    Send a message to the AI chat and get instant response.
    
    This endpoint:
    1. Receives user message
    2. Sends to Kafka for processing
    3. Waits for AI response (with timeout)
    4. Returns AI response to client
    """
    from kafka_client import get_kafka_producer, TOPICS
    
    conversation_id = data.conversation_id or f"chat_{datetime.now().timestamp()}"
    
    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    # Store user message
    user_message = {
        "role": "user",
        "content": data.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    conversations[conversation_id].append(user_message)
    
    # Prepare Kafka message
    kafka_message = {
        "channel": "web_chat",
        "channel_message_id": conversation_id,
        "customer_email": "chat@example.com",
        "customer_name": "Chat User",
        "subject": "Quick Chat",
        "content": data.message,
        "category": "general",
        "priority": "medium",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "conversation_id": conversation_id,
            "is_chat": True,
        },
    }
    
    # Publish to Kafka
    try:
        producer = await get_kafka_producer()
        await producer.publish(TOPICS["tickets_incoming"], kafka_message)
    except Exception as e:
        # If Kafka fails, generate local response
        pass
    
    # Wait for AI response (poll database)
    ai_response = await wait_for_ai_response(conversation_id, timeout=10)
    
    if not ai_response:
        # Fallback: Generate simple response
        ai_response = generate_fallback_response(data.message)
    
    # Store AI response
    ai_message = {
        "role": "agent",
        "content": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    conversations[conversation_id].append(ai_message)
    
    return ChatResponse(
        conversation_id=conversation_id,
        message=data.message,
        ai_response=ai_response,
    )


@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """Get chat conversation history."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id],
    }


async def wait_for_ai_response(conversation_id: str, timeout: int = 10) -> str | None:
    """
    Wait for AI response from worker.
    Poll database every 1 second for new messages.
    """
    from database.queries import get_conversation_messages
    
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        try:
            messages = await get_conversation_messages(conversation_id)
            
            # Look for agent message
            for msg in messages:
                if msg.get("role") == "agent":
                    return msg.get("content")
        except Exception:
            pass
        
        await asyncio.sleep(1)
    
    return None


def generate_fallback_response(message: str) -> str:
    """Generate a simple fallback response when AI is unavailable."""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        return "Hello! 👋 How can I assist you today?"
    
    if "help" in message_lower:
        return "I'm here to help! Please tell me more about your issue and I'll do my best to assist you."
    
    if any(word in message_lower for word in ["billing", "payment", "invoice"]):
        return "I understand you have a billing question. Could you please provide more details about your concern? I can help with invoices, refunds, or payment issues."
    
    if any(word in message_lower for word in ["technical", "bug", "error", "not working"]):
        return "I'm sorry to hear you're experiencing technical difficulties. Let me help you troubleshoot. Can you describe what's happening?"
    
    if "thank" in message_lower:
        return "You're welcome! Is there anything else I can help you with?"
    
    return "Thank you for reaching out! I've received your message and I'm here to help. Could you provide more details about your issue so I can assist you better?"
