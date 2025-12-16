"""
Migration script to add vendor_certificates table
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine


async def create_vendor_certificates_table():
    """Create vendor_certificates table"""
    
    sql_commands = [
        # Create table
        """
        CREATE TABLE IF NOT EXISTS vendor_certificates (
            id SERIAL PRIMARY KEY,
            certificate_type VARCHAR(100) NOT NULL,
            certificate_number VARCHAR(255),
            issue_date DATE NOT NULL,
            expiry_date DATE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'compliant',
            issuing_authority VARCHAR(255),
            certificate_url VARCHAR(500),
            scope TEXT,
            notes TEXT,
            vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
            application_id INTEGER REFERENCES applications(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # Create indexes
        "CREATE INDEX IF NOT EXISTS idx_vendor_certificates_vendor_id ON vendor_certificates(vendor_id)",
        "CREATE INDEX IF NOT EXISTS idx_vendor_certificates_application_id ON vendor_certificates(application_id)",
        "CREATE INDEX IF NOT EXISTS idx_vendor_certificates_expiry_date ON vendor_certificates(expiry_date)",
        "CREATE INDEX IF NOT EXISTS idx_vendor_certificates_status ON vendor_certificates(status)",
        # Create function
        """
        CREATE OR REPLACE FUNCTION update_vendor_certificates_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """,
        # Drop trigger if exists
        "DROP TRIGGER IF EXISTS trigger_vendor_certificates_updated_at ON vendor_certificates",
        # Create trigger
        """
        CREATE TRIGGER trigger_vendor_certificates_updated_at
            BEFORE UPDATE ON vendor_certificates
            FOR EACH ROW
            EXECUTE FUNCTION update_vendor_certificates_updated_at()
        """
    ]
    
    async with engine.begin() as conn:
        for sql_command in sql_commands:
            await conn.execute(text(sql_command))
        print("✓ Created vendor_certificates table")
        print("✓ Created indexes on vendor_certificates")
        print("✓ Created trigger for updated_at column")


async def main():
    """Run migration"""
    print("Starting migration: Add vendor_certificates table...")
    try:
        await create_vendor_certificates_table()
        print("\n✓ Migration completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
