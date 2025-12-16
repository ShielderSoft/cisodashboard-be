#!/bin/bash

# RiskTrix Backend Setup Script
# This script sets up the complete development environment

set -e

echo "🚀 Setting up RiskTrix Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python 3.11+ is installed
check_python() {
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc) -eq 1 ]]; then
            PYTHON_CMD="python3"
        else
            print_error "Python 3.11+ is required. Found Python $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3.11+ is not installed"
        exit 1
    fi
    print_status "Python check passed: $($PYTHON_CMD --version)"
}

# Create virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    else
        print_status "Virtual environment already exists"
    fi
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_status "Activating virtual environment and installing dependencies..."
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Dependencies installed successfully"
}

# Setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please update the .env file with your actual configuration"
    else
        print_status ".env file already exists"
    fi
}

# Check PostgreSQL
check_postgresql() {
    if command -v psql &> /dev/null; then
        print_status "PostgreSQL is available"
    else
        print_warning "PostgreSQL not found. Please install PostgreSQL 15+"
        print_warning "On macOS: brew install postgresql@15"
        print_warning "On Ubuntu: sudo apt-get install postgresql-15"
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Source environment variables
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
    fi
    
    # Create database user and database
    print_status "Creating database and user..."
    
    # Create user and database (adjust as needed for your setup)
    echo "Please run the following commands in PostgreSQL as a superuser:"
    echo "CREATE USER ${POSTGRES_USER:-risktrix_user} WITH ENCRYPTED PASSWORD '${POSTGRES_PASSWORD:-risktrix_secure_password_2024}';"
    echo "CREATE DATABASE ${POSTGRES_DB:-risktrix_db} OWNER ${POSTGRES_USER:-risktrix_user};"
    echo "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB:-risktrix_db} TO ${POSTGRES_USER:-risktrix_user};"
}

# Initialize Alembic
init_alembic() {
    print_status "Initializing database migrations..."
    
    source venv/bin/activate
    
    # Create initial migration
    if [ ! -d "migrations/versions" ]; then
        alembic revision --autogenerate -m "Initial migration"
    fi
    
    print_status "Database migrations initialized"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p uploads
    mkdir -p logs
    mkdir -p backups
    
    print_status "Directories created"
}

# Main setup function
main() {
    echo "🏗️  RiskTrix Backend Setup"
    echo "=========================="
    
    check_python
    setup_venv
    install_dependencies
    setup_env
    check_postgresql
    setup_database
    create_directories
    init_alembic
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update the .env file with your database credentials"
    echo "2. Create the PostgreSQL database and user"
    echo "3. Run migrations: alembic upgrade head"
    echo "4. Start the development server: python -m uvicorn app.main:app --reload"
    echo ""
    echo "🐳 For Docker setup:"
    echo "   docker-compose up -d"
    echo ""
}

# Run main function
main