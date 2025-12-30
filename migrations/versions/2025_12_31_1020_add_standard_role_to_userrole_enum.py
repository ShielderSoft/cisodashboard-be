"""add standard role to userrole enum

Revision ID: add_standard_role
Revises: add_user_profile_columns
Create Date: 2025-12-31 10:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_standard_role'
down_revision = 'add_user_profile_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'standard' value to the userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'standard' AFTER 'admin'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type without 'standard' if rollback is needed
    pass
