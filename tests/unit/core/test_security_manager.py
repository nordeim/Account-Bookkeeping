# File: tests/unit/core/test_security_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import datetime

from app.core.security_manager import SecurityManager
from app.core.database_manager import DatabaseManager
from app.models.core.user import User, Role, Permission
from app.utils.result import Result
from app.utils.pydantic_models import UserCreateData, UserUpdateData, RoleCreateData

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager."""
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def security_manager(mock_db_manager: MagicMock) -> SecurityManager:
    """Fixture to create a SecurityManager instance."""
    return SecurityManager(db_manager=mock_db_manager)

@pytest.fixture
def sample_user_orm() -> User:
    """Provides a sample User ORM object."""
    user = User(
        id=1,
        username="testuser",
        password_hash="$2b$12$EXAMPLEHASHSTRINGHERE............", # Example hash
        is_active=True,
        roles=[]
    )
    return user

@pytest.fixture
def sample_admin_role() -> Role:
    return Role(id=1, name="Administrator", permissions=[])

@pytest.fixture
def sample_viewer_role() -> Role:
    view_perm = Permission(id=1, code="ACCOUNT_VIEW", module="Accounting")
    return Role(id=2, name="Viewer", permissions=[view_perm])


def test_hash_and_verify_password(security_manager: SecurityManager):
    """Test that password hashing and verification work correctly."""
    password = "MyStrongPassword123"
    hashed_password = security_manager.hash_password(password)
    
    assert hashed_password != password
    assert isinstance(hashed_password, str)
    assert security_manager.verify_password(password, hashed_password) is True
    assert security_manager.verify_password("WrongPassword", hashed_password) is False

async def test_authenticate_user_success(security_manager: SecurityManager, mock_session: AsyncMock, sample_user_orm: User):
    """Test successful user authentication."""
    password = "password"
    sample_user_orm.password_hash = security_manager.hash_password(password)
    sample_user_orm.is_active = True
    
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_user_orm
    
    authenticated_user = await security_manager.authenticate_user("testuser", password)
    
    assert authenticated_user is not None
    assert authenticated_user.id == 1
    assert security_manager.current_user == authenticated_user
    mock_session.commit.assert_awaited_once()

async def test_authenticate_user_wrong_password(security_manager: SecurityManager, mock_session: AsyncMock, sample_user_orm: User):
    """Test authentication failure due to wrong password."""
    password = "password"
    sample_user_orm.password_hash = security_manager.hash_password(password)
    sample_user_orm.is_active = True
    sample_user_orm.failed_login_attempts = 0
    
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_user_orm

    authenticated_user = await security_manager.authenticate_user("testuser", "wrongpassword")
    
    assert authenticated_user is None
    assert security_manager.current_user is None
    assert sample_user_orm.failed_login_attempts == 1
    mock_session.commit.assert_awaited_once()

async def test_authenticate_user_inactive(security_manager: SecurityManager, mock_session: AsyncMock, sample_user_orm: User):
    """Test authentication failure for an inactive user."""
    sample_user_orm.is_active = False
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_user_orm

    authenticated_user = await security_manager.authenticate_user("testuser", "password")
    
    assert authenticated_user is None
    mock_session.commit.assert_awaited_once() # Still commits attempt info

async def test_create_user_with_roles_success(security_manager: SecurityManager, mock_session: AsyncMock, sample_viewer_role: Role):
    """Test successfully creating a user with roles assigned."""
    dto = UserCreateData(
        username="newuser",
        password="ValidPassword1",
        confirm_password="ValidPassword1",
        full_name="New User",
        email="new@user.com",
        is_active=True,
        assigned_role_ids=[sample_viewer_role.id],
        user_id=99 # Admin user performing action
    )
    
    # Mock checks: no existing user, role exists
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None # No existing user
    mock_execute_result.scalars.return_value.all.return_value = [sample_viewer_role] # Role lookup finds it
    mock_session.execute.return_value = mock_execute_result

    # Mock refresh to simulate DB setting ID
    async def mock_refresh(obj, attribute_names=None): obj.id = 10
    mock_session.refresh.side_effect = mock_refresh
    
    result = await security_manager.create_user_with_roles(dto)
    
    assert result.is_success
    assert result.value is not None
    assert result.value.id == 10
    assert result.value.username == "newuser"
    assert len(result.value.roles) == 1
    assert result.value.roles[0].name == "Viewer"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    
async def test_has_permission_as_admin(security_manager: SecurityManager, sample_user_orm: User, sample_admin_role: Role):
    """Test that a user with the Administrator role has all permissions."""
    sample_user_orm.roles = [sample_admin_role]
    security_manager.current_user = sample_user_orm
    
    assert security_manager.has_permission("ANY_PERMISSION_CODE") is True

async def test_has_permission_specific_role(security_manager: SecurityManager, sample_user_orm: User, sample_viewer_role: Role):
    """Test permission check for a user with specific, non-admin roles."""
    sample_user_orm.roles = [sample_viewer_role]
    security_manager.current_user = sample_user_orm
    
    assert security_manager.has_permission("ACCOUNT_VIEW") is True
    assert security_manager.has_permission("ACCOUNT_CREATE") is False # Viewer role doesn't have this
    assert security_manager.has_permission("NON_EXISTENT_PERM") is False

async def test_has_permission_no_user(security_manager: SecurityManager):
    """Test that has_permission returns False when no user is logged in."""
    security_manager.current_user = None
    assert security_manager.has_permission("ANY_PERMISSION") is False
