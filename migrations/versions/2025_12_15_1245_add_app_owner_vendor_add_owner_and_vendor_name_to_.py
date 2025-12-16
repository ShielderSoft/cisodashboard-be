"""Add owner and vendor_name to applications

Revision ID: add_app_owner_vendor
Revises: add_vuln_remarks_poc
Create Date: 2025-12-15 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_app_owner_vendor'
down_revision = 'add_vuln_remarks_poc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add owner column to applications table
    op.add_column('applications', sa.Column('owner', sa.String(length=255), nullable=True))
    
    # Add vendor_name column to applications table
    op.add_column('applications', sa.Column('vendor_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove vendor_name column
    op.drop_column('applications', 'vendor_name')
    
    # Remove owner column
    op.drop_column('applications', 'owner')
