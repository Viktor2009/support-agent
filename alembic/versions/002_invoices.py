"""Add invoices table

Revision ID: 002
Revises: 001
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("invoice_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("due_date", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("invoice_id"),
    )


def downgrade() -> None:
    op.drop_table("invoices")
