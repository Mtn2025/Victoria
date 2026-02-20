# Production Deployment Checklist

## 1. Pre-Deployment (Environment Variables)
- [ ] Configure the following secrets in your deployment platform (e.g., Coolify, Render, AWS):
    - **Database & Services**: 
      - `DATABASE_URL` (Pointer to Production PostgreSQL/SQLite volume).
      - `REDIS_URL` (For Caching and Pub/Sub).
    - **Backend API Keys**:
      - `GROQ_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `TELNYX_API_KEY`.
    - **Frontend Connection to Backend (CRITICAL)**:
      - `VITE_API_URL` (Must point exactly to your backend public URL, e.g., `https://api.tudominio.com/api` or `http://<coolify-backend-domain>/api`)
      - `VITE_WS_URL` (For WebSockets, e.g., `wss://api.tudominio.com/ws` or `ws://<coolify-backend-domain>/ws`)
    - **Security**:
      - `VICTORIA_API_KEY` (Strong randomized key for Frontend-Backend handshake).
- [ ] Ensure `SENTRY_DSN` is correctly configured for error tracking.
- [ ] Validate Docker images build successfully (`cd-production.yml`).

## 2. Infrastructure Checks
- [ ] Validate Domain configs (SSL Certificates issued/active).
- [ ] Configure Ingress/Nginx rules for WebSocket connections (`/ws/media-stream`).
  - Required Nginx settings: `proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`
- [ ] Ensure Persistent Volumes are correctly mapped for databases and logs if not using external managed services.
- [ ] Ensure Prometheus Metrics are reachable internally to the Grafana instance but NOT exposed to the public internet (`/metrics`).

## 3. Deployment Execution
- [ ] Trigger `.github/workflows/cd-production.yml` manually or via Release Tag.
- [ ] Check deployment logs for startup errors (container restarts).

## 4. Post-Deployment Verification (Smoke Tests)
- [ ] Run Liveness Probe: `curl https://<api-domain>/health/live` -> Expect `{"status": "ok"}`
- [ ] Run Readiness Probe: `curl https://<api-domain>/health/ready` -> Expect `{"status": "ready"}`
- [ ] Access frontend URL (`https://<app-domain>`) and check for console errors.
- [ ] Retrieve system features via API: `curl -H "X-API-Key: <key>" https://<api-domain>/api/config/features`

## 5. Rollback Plan
- [ ] Refer to `docs/deployment/ROLLBACK.md` in case of critical failure.
