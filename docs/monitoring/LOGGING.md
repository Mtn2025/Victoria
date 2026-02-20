# Logging Strategy

## 1. Structured Logging
The backend is configured to emit logs in JSON format. This allows log aggregation systems to parse fields automatically.

```json
{
  "timestamp": "2023-10-27T10:00:00.123456",
  "level": "INFO",
  "message": "Processing call",
  "module": "call_orchestrator",
  "correlation_id": "123-abc"
}
```

## 2. Aggregation (Recommendation)
For production, we recommend deploying the **PLG Stack** (Promtail, Loki, Grafana) or **ELK Stack**.

### Docker Compose Setup (Example)
Add Promtail to `docker-compose.prod.yml` to scrape container logs and push to Loki.

## 3. Policy
- **PII**: Never log full transcripts or PII in `INFO` level.
- **Retention**: Keep logs for 30 days hot storage.
