"""first migration

Revision ID: 7969ce99fb31
Revises:
Create Date: 2022-01-06 16:20:28.113245

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7969ce99fb31"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "asdf",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("asdf")
