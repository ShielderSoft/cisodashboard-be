"""
Pytest configuration and fixtures for RBAC tests
"""
import pytest
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def async_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_db_engine):
    """Create async database session"""
    async_session_maker = sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def override_get_db(async_session):
    """Override the get_db dependency"""
    async def _override_get_db():
        yield async_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(async_session):
    """Create admin user"""
    user = User(
        email="admin@test.com",
        username="admin",
        hashed_password=get_password_hash("Admin@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def ciso_user(async_session):
    """Create CISO user"""
    user = User(
        email="ciso@test.com",
        username="ciso",
        hashed_password=get_password_hash("Ciso@123"),
        role=UserRole.CISO,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def infosec_manager_user(async_session):
    """Create InfoSec Manager user"""
    user = User(
        email="manager@test.com",
        username="manager",
        hashed_password=get_password_hash("Manager@123"),
        role=UserRole.INFOSEC_MANAGER,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def external_auditor_user(async_session):
    """Create External Auditor user"""
    user = User(
        email="ext_auditor@test.com",
        username="ext_auditor",
        hashed_password=get_password_hash("ExtAuditor@123"),
        role=UserRole.EXTERNAL_AUDITOR,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def internal_auditor_user(async_session):
    """Create Internal Auditor user"""
    user = User(
        email="int_auditor@test.com",
        username="int_auditor",
        hashed_password=get_password_hash("IntAuditor@123"),
        role=UserRole.INTERNAL_AUDITOR,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def security_analyst_user(async_session):
    """Create Security Analyst user"""
    user = User(
        email="analyst@test.com",
        username="analyst",
        hashed_password=get_password_hash("Analyst@123"),
        role=UserRole.SECURITY_ANALYST,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def viewer_user(async_session):
    """Create Viewer user"""
    user = User(
        email="viewer@test.com",
        username="viewer",
        hashed_password=get_password_hash("Viewer@123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def all_users(
    admin_user, 
    ciso_user, 
    infosec_manager_user,
    external_auditor_user,
    internal_auditor_user,
    security_analyst_user,
    viewer_user
):
    """Get all user fixtures"""
    return {
        "admin": admin_user,
        "ciso": ciso_user,
        "infosec_manager": infosec_manager_user,
        "external_auditor": external_auditor_user,
        "internal_auditor": internal_auditor_user,
        "security_analyst": security_analyst_user,
        "viewer": viewer_user,
    }


@pytest.fixture
async def async_client(override_get_db):
    """Create async HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def get_auth_headers(async_session):
    """Get authentication headers for a user"""
    async def _get_auth_headers(user: User):
        # In real implementation, generate JWT token
        # For now, return mock header
        return {
            "Authorization": f"Bearer mock_token_for_{user.email}"
        }
    return _get_auth_headers
