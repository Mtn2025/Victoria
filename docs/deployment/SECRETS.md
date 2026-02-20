# Secrets Management Strategy

## 1. Development (Local)
- **Tool**: `.env` files managed manually or via `scripts/check_env.py`.
- **Location**: `config/environments/.env.local`.
- **Policy**: NEVER commit `.env.local` or any file containing real API keys.
- **Template**: Use `config/environments/.env.example` for structure.

## 2. Staging/Production
- **Tool**: Platform-native Variable Injection (e.g., Coolify, Docker Secrets, AWS SSM).
- **Injection**: Environment variables injected at container runtime.
- **CI/CD**: GitHub Actions Secrets for build-time args (if needed).

## 3. Implementation Details
- **Backend**: Uses `pydantic-settings` to read from `OS ENV` first, then fallback to `.env` file if specific `ENVIRONMENT` is set.
- **Frontend**: Uses `VITE_*` prefix. Secrets must be injected at build time (or runtime via config endpoint if using strict separation).

## 4. Forbidden Practices
- ❌ Hardcoding API keys in code.
- ❌ Committing `.env` files.
- ❌ Logging full API responses that might contain keys.
