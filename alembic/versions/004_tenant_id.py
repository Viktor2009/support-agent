"""add tenant_id columns

Revision ID: 004
Revises: 003
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("tenant_id", sa.String(), server_default="default", nullable=False),
    )
    op.drop_constraint("customers_pkey", "customers", type_="primary")
    op.create_primary_key("customers_pkey", "customers", ["tenant_id", "customer_id"])

    for table in ("orders", "invoices", "sessions", "feedback"):
        op.add_column(
            table,
            sa.Column("tenant_id", sa.String(), server_default="default", nullable=False),
        )


def downgrade() -> None:
    for table in ("feedback", "sessions", "invoices", "orders"):
        op.drop_column(table, "tenant_id")

    op.drop_constraint("customers_pkey", "customers", type_="primary")
    op.drop_column("customers", "tenant_id")
    op.create_primary_key("customers_pkey", "customers", ["customer_id"])
