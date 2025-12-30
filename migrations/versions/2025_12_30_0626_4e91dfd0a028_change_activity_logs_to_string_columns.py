"""change_activity_logs_to_string_columns

Revision ID: 4e91dfd0a028
Revises: c0dc79dc8a00
Create Date: 2025-12-30 06:26:24.633602+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e91dfd0a028'
down_revision = 'c0dc79dc8a00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change activity_type column from enum to varchar
    op.execute('ALTER TABLE activity_logs ALTER COLUMN activity_type TYPE VARCHAR(100) USING activity_type::text')
    
    # Change priority column from enum to varchar  
    op.execute('ALTER TABLE activity_logs ALTER COLUMN priority TYPE VARCHAR(50) USING priority::text')


def downgrade() -> None:
    # Revert priority column back to enum
    op.execute('ALTER TABLE activity_logs ALTER COLUMN priority TYPE activitypriority USING priority::activitypriority')
    
    # Revert activity_type column back to enum
    op.execute('ALTER TABLE activity_logs ALTER COLUMN activity_type TYPE activitytype USING activity_type::activitytype')