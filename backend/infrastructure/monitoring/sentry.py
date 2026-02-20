import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging

from backend.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

def init_sentry():
    """
    Initialize Sentry SDK if DSN is provided.
    """
    dsn = getattr(settings, "SENTRY_DSN", None)
    
    if dsn:
        logger.info("Initializing Sentry Error Tracking...")
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            environment=settings.ENVIRONMENT,
            traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
        )
    else:
        logger.warning("SENTRY_DSN not found. Error tracking disabled.")
