from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class CallModel(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id"), nullable=True, index=True)
    agent: Mapped[Optional["AgentModel"]] = relationship(back_populates="calls")
    
    status: Mapped[str] = mapped_column(String, default="initiated", index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    client_type: Mapped[str] = mapped_column(String, default="unknown", index=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    transcripts: Mapped[List["TranscriptModel"]] = relationship(back_populates="call", cascade="all, delete-orphan")
