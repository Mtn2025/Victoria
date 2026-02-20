# Secrets Management Strategy

## 1. Development (Local)
- **Tool**: `.env` files managed manually or via `scripts/check_env.py`.
- **Location**: `config/environments/.env.local`.
- **Policy**: NEVER commit `.env.local` or any file containing real API keys.
- **Template**: Use `config/environments/.env.example` for structure.

## 2. Staging/Production (e.g., Coolify, Render, AWS)
- **Tool**: Platform-native Variable Injection (e.g., Coolify Environment Variables Tab).
- **Injection**: Environment variables injected at container runtime and build time (for Frontend).
- **Note on Coolify**: Coolify will auto-generate variables like `SERVICE_URL_FRONTEND` or `SERVICE_FQDN_BACKEND`. **DO NOT modify or delete these.** You must add Victoria's own required variables alongside them.

## 3. Implementation Details
- **Backend**: Uses `pydantic-settings` to read from System Environment (`OS ENV`). If a variable like `GROQ_API_KEY` is set in Coolify, it reads it directly.
- **Frontend**: Uses `VITE_*` prefix. **CRITICAL:** Variables like `VITE_API_URL` and `VITE_WS_URL` must be injected *at build time*. If you are deploying via Coolify, ensure these are added to the Frontend service's Environment Variables tab *before* triggering the deployment, pointing to the Backend's public URL.

## 4. Forbidden Practices
- ❌ Hardcoding API keys in code.
- ❌ Committing `.env` files.
- ❌ Logging full API responses that might contain keys.
