"""initial user table

Revision ID: f95d13e53aaf
Revises: 
Create Date: 2025-02-08 22:28:20.553223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.core.utils import get_date_without_tz


# revision identifiers, used by Alembic.
revision: str = 'f95d13e53aaf'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("last_name", sa.String, nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("password", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime,
                  default=get_date_without_tz(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
