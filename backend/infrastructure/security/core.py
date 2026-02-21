from fastapi import Security, HTTPException, Depends, Request
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.infrastructure.config.settings import settings

# 1. Rate Limiting
limiter = Limiter(key_func=get_remote_address)

# 2. Authentication — X-API-Key header only (no query string: would expose key in logs/URLs)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    """
    Validate API Key from X-API-Key header.
    Used as a FastAPI dependency in all protected routes.
    """
    expected_key = getattr(settings, "VICTORIA_API_KEY", "dev-secret-key")

    if api_key_header == expected_key:
        return api_key_header

    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )

def setup_security(app):
    """
    Apply security middleware to app.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
