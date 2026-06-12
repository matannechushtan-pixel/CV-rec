import uuid
from datetime import datetime
from sqlalchemy import String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    job_listing_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("job_listings.id"))
    cv_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cvs.id"))
    match_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(
        String, default="applied"
    )  # applied | viewed | interview | rejected | offer
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text)
    cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cover_letters.id"))

    user: Mapped["User"] = relationship("User", back_populates="applications")  # noqa: F821
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="applications")  # noqa: F821
    cv: Mapped["CV"] = relationship("CV", back_populates="applications")  # noqa: F821
