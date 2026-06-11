"""CV generation fields and profile enrichment

Revision ID: 002
Revises: 001
Create Date: 2026-06-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cvs", sa.Column("pdf_url", sa.Text(), nullable=True))
    op.add_column("cvs", sa.Column("latex_source", sa.Text(), nullable=True))
    op.add_column("cvs", sa.Column("font_id", sa.Text(), nullable=True))

    op.add_column("profiles", sa.Column("behavioral_profile", postgresql.JSONB(), nullable=True))
    op.add_column("profiles", sa.Column("writing_style", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "writing_style")
    op.drop_column("profiles", "behavioral_profile")

    op.drop_column("cvs", "font_id")
    op.drop_column("cvs", "latex_source")
    op.drop_column("cvs", "pdf_url")
