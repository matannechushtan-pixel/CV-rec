import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from core.database import Base


class JobListing(Base):
    __tablename__ = "job_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String, unique=True)
    source: Mapped[str | None] = mapped_column(String)  # adzuna | jsearch
    title: Mapped[str | None] = mapped_column(String)
    company: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    required_skills: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    apply_url: Mapped[str | None] = mapped_column(String)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job_listing")  # noqa: F821
