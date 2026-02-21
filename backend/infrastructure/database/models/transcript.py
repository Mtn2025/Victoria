from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class TranscriptModel(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), index=True)
    
    role: Mapped[str] = mapped_column(String) # user, assistant
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    call: Mapped["CallModel"] = relationship(back_populates="transcripts")
