"""create llm_settings table

Revision ID: e8a1c3d5f702
Revises: d4c8f6a2b901
Create Date: 2026-09-20 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8a1c3d5f702"
down_revision: Union[str, Sequence[str], None] = "d4c8f6a2b901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("llm_settings")
