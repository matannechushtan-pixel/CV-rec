import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # job_seeker | company_admin
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False)
    cvs: Mapped[list["CV"]] = relationship("CV", back_populates="user")  # noqa: F821
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="user")  # noqa: F821
    discord_connection: Mapped["DiscordConnection | None"] = relationship("DiscordConnection", back_populates="user", uselist=False)  # noqa: F821


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    full_name: Mapped[str | None] = mapped_column(String)
    target_role: Mapped[str | None] = mapped_column(String)
    target_industry: Mapped[str | None] = mapped_column(String)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    behavioral_profile: Mapped[dict | None] = mapped_column(JSONB)
    writing_style: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
