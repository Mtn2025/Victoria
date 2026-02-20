# Distributed Tracing

## 1. Strategy
We use **OpenTelemetry** standards. Currently, minimal tracing is provided via **Sentry Performance Monitoring**.

## 2. Implementation
- **Correlation IDs**: Each HTTP request generates a `X-Request-ID` which is propagated to downstream services (DB, External APIs).
- **Sentry**: Captures transaction traces for endpoint latency analysis.

## 3. Future Expansion (OpenTelemetry Collector)
To move to a vendor-neutral tracing solution:
1. Install `opentelemetry-instrumentation-fastapi`.
2. Configure OTLP Exporter to send traces to Jaeger or Tempo.
