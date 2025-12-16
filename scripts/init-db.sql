#!/bin/bash
# Database initialization script

set -e

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable UUID extension
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Enable pg_stat_statements for query monitoring
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    
    -- Create indexes for performance
    -- These will be created by Alembic migrations, but keeping as backup
    
    -- Grant necessary permissions
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- Create schemas if needed
    CREATE SCHEMA IF NOT EXISTS audit;
    
    ECHO 'Database initialization completed successfully!';
EOSQL