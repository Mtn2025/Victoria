"""
Control Channel - Signal bus for control commands in conversation pipeline.

Application Service: Coordinates control flow independently from data flow.
Enables immediate response to interrupts, cancellations, and emergency stops.
"""
import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ControlSignal(Enum):
    """
    Control signal types for pipeline management.
    
    Signals:
        INTERRUPT: User interrupted assistant (barge-in)
        CANCEL: Cancel current operation
        CLEAR_PIPELINE: Clear all pending output frames
        EMERGENCY_STOP: Force shutdown
        PAUSE: Pause processing
        RESUME: Resume processing
    """
    INTERRUPT = "interrupt"
    CANCEL = "cancel"
    CLEAR_PIPELINE = "clear_pipeline"
    EMERGENCY_STOP = "emergency_stop"
    PAUSE = "pause"
    RESUME = "resume"


@dataclass
class ControlMessage:
    """
    Control message with signal type and metadata.
    
    Attributes:
        signal: Type of control signal
        metadata: Additional context (e.g., interruption reason, error details)
    """
    signal: ControlSignal
    metadata: Dict[str, Any]


class ControlChannel:
    """
    Async signal queue for control commands.
    
    Responsibilities:
    - Send control signals from any component
    - Wait for signals in control loop (non-blocking)
    - Prioritize control flow over data flow
    - Enable immediate interrupt handling
    
    Pattern: Producer-Consumer with AsyncIO queue
    - Producers: Processors, Orchestrator, External events
    - Consumer: Control loop in orchestrator
    
    Example:
        >>> channel = ControlChannel()
        >>> 
        >>> # Producer (in processor)
        >>> await channel.send_signal(
        ...     ControlSignal.INTERRUPT,
        ...     metadata={'text': 'user spoke'}
        ... )
        >>> 
        >>> # Consumer (in orchestrator control loop)
        >>> while active:
        ...     msg = await channel.wait_for_signal(timeout=1.0)
        ...     if msg and msg.signal == ControlSignal.INTERRUPT:
        ...         await handle_interruption()
    """
    
    def __init__(self, maxsize: int = 100):
        """
        Initialize control channel.
        
        Args:
            maxsize: Maximum queue size (default: 100)
        """
        self._queue: asyncio.Queue[ControlMessage] = asyncio.Queue(maxsize=maxsize)
        self._active = True
        logger.info("🎛️ ControlChannel initialized")
    
    async def send_signal(
        self,
        signal: ControlSignal,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send control signal to channel.
        
        Args:
            signal: Type of control signal
            metadata: Additional context
        """
        if not self._active:
            logger.warning(f"⚠️ Control channel inactive, signal dropped: {signal.value}")
            return
        
        msg = ControlMessage(
            signal=signal,
            metadata=metadata or {}
        )
        
        try:
            # Non-blocking put (fail if queue full)
            self._queue.put_nowait(msg)
            logger.debug(f"📤 Signal sent: {signal.value} (metadata: {metadata})")
        except asyncio.QueueFull:
            logger.error(f"❌ Control queue full, signal dropped: {signal.value}")
    
    async def wait_for_signal(self, timeout: float = 1.0) -> Optional[ControlMessage]:
        """
        Wait for control signal (non-blocking with timeout).
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            ControlMessage if received, None if timeout
            
        Raises:
            TimeoutError: If timeout reached (for explicit handling)
        """
        if not self._active:
            return None
        
        try:
            msg = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            logger.debug(f"📥 Signal received: {msg.signal.value}")
            return msg
        except asyncio.TimeoutError:
            # Normal timeout, no signal received
            return None
    
    async def clear(self) -> None:
        """
        Clear all pending signals.
        
        Use when resetting pipeline or ignoring old signals.
        """
        count = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        
        if count > 0:
            logger.info(f"🧹 Cleared {count} pending signals")
    
    def close(self) -> None:
        """
        Close control channel.
        
        Marks channel as inactive and clears queue.
        """
        self._active = False
        logger.info("🔒 ControlChannel closed")
    
    @property
    def is_active(self) -> bool:
        """Check if channel is active."""
        return self._active
    
    @property
    def pending_count(self) -> int:
        """Get count of pending signals."""
        return self._queue.qsize()


# Convenience functions for common signals

async def send_interrupt(
    channel: ControlChannel,
    reason: str = "",
    text: str = ""
) -> None:
    """
    Send INTERRUPT signal.
    
    Args:
        channel: Control channel instance
        reason: Interruption reason
        text: Optional text that triggered interrupt
    """
    await channel.send_signal(
        ControlSignal.INTERRUPT,
        metadata={'reason': reason, 'text': text}
    )


async def send_cancel(channel: ControlChannel, reason: str = "") -> None:
    """
    Send CANCEL signal.
    
    Args:
        channel: Control channel instance
        reason: Cancellation reason
    """
    await channel.send_signal(
        ControlSignal.CANCEL,
        metadata={'reason': reason}
    )


async def send_emergency_stop(channel: ControlChannel, reason: str) -> None:
    """
    Send EMERGENCY_STOP signal.
    
    Args:
        channel: Control channel instance
        reason: Emergency reason
    """
    await channel.send_signal(
        ControlSignal.EMERGENCY_STOP,
        metadata={'reason': reason}
    )
