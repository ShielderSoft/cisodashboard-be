"""add_certificate_fields_to_vendors

Revision ID: be2c37d28dbf
Revises: 2096077ae5cf
Create Date: 2026-02-04 11:20:57.881473+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be2c37d28dbf'
down_revision = '2096077ae5cf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add certificate fields to vendors table
    op.add_column('vendors', sa.Column('application_name', sa.String(length=255), nullable=True))
    op.add_column('vendors', sa.Column('certificate_type', sa.String(length=100), nullable=True))
    op.add_column('vendors', sa.Column('certificate_issue_date', sa.Date(), nullable=True))
    op.add_column('vendors', sa.Column('certificate_expiry_date', sa.Date(), nullable=True))


def downgrade() -> None:
    # Remove certificate fields from vendors table
    op.drop_column('vendors', 'certificate_expiry_date')
    op.drop_column('vendors', 'certificate_issue_date')
    op.drop_column('vendors', 'certificate_type')
    op.drop_column('vendors', 'application_name')