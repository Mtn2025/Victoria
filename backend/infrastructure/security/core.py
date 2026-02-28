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

import logging

logger = logging.getLogger(__name__)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    """
    Validate API Key from X-API-Key header.
    Used as a FastAPI dependency in all protected routes.
    """
    # Fix getattr replacing the default with None when the variable is explicitly None
    expected_key = getattr(settings, "VICTORIA_API_KEY", None)
    if not expected_key:
        expected_key = "dev-secret-key"
        
    # Strip spaces and QUOTES to ensure exact match even if Docker/Coolify injects literal quotes
    api_key_header = api_key_header.strip() if api_key_header else ""
    expected_key = expected_key.strip().strip("'").strip('"')
    
    # Check if the header matches
    if api_key_header == expected_key:
        return api_key_header

    # Log the mismatch securely (masking part of the received key)
    masked_received = api_key_header[:3] + "***" if len(api_key_header) > 3 else "***"
    logger.warning(
        f"Auth Failed: Header X-API-Key '{masked_received}' did not match environment expected_key."
    )

    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )

def setup_security(app):
    """
    Apply security middleware to app.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
