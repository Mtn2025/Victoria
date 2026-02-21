"""
Frame Processor Base Class.
Part of the Application Layer (Hexagonal Architecture).
"""
import logging
from abc import ABC, abstractmethod
from enum import IntEnum

from backend.application.processors.frames import Frame

logger = logging.getLogger(__name__)

class FrameDirection(IntEnum):
    DOWNSTREAM = 1  # Audio Input -> Processing -> Output
    UPSTREAM = 2    # Feedback / Control signals going back up

class FrameProcessor(ABC):
    """
    Base class for pipeline processors.
    Implements a doubly-linked list structure for the pipeline.
    """
    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self._next: 'FrameProcessor' | None = None
        self._prev: 'FrameProcessor' | None = None

    def link(self, processor: 'FrameProcessor'):
        """Connect this processor to the next one."""
        self._next = processor
        processor._prev = self

    async def start(self):
        """Initialize resources (optional hook)."""
        pass

    async def stop(self):
        """Cleanup resources (optional hook)."""
        pass

    @abstractmethod
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process a frame.
        Must call push_frame() to propagate results.
        """
        pass

    async def push_frame(self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM):
        """Send a frame to the next/prev processor."""
        if direction == FrameDirection.DOWNSTREAM:
            if self._next:
                try:
                    await self._next.process_frame(frame, direction)
                except Exception as e:
                    logger.error(f"[{self.name} -> {self._next.name}] Process Error: {e}", exc_info=True)
            else:
                # End of chain
                pass
        elif direction == FrameDirection.UPSTREAM:
            if self._prev:
                try:
                    await self._prev.process_frame(frame, direction)
                except Exception as e:
                    logger.error(f"[{self.name} -> {self._prev.name}] Process Error: {e}", exc_info=True)
            else:
                # Start of chain
                pass
