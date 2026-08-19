"""Add an independent expiry timestamp to share links."""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_share_expiry"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("share_links")}
    if "expires_at" in columns:
        return

    with op.batch_alter_table("share_links") as batch_op:
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.execute(
        "UPDATE share_links SET expires_at = "
        "COALESCE((SELECT expires_at FROM diff_tasks WHERE diff_tasks.id = share_links.task_id), CURRENT_TIMESTAMP) "
        "WHERE expires_at IS NULL"
    )
    with op.batch_alter_table("share_links") as batch_op:
        batch_op.alter_column("expires_at", existing_type=sa.DateTime(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("share_links") as batch_op:
        batch_op.drop_column("expires_at")
