"""
DTMF Registry — Infrastructure Singleton.

Thread-safe registry that maps call_session_id → active CallOrchestrator.
Enables telephony.py (HTTP webhook layer) to send DTMF signals into
the correct WebSocket session managed by telnyx_stream.py.

Architecture: Bridge between HTTP layer (webhook events) and WS layer (audio pipeline).

Usage:
    # In telnyx_stream.py (WebSocket lifecycle):
    DtmfRegistry.register(session_id, orchestrator)  # on connect
    DtmfRegistry.unregister(session_id)               # on disconnect/finally

    # In telephony.py _handle_dtmf():
    orch = DtmfRegistry.get(session_id)
    if orch:
        await orch.handle_dtmf(digit)

Sprint 4 — B-09: DTMF → Pipeline de Decisión
Reference: sprint4_reference.md §B-09
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from backend.application.services.call_orchestrator import CallOrchestrator

logger = logging.getLogger(__name__)


class DtmfRegistry:
    """
    In-process registry of active CallOrchestrator instances keyed by call_session_id.

    Single-server safe. For multi-server deployments, replace with Redis pub/sub.
    """

    # Class-level state (process-wide singleton)
    _lock: asyncio.Lock = asyncio.Lock()
    _instances: dict[str, "CallOrchestrator"] = {}

    @classmethod
    async def register(cls, session_id: str, orchestrator: "CallOrchestrator") -> None:
        """Register an orchestrator for a session. Safe to call multiple times."""
        async with cls._lock:
            cls._instances[session_id] = orchestrator
        logger.debug(f"[DtmfRegistry] Registered session: {session_id} (total: {len(cls._instances)})")

    @classmethod
    async def unregister(cls, session_id: str) -> None:
        """Remove an orchestrator when the WebSocket session ends."""
        async with cls._lock:
            removed = cls._instances.pop(session_id, None)
        if removed:
            logger.debug(f"[DtmfRegistry] Unregistered session: {session_id}")

    @classmethod
    def get(cls, session_id: str) -> Optional["CallOrchestrator"]:
        """
        Retrieve orchestrator by session_id. Returns None if not found.
        Non-blocking — safe to call from async handlers.
        """
        return cls._instances.get(session_id)

    @classmethod
    def count(cls) -> int:
        """Return number of active sessions. For monitoring/testing."""
        return len(cls._instances)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registrations. For testing only.
        NOT safe to call in production during active calls.
        """
        cls._instances.clear()
