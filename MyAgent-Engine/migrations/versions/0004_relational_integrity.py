"""Enforce relational integrity after the v2 additive schema.

Revision ID: 0004_relational_integrity
Revises: 0003_v2_stable
Create Date: 2026-07-14
"""

from alembic import op

revision = "0004_relational_integrity"
down_revision = "0003_v2_stable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Clean legacy orphan rows, then add explicit foreign keys.

    The cleanup is intentionally conservative: orphaned mandatory children are
    removed, while broken optional project/user links are detached with NULL.
    """
    op.execute(
        "DELETE FROM refresh_sessions WHERE NOT EXISTS "
        "(SELECT 1 FROM users WHERE users.id = refresh_sessions.user_id)"
    )
    op.execute(
        "DELETE FROM knowledge_documents WHERE NOT EXISTS "
        "(SELECT 1 FROM users WHERE users.id = knowledge_documents.user_id)"
    )
    op.execute(
        "DELETE FROM conversations WHERE NOT EXISTS "
        "(SELECT 1 FROM users WHERE users.id = conversations.user_id)"
    )
    op.execute(
        "DELETE FROM projects WHERE NOT EXISTS "
        "(SELECT 1 FROM users WHERE users.id = projects.owner_id)"
    )
    op.execute(
        "UPDATE conversations SET project_id = NULL WHERE project_id IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM projects WHERE projects.id = conversations.project_id)"
    )
    op.execute(
        "UPDATE knowledge_documents SET project_id = NULL WHERE project_id IS NOT NULL "
        "AND NOT EXISTS "
        "(SELECT 1 FROM projects WHERE projects.id = knowledge_documents.project_id)"
    )
    op.execute(
        "UPDATE audit_events SET user_id = NULL WHERE user_id IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM users WHERE users.id = audit_events.user_id)"
    )
    op.execute(
        "DELETE FROM messages WHERE NOT EXISTS "
        "(SELECT 1 FROM conversations WHERE conversations.id = messages.conversation_id)"
    )

    with op.batch_alter_table("projects") as batch_op:
        batch_op.create_foreign_key(
            "fk_projects_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("conversations") as batch_op:
        batch_op.create_foreign_key(
            "fk_conversations_project_id_projects",
            "projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_conversations_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_conversations_project_id", ["project_id"])

    with op.batch_alter_table("messages") as batch_op:
        batch_op.create_foreign_key(
            "fk_messages_conversation_id_conversations",
            "conversations",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.create_foreign_key(
            "fk_refresh_sessions_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("knowledge_documents") as batch_op:
        batch_op.create_foreign_key(
            "fk_knowledge_documents_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_knowledge_documents_project_id_projects",
            "projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("audit_events") as batch_op:
        batch_op.create_foreign_key(
            "fk_audit_events_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("audit_events") as batch_op:
        batch_op.drop_constraint("fk_audit_events_user_id_users", type_="foreignkey")

    with op.batch_alter_table("knowledge_documents") as batch_op:
        batch_op.drop_constraint("fk_knowledge_documents_project_id_projects", type_="foreignkey")
        batch_op.drop_constraint("fk_knowledge_documents_user_id_users", type_="foreignkey")

    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.drop_constraint("fk_refresh_sessions_user_id_users", type_="foreignkey")

    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_constraint("fk_messages_conversation_id_conversations", type_="foreignkey")

    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_index("ix_conversations_project_id")
        batch_op.drop_constraint("fk_conversations_user_id_users", type_="foreignkey")
        batch_op.drop_constraint("fk_conversations_project_id_projects", type_="foreignkey")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("fk_projects_owner_id_users", type_="foreignkey")
