"""performance indexes

Revision ID: 0002_performance_indexes
Revises: 
Create Date: 2026-05-17
"""

from alembic import op


revision = "0002_performance_indexes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_receipts_user_date ON receipts (user_id, receipt_date)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_receipts_user_date")
