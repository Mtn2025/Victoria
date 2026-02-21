"""
Pipeline Frames (DTOs).
Part of the Application Layer (Hexagonal Architecture).
"""
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any, Literal

class FrameDirection(IntEnum):
    """Direction a frame travels through the pipeline.
    
    CANONICAL DEFINITION — single source of truth.
    Imported by frame_processor.py and re-exported from there.
    Do NOT redefine FrameDirection elsewhere.
    """
    DOWNSTREAM = 1  # source → sink (normal flow: audio → VAD → STT → LLM → TTS)
    UPSTREAM   = 2  # sink → source (e.g. backpressure, control signals)

@dataclass(kw_only=True)
class Frame:
    """Base class for all pipeline frames."""
    id: str = field(init=False)
    name: str = field(init=False)
    timestamp: float = field(default_factory=time.time)
    trace_id: str = field(default="")
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.id = str(uuid.uuid4())
        self.name = self.__class__.__name__
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())

    def to_dict(self, include_binary: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_binary and 'data' in data and isinstance(data['data'], bytes):
            data['data'] = f"<bytes len={len(data['data'])}>"
        return data

# --- System/Control Frames ---

@dataclass(kw_only=True)
class SystemFrame(Frame):
    """High priority system signals."""
    pass

@dataclass(kw_only=True)
class DataFrame(Frame):
    """Standard priority data payload."""
    pass

@dataclass(kw_only=True)
class ControlFrame(Frame):
    """Control signals for processors."""
    pass

@dataclass(kw_only=True)
class StartFrame(SystemFrame):
    pass

@dataclass(kw_only=True)
class EndFrame(SystemFrame):
    reason: str = "normal"

@dataclass(kw_only=True)
class CancelFrame(SystemFrame):
    reason: str = "cancelled"

@dataclass(kw_only=True)
class EndTaskFrame(SystemFrame):
    """Signal to end a specific task/tool execution."""
    task_id: str = ""
    result: dict[str, Any] = field(default_factory=dict)

@dataclass(kw_only=True)
class ErrorFrame(SystemFrame):
    error: str
    fatal: bool = False

@dataclass(kw_only=True)
class BackpressureFrame(SystemFrame):
    """
    Backpressure signal emitted when pipeline queue is full or approaching capacity.
    """
    queue_size: int
    max_size: int
    severity: str = "warning"  # 'warning' or 'critical'

@dataclass(kw_only=True)
class UserStartedSpeakingFrame(SystemFrame):
    """Signal detected by VAD that user has started speaking."""
    pass

@dataclass(kw_only=True)
class UserStoppedSpeakingFrame(SystemFrame):
    """Signal detected by VAD that user has stopped speaking."""
    pass

# --- Data Frames ---

@dataclass(kw_only=True)
class AudioFrame(DataFrame):
    """Raw audio data frame."""
    data: bytes
    sample_rate: int
    channels: int = 1

@dataclass(kw_only=True)
class TextFrame(DataFrame):
    """Transcript or text response frame."""
    text: str
    is_final: bool = True
    role: Literal["user", "assistant", "system"] = "user"

@dataclass(kw_only=True)
class ImageFrame(DataFrame):
    """Image data frame."""
    data: bytes
    format: str
    size: tuple[int, int]
