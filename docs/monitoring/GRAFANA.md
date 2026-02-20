# Grafana Configuration Guide

## 1. Data Source Setup
1. Add new Data Source: **Prometheus**
2. URL: `http://victoria_backend_prod:8000` (internal Docker network)
3. Save & Test.

## 2. Dashboard Panels

### A. System Health
- **CPU/Memory**: Use `process_cpu_seconds_total` and `process_resident_memory_bytes`.
- **Request Rate**: `rate(http_requests_total[5m])`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`

### B. Business Metrics (Victoria Custom)
- **Active Calls**: 
  - Query: `victoria_calls_total`
  - Visualization: Stat / Gauge
- **Call Duration Distribution**:
  - Query: `histogram_quantile(0.95, sum(rate(victoria_call_duration_seconds_bucket[5m])) by (le))`
  - Visualization: Time Series
- **Provider Latency (TTS/STT)**:
  - Query: `increase(victoria_tts_generation_seconds_sum[1h]) / increase(victoria_tts_generation_seconds_count[1h])`
  
## 3. Alerts
- **High Error Rate**: > 5% errors in 5min.
- **Provider Down**: Zero successful calls in 15min (during business hours).
