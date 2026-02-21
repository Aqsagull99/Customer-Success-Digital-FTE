# Web Support Form - Integration Guide

## Overview

The Web Support Form is a React component that provides customers with a self-service support interface. It connects to the FastAPI backend to create tickets, which are processed by the AI agent.

## Architecture

```
User Browser          FastAPI Backend          Kafka          AI Agent
    |                      |                    |                |
    |-- POST /support/submit -->               |                |
    |                      |-- publish event -->|                |
    |<-- ticket_id + msg --|                    |                |
    |                      |                    |-- consume -->  |
    |                      |                    |   process      |
    |-- GET /support/ticket/{id} -->            |                |
    |<-- status + history --|                    |                |
```

## Quick Start

### 1. Start Backend Services
```bash
cd production
docker-compose up -d
```

### 2. Start React Dev Server
```bash
cd production/web-form
npm install
npm run dev
# Opens at http://localhost:5173
```

### 3. Build for Production
```bash
cd production/web-form
npm run build
# Output in dist/ - serve with any static file server
```

## API Endpoints

### Submit Support Form

**POST** `/support/submit`

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Help with API",
  "category": "technical",
  "message": "I need help with the API authentication process"
}
```

**Response:**
```json
{
  "ticket_id": "uuid-string",
  "message": "Thank you for contacting us! Our AI assistant will respond shortly.",
  "estimated_response_time": "Usually within 5 minutes"
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| name | Min 2 characters |
| email | Valid email format |
| subject | Required |
| category | One of: general, technical, billing, feedback, bug_report |
| message | Min 10 characters |

**Error Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "Message must be at least 10 characters",
      "type": "value_error"
    }
  ]
}
```

### Check Ticket Status

**GET** `/support/ticket/{ticket_id}`

**Response:**
```json
{
  "ticket_id": "uuid-string",
  "status": "open",
  "created_at": "2026-02-21T08:00:00+00:00"
}
```

**Statuses:** `open` -> `processing` -> `resolved` | `escalated`

## Embedding the Form

### Option 1: iframe Embed
```html
<iframe
  src="http://your-domain:5173"
  width="100%"
  height="600px"
  frameborder="0">
</iframe>
```

### Option 2: Direct API Integration
Any frontend can call the API directly:
```javascript
const response = await fetch('http://localhost:8000/support/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Customer Name',
    email: 'customer@email.com',
    subject: 'Support Request',
    category: 'technical',
    message: 'Detailed description of the issue...'
  })
});

const { ticket_id, message } = await response.json();
```

## CORS Configuration

The backend allows all origins by default. For production, update `api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Categories

| Category | Description | AI Handling |
|----------|-------------|-------------|
| general | General inquiries | AI responds from knowledge base |
| technical | Technical/API issues | AI searches docs, may escalate |
| billing | Billing questions | Immediate escalation to human |
| feedback | Product feedback | AI acknowledges, logs for review |
| bug_report | Bug reports | AI creates P2 ticket, escalates if critical |
