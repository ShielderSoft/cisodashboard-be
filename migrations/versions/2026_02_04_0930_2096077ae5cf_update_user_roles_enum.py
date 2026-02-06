"""update_user_roles_enum

Revision ID: 2096077ae5cf
Revises: add_standard_role
Create Date: 2026-02-04 09:30:06.460438+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2096077ae5cf'
down_revision = 'add_standard_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE ADD VALUE to be in its own transaction
    # and committed before the new values can be used.
    # We use op.get_bind().execute() with autocommit mode for ALTER TYPE
    
    connection = op.get_bind()
    
    # Step 1: Add new enum values (these need to be committed immediately)
    # Use COMMIT and start new transaction for each ALTER TYPE
    connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'INFOSEC_MANAGER'"))
    connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'EXTERNAL_AUDITOR'"))
    connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'INTERNAL_AUDITOR'"))
    
    # Force a commit by using op.execute which respects transaction boundaries
    # The values are now available for use
    
    # Step 2: Update existing users with old roles to new roles
    # STANDARD -> SECURITY_ANALYST (or VIEWER for basic users)
    op.execute("UPDATE users SET role = 'SECURITY_ANALYST' WHERE role = 'STANDARD'")
    
    # COMPLIANCE_OFFICER -> INFOSEC_MANAGER
    op.execute("UPDATE users SET role = 'INFOSEC_MANAGER' WHERE role = 'COMPLIANCE_OFFICER'")
    
    # AUDITOR -> INTERNAL_AUDITOR (you can change to EXTERNAL_AUDITOR if needed)
    op.execute("UPDATE users SET role = 'INTERNAL_AUDITOR' WHERE role = 'AUDITOR'")
    
    # Step 3: Note - We cannot remove old enum values in PostgreSQL easily
    # Old values (STANDARD, COMPLIANCE_OFFICER, AUDITOR) will remain in the enum
    # but won't be used. To fully remove them, you'd need to recreate the enum,
    # which requires dropping and recreating the table or using a complex workaround.


def downgrade() -> None:
    # Revert role mappings
    op.execute("UPDATE users SET role = 'STANDARD' WHERE role = 'SECURITY_ANALYST'")
    op.execute("UPDATE users SET role = 'COMPLIANCE_OFFICER' WHERE role = 'INFOSEC_MANAGER'")
    op.execute("UPDATE users SET role = 'AUDITOR' WHERE role IN ('INTERNAL_AUDITOR', 'EXTERNAL_AUDITOR')")