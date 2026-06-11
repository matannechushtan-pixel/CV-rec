import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from core.database import Base


class CV(Base):
    __tablename__ = "cvs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    version_name: Mapped[str | None] = mapped_column(String)
    raw_text: Mapped[str | None] = mapped_column(Text)
    structured_data: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    is_base: Mapped[bool] = mapped_column(Boolean, default=False)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    latex_source: Mapped[str | None] = mapped_column(Text)
    font_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="cvs")  # noqa: F821
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="cv")  # noqa: F821
