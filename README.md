# 🛡️ RiskTrix Backend API

Enterprise CISO Dashboard - Comprehensive Cybersecurity Risk Management Platform

## 🏗️ Architecture Overview

RiskTrix Backend is a scalable, production-ready FastAPI application designed for enterprise cybersecurity risk management. It provides comprehensive APIs for:

- **Vulnerability Management** - Track, assess, and remediate security vulnerabilities
- **Vendor Compliance (TPRM)** - Third-Party Risk Management and vendor oversight
- **Compliance Tracking** - Monitor adherence to security standards (ISO 27001, PCI DSS, etc.)
- **Application Security** - Manage application portfolios and security assessments
- **EOSL Management** - End of Service Life tracking for technology refresh
- **Audit & Reporting** - Comprehensive audit trails and compliance reporting

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.115+ (async/await support)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0 (async)
- **Authentication**: JWT with role-based access control
- **Caching**: Redis for session management and caching
- **Migrations**: Alembic for database schema management
- **Containerization**: Docker & Docker Compose
- **Monitoring**: Structured logging and health checks

## 📁 Project Structure

```
risktrix-backend/
├── app/
│   ├── api/                    # API endpoints
│   │   └── v1/
│   │       ├── endpoints/      # Individual endpoint modules
│   │       └── api.py         # Main API router
│   ├── core/                   # Core application config
│   │   ├── config.py          # Settings and configuration
│   │   └── security.py        # Authentication & security
│   ├── crud/                   # Database CRUD operations
│   ├── db/                     # Database configuration
│   │   ├── session.py         # Database session management
│   │   └── init_db.py         # Database initialization
│   ├── models/                 # SQLAlchemy models
│   │   └── models.py          # All database models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic layer
│   ├── utils/                  # Utility functions
│   └── main.py                 # FastAPI application entry point
├── migrations/                 # Alembic database migrations
├── scripts/                    # Setup and utility scripts
├── tests/                      # Test suite
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container configuration
├── requirements.txt            # Python dependencies
└── setup.sh                   # Automated setup script
```

## 🚀 Quick Start

### Option 1: Docker Setup (Recommended)

```bash
# Clone and navigate to project
cd risktrix-backend

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

The application will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/api/v1/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

### Option 2: Local Development Setup

```bash
# Run the automated setup script
./setup.sh

# Or manual setup:
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Setup PostgreSQL database
createuser -s risktrix_user
createdb -O risktrix_user risktrix_db

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=risktrix_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=risktrix_db

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## 📊 Database Models

### Core Entities

- **Users**: Role-based authentication (Admin, CISO, Security Analyst, etc.)
- **Organizations**: Multi-tenant organization management
- **Applications**: Application portfolio with security context
- **Vulnerabilities**: Comprehensive vulnerability tracking with CVSS scoring
- **Vendors**: Third-party vendor management and risk assessment
- **Compliance**: Standards tracking (ISO 27001, PCI DSS, SOX, GDPR, HIPAA)
- **EOSL Records**: End of Service Life technology tracking

### Key Features

- **Audit Logging**: Complete audit trail for all system activities
- **Role-based Access**: Granular permissions based on user roles
- **Multi-tenant**: Organization-based data isolation
- **Extensible**: Modular design for easy feature additions

## 🔒 Security Features

- **JWT Authentication** with refresh token support
- **Role-based Authorization** (RBAC)
- **CORS Protection** with configurable origins
- **Rate Limiting** to prevent abuse
- **Input Validation** with Pydantic schemas
- **SQL Injection Protection** via SQLAlchemy ORM
- **Password Hashing** with bcrypt
- **Audit Logging** for compliance and forensics

## 🌐 API Endpoints

### Core Modules

| Module | Endpoint | Description |
|--------|----------|-------------|
| Authentication | `/api/v1/auth/` | Login, logout, token refresh |
| Users | `/api/v1/users/` | User management and profiles |
| Applications | `/api/v1/applications/` | Application portfolio management |
| Vulnerabilities | `/api/v1/vulnerabilities/` | Vulnerability tracking and remediation |
| Vendors | `/api/v1/vendors/` | Third-party risk management |
| Compliance | `/api/v1/compliance/` | Compliance standards and records |
| EOSL | `/api/v1/eosl/` | End of Service Life tracking |
| Dashboard | `/api/v1/dashboard/` | Dashboard metrics and analytics |
| Reports | `/api/v1/reports/` | Report generation and export |

### API Documentation

- **Interactive Docs**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.json

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_vulnerabilities.py
```

## 📋 Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Implement Changes**: Add models, schemas, CRUD, and endpoints
3. **Create Migration**: `alembic revision --autogenerate -m "Add new feature"`
4. **Test Changes**: Run test suite and manual testing
5. **Update Documentation**: Update API docs and README
6. **Submit PR**: Create pull request for review

## 🐳 Docker Commands

```bash
# Build and start services
docker-compose up --build -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Access database
docker-compose exec postgres psql -U risktrix_user -d risktrix_db

# Access backend container
docker-compose exec backend bash

# Database backup
docker-compose run --rm backup
```

## 📊 Monitoring & Health Checks

- **Health Check**: `GET /health`
- **Application Logs**: Structured logging with timestamps
- **Database Connection Monitoring**: Connection pool metrics
- **Performance Tracking**: Request/response time logging

## 🔧 Production Deployment

1. **Environment Setup**: Configure production environment variables
2. **Database Setup**: Setup production PostgreSQL with backup strategy
3. **SSL Configuration**: Configure HTTPS with proper certificates
4. **Reverse Proxy**: Setup Nginx for load balancing and SSL termination
5. **Monitoring**: Implement monitoring and alerting
6. **Backup Strategy**: Configure automated database backups

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Email**: support@risktrix.com
- **Documentation**: [API Documentation](http://localhost:8000/api/v1/docs)
- **Issues**: Submit GitHub issues for bugs and feature requests

---

**RiskTrix Backend** - Enterprise-grade cybersecurity risk management platform built with modern Python technologies.