"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text(), unique=True, nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("full_name", sa.Text()),
        sa.Column("target_role", sa.Text()),
        sa.Column("target_industry", sa.Text()),
        sa.Column("years_experience", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cvs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("version_name", sa.Text()),
        sa.Column("raw_text", sa.Text()),
        sa.Column("structured_data", postgresql.JSONB()),
        sa.Column("embedding", sa.Text()),  # placeholder; real type added below
        sa.Column("is_base", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute("ALTER TABLE cvs ALTER COLUMN embedding TYPE vector(1536) USING NULL;")
    op.execute("CREATE INDEX ON cvs USING hnsw (embedding vector_cosine_ops);")

    op.create_table(
        "job_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.Text(), unique=True),
        sa.Column("source", sa.Text()),
        sa.Column("title", sa.Text()),
        sa.Column("company", sa.Text()),
        sa.Column("location", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("required_skills", postgresql.JSONB()),
        sa.Column("embedding", sa.Text()),
        sa.Column("salary_min", sa.Integer()),
        sa.Column("salary_max", sa.Integer()),
        sa.Column("apply_url", sa.Text()),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute("ALTER TABLE job_listings ALTER COLUMN embedding TYPE vector(1536) USING NULL;")
    op.execute("CREATE INDEX ON job_listings USING hnsw (embedding vector_cosine_ops);")

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text()),
        sa.Column("industry", sa.Text()),
        sa.Column("size", sa.Text()),
        sa.Column("culture_summary", sa.Text()),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "company_job_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id")),
        sa.Column("title", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("required_skills", postgresql.JSONB()),
        sa.Column("embedding", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute(
        "ALTER TABLE company_job_posts ALTER COLUMN embedding TYPE vector(1536) USING NULL;"
    )
    op.execute("CREATE INDEX ON company_job_posts USING hnsw (embedding vector_cosine_ops);")

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "job_listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_listings.id")
        ),
        sa.Column("cv_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cvs.id")),
        sa.Column("match_score", sa.Float()),
        sa.Column("status", sa.Text(), server_default="applied"),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "roadmaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("target_role", sa.Text()),
        sa.Column("gap_analysis", postgresql.JSONB()),
        sa.Column("steps", postgresql.JSONB()),
        sa.Column("estimated_timeline_weeks", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cover_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column(
            "job_listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_listings.id")
        ),
        sa.Column("content", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("cover_letters")
    op.drop_table("roadmaps")
    op.drop_table("applications")
    op.drop_table("company_job_posts")
    op.drop_table("companies")
    op.drop_table("job_listings")
    op.drop_table("cvs")
    op.drop_table("profiles")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector;")
