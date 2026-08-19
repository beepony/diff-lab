"""Create the initial Diff.lab schema, including indexes for active-task lookups."""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _index(inspector, table_name: str, index_name: str):
    return next((index for index in inspector.get_indexes(table_name) if index["name"] == index_name), None)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "diff_tasks"):
        op.create_table(
            "diff_tasks",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("mode", sa.String(), nullable=False),
            sa.Column("column_a", sa.Text(), nullable=False),
            sa.Column("column_b", sa.Text(), nullable=False),
            sa.Column("column_a_meta", sa.Text(), nullable=True),
            sa.Column("column_b_meta", sa.Text(), nullable=True),
            sa.Column("options", sa.Text(), nullable=True),
            sa.Column("result_meta", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
        )

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "share_links"):
        op.create_table(
            "share_links",
            sa.Column("task_id", sa.String(), nullable=False),
            sa.Column("access_token", sa.String(), nullable=False),
            sa.Column("permission", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["diff_tasks.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("task_id", "access_token"),
        )

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "diff_tasks", "ix_diff_tasks_expires_created"):
        op.create_index("ix_diff_tasks_expires_created", "diff_tasks", ["expires_at", "created_at"])
    share_token_index = _index(inspector, "share_links", "ix_share_links_access_token")
    if share_token_index and not share_token_index["unique"]:
        duplicates = bind.execute(
            sa.text(
                "SELECT access_token FROM share_links "
                "GROUP BY access_token HAVING COUNT(*) > 1 LIMIT 1"
            )
        ).first()
        if duplicates:
            raise RuntimeError("Cannot enforce unique share tokens: duplicate token exists")
        op.drop_index("ix_share_links_access_token", table_name="share_links")
        share_token_index = None
    if not share_token_index:
        op.create_index("ix_share_links_access_token", "share_links", ["access_token"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_table(inspector, "share_links"):
        op.drop_table("share_links")
    if _has_table(inspector, "diff_tasks"):
        op.drop_table("diff_tasks")
