"""Gemini CV generator fields

Revision ID: 003
Revises: 002
Create Date: 2026-06-11
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cvs", sa.Column("html_content", sa.Text(), nullable=True))
    op.add_column("cvs", sa.Column("source", sa.String(), nullable=True))
    op.add_column("cvs", sa.Column("language", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("cvs", "language")
    op.drop_column("cvs", "source")
    op.drop_column("cvs", "html_content")
