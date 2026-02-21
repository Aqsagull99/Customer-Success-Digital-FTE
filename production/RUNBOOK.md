# Incident Response Runbook - Customer Success FTE

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| P1 - Critical | All channels down, no messages processing | 5 min | Database crash, Kafka down |
| P2 - Major | One channel down or agent not responding | 15 min | Gmail webhook failing, high error rate |
| P3 - Minor | Degraded performance, non-critical issues | 1 hour | Slow responses, high latency |

## Incident Procedures

### 1. All Channels Down (P1)

**Symptoms**: Health check failing, no messages being processed

**Diagnosis**:
```bash
# Check all pods
kubectl get pods -n customer-success-fte

# Check API logs
kubectl logs deployment/fte-api -n customer-success-fte --tail=50

# Check database
kubectl exec -it deployment/fte-api -n customer-success-fte -- python -c "
import asyncio
from database.queries import get_db_pool
async def check(): pool = await get_db_pool(); print('DB OK')
asyncio.run(check())
"
```

**Resolution**:
1. Check PostgreSQL: `kubectl logs statefulset/postgres -n customer-success-fte`
2. Check Kafka: `kubectl logs statefulset/kafka -n customer-success-fte`
3. If DB is down: Restart postgres pod, wait for recovery
4. If Kafka is down: Restart kafka pod, consumers will auto-reconnect
5. If API is down: `kubectl rollout restart deployment/fte-api -n customer-success-fte`

### 2. WhatsApp Channel Down (P2)

**Symptoms**: WhatsApp messages not being received/sent

**Diagnosis**:
```bash
# Check webhook endpoint
curl -X POST https://<your-domain>/webhooks/whatsapp -d "test=1"

# Check Twilio status
# Visit: https://status.twilio.com/

# Check worker logs
kubectl logs deployment/fte-message-processor -n customer-success-fte --tail=50
```

**Resolution**:
1. Verify ngrok tunnel is active (if local dev)
2. Check Twilio console for webhook errors
3. Verify TWILIO_AUTH_TOKEN in secrets
4. Restart worker: `kubectl rollout restart deployment/fte-message-processor`

### 3. Gmail Channel Down (P2)

**Symptoms**: Email messages not being received

**Diagnosis**:
```bash
# Check Gmail watch status
# Pub/Sub subscriptions expire every 7 days

# Check webhook logs
kubectl logs deployment/fte-api -n customer-success-fte | grep gmail
```

**Resolution**:
1. Re-run Gmail watch setup (subscriptions expire every 7 days)
2. Check Google Cloud Pub/Sub for dead-lettered messages
3. Verify Gmail credentials haven't expired
4. Refresh OAuth token if needed

### 4. High Agent Latency (P3)

**Symptoms**: Agent processing > 10s, Prometheus alert firing

**Diagnosis**:
```bash
# Check OpenAI API status
curl https://status.openai.com/api/v2/status.json

# Check metrics
curl http://localhost:8000/metrics/channels

# Check Kafka consumer lag
kubectl exec kafka-0 -- kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group fte-message-processor
```

**Resolution**:
1. If OpenAI is slow: Wait for upstream recovery; consider rate limiting
2. If Kafka lag is high: Scale workers: `kubectl scale deployment/fte-message-processor --replicas=5`
3. If DB queries slow: Check `pg_stat_activity` for long-running queries
4. Temporary: Increase HPA max replicas

### 5. High Escalation Rate (P3)

**Symptoms**: >30% escalation rate for 10+ minutes

**Diagnosis**:
```bash
# Check recent escalations
curl http://localhost:8000/metrics/channels

# Check if specific category is spiking
# Query agent_metrics table for escalation reasons
```

**Resolution**:
1. Review escalation reasons in agent_metrics
2. If legitimate spike (e.g. outage): Expected behavior, inform human team
3. If false positives: Review and tune escalation rules in prompts.py
4. If sentiment model issue: Check recent messages for misclassification

### 6. Database Connection Failures (P1)

**Symptoms**: 500 errors on all endpoints, connection pool exhausted

**Resolution**:
1. Check PostgreSQL pod status and resource usage
2. Check connection count: `SELECT count(*) FROM pg_stat_activity;`
3. Kill idle connections if pool exhausted
4. Restart API pods to reset connection pools
5. If persistent: Increase `max_size` in `get_db_pool()`

## Escalation Contacts

| Role | Responsibility |
|------|---------------|
| On-call Engineer | First responder, P1/P2 incidents |
| Platform Team | Infrastructure issues (K8s, Kafka, PostgreSQL) |
| AI/ML Team | Agent behavior, prompt tuning, model issues |
| Channel Team | Twilio, Gmail API, webhook configuration |

## Post-Incident

After every P1/P2 incident:
1. Write incident report within 24 hours
2. Identify root cause
3. Create follow-up tickets for preventive measures
4. Update this runbook if new failure mode discovered
