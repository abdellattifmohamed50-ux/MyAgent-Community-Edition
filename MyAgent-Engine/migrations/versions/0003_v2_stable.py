"""Add v2 bounded memory and provider usage fields.

Revision ID: 0003_v2_stable
Revises: 0002_product_v1_schema
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_v2_stable"
down_revision = "0002_product_v1_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
    )
    op.add_column("messages", sa.Column("model", sa.String(length=120)))
    op.add_column("messages", sa.Column("estimated_cost_microusd", sa.Integer()))
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_column("messages", "estimated_cost_microusd")
    op.drop_column("messages", "model")
    op.drop_column("conversations", "summary")
