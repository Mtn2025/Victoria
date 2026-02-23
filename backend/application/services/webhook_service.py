import logging
import json
import hmac
import hashlib
import httpx
from typing import Optional

from backend.domain.ports.config_repository_port import ConfigDTO
from backend.domain.value_objects.extraction_schema import ExtractionResult

logger = logging.getLogger(__name__)

class WebhookService:
    """
    Service for sending post-call extraction data to external CRMs via Webhook.
    """

    def __init__(self, config: ConfigDTO):
        """
        Initialize the webhook service with agent configuration.
        """
        self.config = config

    async def dispatch_post_call(self, result: ExtractionResult, call_id: str) -> bool:
        """
        Dispatch the extraction result to the configured Webhook URL.
        Signs the payload with HMAC-SHA256 if a secret is provided.
        
        Args:
            result: ExtractionResult containing raw_data and metrics
            call_id: Identifier for the call
            
        Returns:
            bool: True if dispatched successfully or skipped, False on error.
        """
        webhook_url = getattr(self.config, 'webhook_url', None)
        if not webhook_url:
            logger.info(f"⏩ [WEBHOOK] Skiping webhook for call {call_id}: No URL configured.")
            return True

        # Build Data Payload
        payload = {
            "call_id": call_id,
            "agent_id": getattr(self.config, 'name', 'unknown'),
            "summary": result.summary,
            "is_success": result.is_success,
            "sentiment_score": result.sentiment_score,
            "extracted_data": result.raw_data
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Victoria-AI-Webhook/1.0"
        }

        # Apply HMAC SHA-256 Signature if secret exists
        webhook_secret = getattr(self.config, 'webhook_secret', None)
        if webhook_secret:
            signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers["X-Victoria-Signature"] = f"sha256={signature}"

        logger.info(f"🚀 [WEBHOOK] Dispatching post-call data to {webhook_url} for call {call_id}")

        try:
            # Short timeout to avoid blocking processes
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    content=payload_bytes,
                    headers=headers
                )
                
                if response.status_code >= 400:
                    logger.error(f"❌ [WEBHOOK] Failed with status {response.status_code}: {response.text}")
                    return False
                    
                logger.info(f"✅ [WEBHOOK] Successfully delivered to {webhook_url}")
                return True
                
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Transport error: {str(e)}")
            return False
