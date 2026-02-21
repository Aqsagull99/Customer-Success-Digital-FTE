# Deployment Guide - Customer Success FTE

## System Architecture

```
                    ┌──────────────────────────────────────────────────┐
                    │                 FastAPI (Port 8000)               │
                    │  /health  /support/*  /webhooks/*  /metrics/*     │
                    └────────┬──────────────┬──────────────┬───────────┘
                             │              │              │
                    ┌────────▼──┐  ┌────────▼──┐  ┌───────▼────┐
                    │  Web Form │  │   Gmail   │  │  WhatsApp  │
                    │  Handler  │  │  Handler  │  │  Handler   │
                    └────────┬──┘  └────────┬──┘  └───────┬────┘
                             │              │              │
                    ┌────────▼──────────────▼──────────────▼───────────┐
                    │              Apache Kafka (Port 9092)             │
                    │         fte.tickets.incoming (main topic)         │
                    └────────────────────┬────────────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────────────┐
                    │           Message Processor (Worker)             │
                    │      OpenAI Agents SDK + Customer Success Agent  │
                    └────────────────────┬────────────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────────────┐
                    │         PostgreSQL + pgvector (Port 5432)        │
                    │   customers │ conversations │ tickets │ messages │
                    └─────────────────────────────────────────────────┘
```

## Prerequisites

- Docker + Docker Compose
- ngrok (for Twilio/Gmail webhooks in local dev)
- Node.js 18+ (for React web form)
- API Keys:
  - OpenAI API key
  - Twilio account (WhatsApp sandbox)
  - Gmail API OAuth credentials (optional)

## Quick Start (Local Development)

### 1. Environment Setup
```bash
cd production
cp .env.example .env
# Edit .env with your actual keys:
#   OPENAI_API_KEY=sk-...
#   TWILIO_ACCOUNT_SID=AC...
#   TWILIO_AUTH_TOKEN=...
#   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 2. Start All Backend Services
```bash
docker-compose up --build -d
```

This starts:
| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database with pgvector extension |
| Kafka | 9092 | Event streaming (KRaft mode, no Zookeeper) |
| FastAPI API | 8000 | Channel endpoints + webhooks |
| Worker | - | Message processor (Kafka consumer + AI agent) |
| Metrics Collector | - | Background metrics aggregation |
| Prometheus | 9090 | Monitoring dashboard |

### 3. Verify Services
```bash
# Health check
curl http://localhost:8000/health

# Expected:
# {"status":"healthy","channels":{"email":"active","whatsapp":"active","web_form":"active"}}

# Check all containers
docker ps
```

### 4. Start React Web Form
```bash
cd web-form
npm install
npm run dev
# Opens at http://localhost:5173
```

### 5. Setup ngrok (for external webhooks)
```bash
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok-free.app)
```

### 6. Configure Twilio WhatsApp Webhook
1. Go to Twilio Console > Messaging > WhatsApp Sandbox
2. Set webhook URL: `https://<ngrok-url>/webhooks/whatsapp`
3. Set status callback: `https://<ngrok-url>/webhooks/whatsapp/status`

### 7. Configure Gmail Push Notifications
1. Create Google Cloud Pub/Sub topic
2. Set push subscription URL: `https://<ngrok-url>/webhooks/gmail`
3. Grant Gmail API publish permissions to the topic

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System health check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |
| POST | `/support/submit` | Web form submission |
| GET | `/support/ticket/{id}` | Ticket status lookup |
| POST | `/webhooks/gmail` | Gmail Pub/Sub webhook |
| POST | `/webhooks/whatsapp` | Twilio WhatsApp webhook |
| POST | `/webhooks/whatsapp/status` | WhatsApp delivery status |
| GET | `/conversations/{id}` | Conversation history |
| GET | `/customers/lookup?email=` | Customer lookup by email |
| GET | `/customers/lookup?phone=` | Customer lookup by phone |
| GET | `/metrics/channels` | Channel performance metrics |

## Testing

### Run E2E Tests (against live services)
```bash
cd production
LIVE_TEST=1 python -m pytest tests/test_multichannel_e2e.py -v
```

### Run E2E Tests (ASGI transport, no Docker needed)
```bash
cd production
python -m pytest tests/test_multichannel_e2e.py -v
```

### Run Load Test (headless)
```bash
cd production
bash tests/run_load_test.sh http://localhost:8000 20 5 2m
# Args: host, users, spawn_rate, duration
```

### Run Load Test (interactive UI)
```bash
cd production
locust -f tests/load_test.py --host=http://localhost:8000
# Open http://localhost:8089 for Locust UI
```

## Kubernetes Deployment

### 1. Create namespace and configs
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
```

### 2. Deploy services
```bash
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/deployment-worker.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### 3. Verify deployment
```bash
kubectl get pods -n customer-success-fte
kubectl logs -f deployment/fte-api -n customer-success-fte
```

### 4. Scaling
```bash
# Manual scaling
kubectl scale deployment/fte-message-processor -n customer-success-fte --replicas=5

# HPA auto-scales based on CPU (configured in hpa.yaml)
```

## Monitoring

- **Prometheus**: http://localhost:9090
- **Channel Metrics**: http://localhost:8000/metrics/channels
- **Alert Rules**: `monitoring/alert_rules.yml`

### Key Alerts
| Alert | Severity | Condition |
|-------|----------|-----------|
| HighResponseLatency | Warning | p95 > 3s for 2min |
| SlowAgentProcessing | Critical | >30s processing |
| HighEscalationRate | Warning | >30% for 10min |
| ChannelUnavailable | Critical | Channel down 2min |
| HighErrorRate | Critical | >5% 5xx errors |

## Database

### Schema Tables
| Table | Purpose |
|-------|---------|
| customers | Unified customer records across channels |
| customer_identifiers | Cross-channel identity matching |
| conversations | Conversation threads with sentiment tracking |
| messages | All messages with channel + direction tracking |
| tickets | Support ticket lifecycle management |
| knowledge_base | Product docs with vector embeddings (pgvector) |
| channel_configs | Per-channel configuration |
| agent_metrics | Performance metrics storage |

### Connect to Database
```bash
docker exec -it production-postgres-1 psql -U fte_user -d fte_db
```

## Kafka Topics

| Topic | Purpose |
|-------|---------|
| fte.tickets.incoming | All incoming tickets (main queue) |
| fte.channels.email.inbound | Email-specific inbound |
| fte.channels.whatsapp.inbound | WhatsApp-specific inbound |
| fte.channels.webform.inbound | Web form-specific inbound |
| fte.escalations | Escalated tickets |
| fte.metrics | Performance metrics events |
| fte.dlq | Dead letter queue for failed processing |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| PostgreSQL won't start | Check port 5432: `lsof -i :5432` |
| Kafka connection refused | Wait 30s after docker-compose up; Kafka needs time |
| Twilio webhook 403 | Verify ngrok URL matches Twilio console |
| Gmail webhook not firing | Re-run watch setup; Pub/Sub subscriptions expire every 7 days |
| Agent timeout | Check OpenAI API key and credits |
| Worker crashing | Check logs: `docker logs production-worker-1` |
| DB connection exhausted | Restart API: `docker-compose restart api` |

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```
