"""Add remarks and poc_file_path to vulnerabilities

Revision ID: add_vuln_remarks_poc
Revises: 02de63d3577d
Create Date: 2025-12-15 12:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_vuln_remarks_poc'
down_revision = '02de63d3577d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add remarks column to vulnerabilities table
    op.add_column('vulnerabilities', sa.Column('remarks', sa.Text(), nullable=True))
    
    # Add poc_file_path column to vulnerabilities table
    op.add_column('vulnerabilities', sa.Column('poc_file_path', sa.String(length=500), nullable=True))
    
    # Add index to status column for better query performance
    op.create_index('ix_vulnerabilities_status', 'vulnerabilities', ['status'], unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_vulnerabilities_status', table_name='vulnerabilities')
    
    # Remove poc_file_path column
    op.drop_column('vulnerabilities', 'poc_file_path')
    
    # Remove remarks column
    op.drop_column('vulnerabilities', 'remarks')
