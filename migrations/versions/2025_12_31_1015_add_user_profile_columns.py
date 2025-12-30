"""add user profile columns

Revision ID: add_user_profile_columns
Revises: 4e91dfd0a028
Create Date: 2025-12-31 10:15:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_profile_columns'
down_revision = '4e91dfd0a028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new profile-related columns to users table
    op.add_column('users', sa.Column('profile_type', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('company', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('privilege_level', sa.String(length=50), nullable=False, server_default='standard'))
    op.add_column('users', sa.Column('clearance_level', sa.String(length=50), nullable=False, server_default='low'))


def downgrade() -> None:
    op.drop_column('users', 'clearance_level')
    op.drop_column('users', 'privilege_level')
    op.drop_column('users', 'company')
    op.drop_column('users', 'profile_type')
