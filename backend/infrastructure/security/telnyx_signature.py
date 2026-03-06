"""
Telnyx Webhook Signature Verifier.
Part of the Infrastructure Layer (Security).

Verifies the Ed25519 signature sent by Telnyx on every webhook call.
Reference: telnyx_call_architecture.md §6 — Regla #2: Verificar firma Ed25519

Headers verified:
  - telnyx-signature-ed25519  (base64-encoded Ed25519 signature)
  - telnyx-timestamp          (Unix epoch seconds — tolerance: 5 min)

Bypass: In ENVIRONMENT=development the verification always returns True
to avoid blocking local development without a real Telnyx public key.
"""
import base64
import logging
import time
from typing import Optional

from fastapi import Request

logger = logging.getLogger(__name__)

# Maximum allowed difference between webhook timestamp and current time (seconds)
_TIMESTAMP_TOLERANCE_SECS = 300  # 5 minutes


async def verify_telnyx_signature(request: Request, body: bytes) -> bool:
    """
    Verify the Ed25519 signature of an incoming Telnyx webhook.

    Args:
        request: The FastAPI Request object (contains headers).
        body:    The raw HTTP body bytes (must NOT be re-read after this).

    Returns:
        True  — signature valid (or dev bypass active).
        False — invalid signature or missing configuration.
    """
    from backend.infrastructure.config.settings import settings

    # ── Development bypass ───────────────────────────────────────────────────
    if settings.ENVIRONMENT == "development":
        logger.debug("🔓 [TelnyxSig] Dev bypass — signature check skipped")
        return True

    # ── Read required config ─────────────────────────────────────────────────
    pub_key_b64: Optional[str] = settings.TELNYX_PUBLIC_KEY
    if not pub_key_b64:
        logger.error(
            "❌ [TelnyxSig] TELNYX_PUBLIC_KEY not set — cannot verify signature. "
            "Rejecting request."
        )
        return False

    # ── Read headers ─────────────────────────────────────────────────────────
    signature_b64: str = request.headers.get("telnyx-signature-ed25519", "")
    timestamp_str: str = request.headers.get("telnyx-timestamp", "")

    if not signature_b64 or not timestamp_str:
        logger.warning(
            "❌ [TelnyxSig] Missing telnyx-signature-ed25519 or telnyx-timestamp headers"
        )
        return False

    # ── Timestamp tolerance check ─────────────────────────────────────────────
    try:
        ts = int(timestamp_str)
        drift = abs(time.time() - ts)
        if drift > _TIMESTAMP_TOLERANCE_SECS:
            logger.warning(
                f"❌ [TelnyxSig] Timestamp too old/ahead: drift={drift:.0f}s "
                f"(max={_TIMESTAMP_TOLERANCE_SECS}s)"
            )
            return False
    except (ValueError, TypeError):
        logger.warning(f"❌ [TelnyxSig] Invalid timestamp: {timestamp_str!r}")
        return False

    # ── Ed25519 verification ──────────────────────────────────────────────────
    # The signed payload is: "{timestamp}|{body}" as bytes
    signed_payload = f"{timestamp_str}|".encode() + body

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature

        pub_key_bytes = base64.b64decode(pub_key_b64)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_key_bytes)
        sig_bytes = base64.b64decode(signature_b64)
        pub_key.verify(sig_bytes, signed_payload)

        logger.debug("✅ [TelnyxSig] Signature verified successfully")
        return True

    except InvalidSignature:
        logger.warning("❌ [TelnyxSig] Signature mismatch — possible spoofing attempt")
        return False
    except Exception as exc:
        logger.error(f"❌ [TelnyxSig] Unexpected verification error: {exc}")
        return False
