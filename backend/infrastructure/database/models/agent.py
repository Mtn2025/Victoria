import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, JSON, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class AgentModel(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Public UUID — generated in Python (engine-agnostic, works with SQLite in tests)
    agent_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False,
                                             default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
    system_prompt: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String, default="es-MX")

    # Flow & Native Provider (V4 Identity)
    provider: Mapped[str] = mapped_column(String, default="browser", server_default="browser", nullable=False)
    connectivity_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Voice Config
    voice_provider: Mapped[str] = mapped_column(String, default="azure")
    voice_name: Mapped[str] = mapped_column(String)
    voice_style: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    voice_speed: Mapped[float] = mapped_column(Float, default=1.0)
    voice_pitch: Mapped[float] = mapped_column(Float, default=0.0)
    voice_volume: Mapped[float] = mapped_column(Float, default=100.0)

    first_message: Mapped[str] = mapped_column(Text, default="")
    silence_timeout_ms: Mapped[int] = mapped_column(Integer, default=1500)

    # JSON Fields for flexibility
    tools_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    llm_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    voice_config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    stt_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    flow_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analysis_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    system_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    calls: Mapped[List["CallModel"]] = relationship(back_populates="agent")

