"""Application notes and cover letter link

Revision ID: 005
Revises: 004
Create Date: 2026-06-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "applications",
        sa.Column("cover_letter_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_applications_cover_letter_id",
        "applications",
        "cover_letters",
        ["cover_letter_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_applications_cover_letter_id", "applications", type_="foreignkey")
    op.drop_column("applications", "cover_letter_id")
    op.drop_column("applications", "notes")
