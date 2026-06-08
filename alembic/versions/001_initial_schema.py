"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("balance", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("customer_id"),
    )
    op.create_table(
        "orders",
        sa.Column("order_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("ship_date", sa.String(), nullable=True),
        sa.Column("delivery_date", sa.String(), nullable=True),
        sa.Column("total", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("order_id"),
    )
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("messages", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("ticket_id", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("session_id"),
    )


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("orders")
    op.drop_table("customers")
