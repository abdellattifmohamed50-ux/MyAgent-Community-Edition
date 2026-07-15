"""Product v1 persistence schema.

Revision ID: 0002_product_v1_schema
Revises: 0001_initial_schema
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_product_v1_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch operations transparently recreate tables on SQLite while issuing
    # regular ALTER statements on PostgreSQL. This keeps the documented
    # SQLite fallback and the production database on the same migration path.
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(length=120), nullable=True))
    op.execute("UPDATE users SET display_name = email WHERE display_name IS NULL")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "display_name",
            existing_type=sa.String(length=120),
            nullable=False,
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            )
        )
    op.add_column(
        "projects",
        sa.Column("description", sa.Text(), server_default="", nullable=False),
    )
    op.add_column(
        "projects",
        sa.Column("instructions", sa.Text(), server_default="", nullable=False),
    )
    op.add_column("projects", sa.Column("default_provider", sa.String(length=80)))
    op.add_column(
        "projects",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column("conversations", sa.Column("provider", sa.String(length=80)))
    op.add_column(
        "conversations",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column("messages", sa.Column("provider", sa.String(length=80)))
    op.add_column(
        "messages", sa.Column("input_tokens", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "messages", sa.Column("output_tokens", sa.Integer(), server_default="0", nullable=False)
    )
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.String(length=500)),
        sa.Column("ip_address", sa.String(length=64)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64)),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=50), server_default="text", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_knowledge_documents_user_id", "knowledge_documents", ["user_id"])
    op.create_index("ix_knowledge_documents_project_id", "knowledge_documents", ["project_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64)),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), server_default="{}", nullable=False),
        sa.Column("ip_address", sa.String(length=64)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("knowledge_documents")
    op.drop_table("refresh_sessions")
    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_column("output_tokens")
        batch_op.drop_column("input_tokens")
        batch_op.drop_column("provider")
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("provider")
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("default_provider")
        batch_op.drop_column("instructions")
        batch_op.drop_column("description")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("display_name")
