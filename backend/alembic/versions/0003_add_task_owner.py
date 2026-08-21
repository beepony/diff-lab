"""Add anonymous ownership to tasks without assigning legacy records."""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_task_owner"
down_revision = "0002_add_share_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("diff_tasks")}
    if "owner_token_hash" not in columns:
        with op.batch_alter_table("diff_tasks") as batch_op:
            batch_op.add_column(sa.Column("owner_token_hash", sa.String(length=64), nullable=True))

    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("diff_tasks")}
    if "ix_diff_tasks_owner_expires_created" not in indexes:
        op.create_index(
            "ix_diff_tasks_owner_expires_created",
            "diff_tasks",
            ["owner_token_hash", "expires_at", "created_at"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("diff_tasks")}
    if "ix_diff_tasks_owner_expires_created" in indexes:
        op.drop_index("ix_diff_tasks_owner_expires_created", table_name="diff_tasks")
    columns = {column["name"] for column in inspector.get_columns("diff_tasks")}
    if "owner_token_hash" in columns:
        with op.batch_alter_table("diff_tasks") as batch_op:
            batch_op.drop_column("owner_token_hash")
