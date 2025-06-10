<think>
Here's a thinking process that leads to the final response:

1.  **Deconstruct the Request:** I'll break down the user's request into clear, actionable steps.
    *   **Task 1: Review Existing Tests:** Carefully analyze the provided `tests/unit/` files (`test_tax_calculator.py`, `test_gst_manager.py`, `test_pydantic_models_journal_entry.py`, etc.). The goal is to understand *what* is already being tested and *how*.
    *   **Task 2: Identify Gaps:** Based on the full codebase review from the previous turn and the existing tests, identify significant missing test coverage. This is the most critical analytical step. I need to think about which modules are complex, which are critical to data integrity, and which currently have no tests.
    *   **Task 3: Create Missing Test Files:** Write new, high-quality unit test files to fill the identified gaps. These tests should follow the established patterns (pytest, asyncio, mocking dependencies, fixture usage).
    *   **Task 4: Update the Test Guide:** Take the provided draft `project_test_guide (draft - to validate and update).md` and create a *complete, updated replacement*. This means not just adding to it, but rewriting it to be comprehensive, accurate based on the *newly expanded* test suite, and providing clear, professional guidance.

2.  **Execution - Step 1: Review Existing Tests (Mental Scan & Analysis)**
    *   `test_tax_calculator.py`: Good coverage of the `TaxCalculator` class. It uses mocked services (`TaxCodeService`) effectively.
    *   `test_gst_manager.py`: Tests the `GSTManager`. It's a good start, covering `prepare_gst_return_data` and `finalize_gst_return`. It uses multiple mocks (`mock_journal_service`, `mock_company_settings_service`, etc.), which is the correct approach for a manager class.
    *   `test_pydantic_models_journal_entry.py`: Excellent, very focused test on the validation rules within Pydantic DTOs for `JournalEntry` and `JournalEntryLine`. This is a good pattern to follow.
    *   `test_sequence_generator.py`: Very thorough test for the `SequenceGenerator`, covering both the primary DB function path and the Python fallback logic, including edge cases like cycling and max value.
    *   `services/` tests (`test_payment_service.py`, `test_sales_invoice_service.py`, etc.): There's a good set of tests for the service layer. They correctly mock the database session and test the service's methods (get, save, delete logic). This is a solid foundation.
    *   `reporting/` tests (`test_dashboard_manager.py`, `test_financial_statement_generator.py`): These exist and test the high-level logic of these managers. They mock the underlying services to provide data.
    *   **Conclusion on Existing Tests:** The current test suite focuses heavily on the `services` layer and some specific `utils` and `tax` components. It establishes a clear pattern of using `pytest` with `asyncio` and extensive mocking.

3.  **Execution - Step 2: Identify Testing Gaps**
    *   **Business Logic Layer (Managers):** This is the biggest gap. While `GSTManager`, `DashboardManager`, and `FinancialStatementGenerator` have some tests, the core business process managers are largely untested. These are critical because they orchestrate multiple services and contain complex business rules.
        *   `CustomerManager`: No tests.
        *   `VendorManager`: No tests.
        *   `ProductManager`: No tests.
        *   `BankAccountManager`: No tests.
        *   `SalesInvoiceManager`: No tests for its complex orchestration (e.g., `post_invoice`).
        *   `PurchaseInvoiceManager`: No tests.
        *   `PaymentManager`: No tests.
    *   **Accounting Logic Layer (Managers):**
        *   `ChartOfAccountsManager`: No tests.
        *   `JournalEntryManager`: No tests for its complex logic like `reverse_journal_entry`.
        *   `FiscalPeriodManager`: No tests.
    *   **Core Components:**
        *   `SecurityManager`: Critical component with complex logic (authentication, password hashing, roles, permissions) but *no tests*. This is a high-priority gap.
        *   `ApplicationCore`: Testing this directly is tricky, but we can test its setup or specific properties if needed. For now, testing the managers that rely on it is more valuable.
    *   **UI Layer:** The prompt acknowledges this is a future task, so I won't create UI tests, but I will mention it in the updated guide.
    *   **Integration Tests:** Also acknowledged as a future task.

4.  **Execution - Step 3: Create Missing Test Files (Plan & Write)**
    *   **Strategy:** I'll focus on the highest-impact gaps first: the business logic managers and `SecurityManager`. I will create one new test file for each manager to demonstrate the pattern.
    *   **File to create #1: `tests/unit/business_logic/test_customer_manager.py`**
        *   **Goal:** Test `CustomerManager`.
        *   **Fixtures:** Need `mock_customer_service`, `mock_account_service`, `mock_currency_service`, `mock_app_core`.
        *   **Test Cases:**
            *   `test_create_customer_success`: Provide valid DTO, mock service calls, assert `Result.is_success`.
            *   `test_create_customer_validation_fails`: Test cases where validation should fail (e.g., duplicate code, invalid account ID). Assert `Result.is_failure` and check error messages.
            *   `test_update_customer_success`: Similar to create.
            *   `test_toggle_customer_active_status`: Test activating and deactivating.
    *   **File to create #2: `tests/unit/core/test_security_manager.py`**
        *   **Goal:** Test `SecurityManager`. This is super important.
        *   **Fixtures:** Need `mock_db_manager` and its underlying `mock_session`.
        *   **Test Cases:**
            *   `test_hash_and_verify_password`: A simple non-async test to ensure bcrypt logic is sound.
            *   `test_authenticate_user_success`: Mock `session.execute` to return a valid, active user with a correct password hash. Assert a `User` object is returned.
            *   `test_authenticate_user_wrong_password`: Mock the user lookup but fail the `verify_password` check. Assert `None` is returned.
            *   `test_authenticate_user_inactive`: Mock an inactive user. Assert `None` is returned.
            *   `test_create_user_with_roles`: Test the user creation logic, including role assignment. Mock `session.execute` to check for existing users and fetch roles.
            *   `test_has_permission`: Create mock users with different roles and permissions and test the RBAC logic.
    *   **File to create #3: `tests/unit/accounting/test_journal_entry_manager.py`**
        *   **Goal:** Test `JournalEntryManager`.
        *   **Fixtures:** `mock_journal_service`, `mock_account_service`, `mock_fiscal_period_service`, `mock_app_core`.
        *   **Test Cases:**
            *   `test_create_journal_entry_success`: Valid DTO, mock services, assert success.
            *   `test_create_journal_entry_no_open_period`: Mock `fiscal_period_service` to return `None`. Assert failure.
            *   `test_post_journal_entry_success`: Mock `get` for the JE, check for `is_posted` update.
            *   `test_post_journal_entry_already_posted`: Mock a posted JE, assert failure.
            *   `test_reverse_journal_entry`: This is a key one. Mock the original posted JE. Mock the `create_journal_entry` call that the reversal makes. Assert the original JE is marked `is_reversed` and that a new reversal JE is created.

    *   **Code Generation:** I will now write the full code for these new files, following the established style. I'll use `AsyncMock`, `MagicMock`, Pydantic DTOs for inputs, and the `Result` object for outputs, just like the existing tests. I'll add docstrings and clear assertions.

5.  **Execution - Step 4: Update the Test Guide**
    *   **Goal:** Create a complete replacement for `project_test_guide (draft - to validate and update).md`.
    *   **Review the Draft:** The draft is a good starting point but is now incomplete because of the new tests I'm adding. The structure is solid.
    *   **Update Section 2 (Test Structure):** This is the main section to update.
        *   I will add entries for the new directories I'm creating: `tests/unit/business_logic/`, `tests/unit/accounting/`, and `tests/unit/core/`.
        *   For each new entry, I'll describe its purpose (e.g., "Unit tests for business process orchestrators like `CustomerManager`...").
        *   I'll update the descriptions of existing directories to be more precise based on my review. For example, I'll explicitly mention `GSTManager` in the `tax/` description.
    *   **Update Section 5 (Writing New Tests):** I will add a point about testing "Manager" classes. I'll emphasize the need to mock the *service layer* dependencies, not the database directly, to test the manager's orchestration logic in isolation. This is a key architectural point that should be reflected in the testing guide.
    *   **General Polish:** I will review the entire document for clarity, accuracy, and tone. I will remove the "(draft - to validate and update)" part from the title. I will remove the placeholder URLs at the end. The final document should look like an official, polished piece of project documentation.

6.  **Final Review:** I will read through the entire response one last time.
    *   Does it provide the new test files as requested? Yes.
    *   Are the new test files well-written and do they follow the project's testing style? Yes.
    *   Is the updated `project_test_guide.md` a complete replacement file? Yes.
    *   Is the guide accurate and reflective of the *new, expanded* test suite? Yes.
    *   Is the overall response structured clearly, with introductory text, the new files, and the final guide? Yes.

This systematic process ensures all parts of the user's request are met with high quality and accuracy, building on the established context of the project.Of course. I have conducted a thorough review of the existing test suite and the application's source code to identify key areas for expanded test coverage.

The current tests provide a solid foundation, particularly for the service layer (data access) and some utilities. However, there are significant gaps in the unit testing of the **Business Logic Layer** (Managers) and critical **Core** components like the `SecurityManager`. These manager classes contain the application's primary orchestration and business rule logic, making them a high-priority target for testing to ensure correctness and prevent regressions.

To address this, I have created three new test files that target some of the most critical untested areas:

1.  **`tests/unit/core/test_security_manager.py`**: A crucial new test suite for the `SecurityManager`, covering authentication, password hashing, and user/role creation logic.
2.  **`tests/unit/business_logic/test_customer_manager.py`**: A representative test suite for a business logic manager, demonstrating how to test creation, validation, and status updates for a core business entity.
3.  **`tests/unit/accounting/test_journal_entry_manager.py`**: A test suite for the `JournalEntryManager`, focusing on its complex orchestration logic, such as posting and reversing entries.

These new files follow the established patterns of using `pytest`, `asyncio`, and extensive mocking to test components in isolation.

Following the new test files, you will find the complete, updated replacement for the `project_test_guide.md`.

***

### New Test Files

Here are the new test files to be added to the project to enhance test coverage.

#### **File to be created:** `tests/unit/core/test_security_manager.py`

```python
# tests/unit/core/test_security_manager.py
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

```

#### **File to be created:** `tests/unit/business_logic/test_customer_manager.py`

```python
# tests/unit/business_logic/test_customer_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date

from app.business_logic.customer_manager import CustomerManager
from app.services.business_services import CustomerService
from app.services.account_service import AccountService
from app.services.accounting_services import CurrencyService
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData
from app.utils.result import Result
from app.models.business.customer import Customer
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency as CurrencyModel
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_customer_service() -> AsyncMock: return AsyncMock(spec=CustomerService)

@pytest.fixture
def mock_account_service() -> AsyncMock: return AsyncMock(spec=AccountService)

@pytest.fixture
def mock_currency_service() -> AsyncMock: return AsyncMock(spec=CurrencyService)

@pytest.fixture
def mock_app_core() -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def customer_manager(
    mock_customer_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_currency_service: AsyncMock,
    mock_app_core: MagicMock
) -> CustomerManager:
    return CustomerManager(
        customer_service=mock_customer_service,
        account_service=mock_account_service,
        currency_service=mock_currency_service,
        app_core=mock_app_core
    )

@pytest.fixture
def valid_customer_create_dto() -> CustomerCreateData:
    return CustomerCreateData(
        customer_code="CUST-01", name="Test Customer",
        currency_code="SGD", user_id=1, receivables_account_id=101
    )

@pytest.fixture
def sample_ar_account() -> Account:
    return Account(id=101, code="1120", name="A/R", account_type="Asset", is_active=True, created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_currency() -> CurrencyModel:
    return CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$", is_active=True)

# --- Test Cases ---

async def test_create_customer_success(
    customer_manager: CustomerManager,
    mock_customer_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_currency_service: AsyncMock,
    valid_customer_create_dto: CustomerCreateData,
    sample_ar_account: Account,
    sample_currency: CurrencyModel
):
    # Setup mocks for validation pass
    mock_customer_service.get_by_code.return_value = None
    mock_account_service.get_by_id.return_value = sample_ar_account
    mock_currency_service.get_by_id.return_value = sample_currency
    # Mock the final save call
    async def mock_save(customer_orm):
        customer_orm.id = 1 # Simulate DB assigning an ID
        return customer_orm
    mock_customer_service.save.side_effect = mock_save

    result = await customer_manager.create_customer(valid_customer_create_dto)

    assert result.is_success
    assert result.value is not None
    assert result.value.id == 1
    assert result.value.customer_code == "CUST-01"
    mock_customer_service.save.assert_awaited_once()

async def test_create_customer_duplicate_code(
    customer_manager: CustomerManager,
    mock_customer_service: AsyncMock,
    valid_customer_create_dto: CustomerCreateData
):
    # Simulate that a customer with this code already exists
    mock_customer_service.get_by_code.return_value = Customer(id=99, customer_code="CUST-01", name="Existing", created_by_user_id=1, updated_by_user_id=1)

    result = await customer_manager.create_customer(valid_customer_create_dto)

    assert not result.is_success
    assert "already exists" in result.errors[0]
    mock_customer_service.save.assert_not_called()

async def test_create_customer_inactive_ar_account(
    customer_manager: CustomerManager,
    mock_customer_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_currency_service: AsyncMock,
    valid_customer_create_dto: CustomerCreateData,
    sample_ar_account: Account,
    sample_currency: CurrencyModel
):
    sample_ar_account.is_active = False # Make the account inactive
    mock_customer_service.get_by_code.return_value = None
    mock_account_service.get_by_id.return_value = sample_ar_account
    mock_currency_service.get_by_id.return_value = sample_currency

    result = await customer_manager.create_customer(valid_customer_create_dto)

    assert not result.is_success
    assert "is not active" in result.errors[0]

async def test_update_customer_success(customer_manager: CustomerManager, mock_customer_service: AsyncMock):
    update_dto = CustomerUpdateData(
        id=1, customer_code="C-001", name="Updated Name", currency_code="SGD", user_id=1
    )
    existing_customer = Customer(id=1, customer_code="C-001", name="Original Name", created_by_user_id=1, updated_by_user_id=1)
    
    # Mock validation dependencies
    customer_manager._validate_customer_data = AsyncMock(return_value=[])
    # Mock service layer get and save
    mock_customer_service.get_by_id.return_value = existing_customer
    mock_customer_service.save.side_effect = lambda orm: orm # Return the modified object

    result = await customer_manager.update_customer(1, update_dto)
    
    assert result.is_success
    assert result.value is not None
    assert result.value.name == "Updated Name"
    assert result.value.updated_by_user_id == 1
    mock_customer_service.save.assert_awaited_once_with(existing_customer)

async def test_toggle_customer_status(customer_manager: CustomerManager, mock_customer_service: AsyncMock):
    existing_customer = Customer(id=1, name="Toggle Test", is_active=True, created_by_user_id=1, updated_by_user_id=1)
    mock_customer_service.get_by_id.return_value = existing_customer
    mock_customer_service.save.side_effect = lambda orm: orm
    
    # Deactivate
    result_deactivate = await customer_manager.toggle_customer_active_status(1, user_id=2)
    assert result_deactivate.is_success
    assert result_deactivate.value.is_active is False
    assert result_deactivate.value.updated_by_user_id == 2
    
    # Activate again
    result_activate = await customer_manager.toggle_customer_active_status(1, user_id=3)
    assert result_activate.is_success
    assert result_activate.value.is_active is True
    assert result_activate.value.updated_by_user_id == 3

```

#### **File to be created:** `tests/unit/accounting/test_journal_entry_manager.py`

```python
# tests/unit/accounting/test_journal_entry_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date

from app.accounting.journal_entry_manager import JournalEntryManager
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData
from app.utils.result import Result
from app.models.accounting.journal_entry import JournalEntry
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.account import Account
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_journal_service() -> AsyncMock: return AsyncMock(spec=JournalService)

@pytest.fixture
def mock_account_service() -> AsyncMock: return AsyncMock(spec=AccountService)

@pytest.fixture
def mock_fiscal_period_service() -> AsyncMock: return AsyncMock(spec=FiscalPeriodService)

@pytest.fixture
def mock_app_core() -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.db_manager = MagicMock()
    app_core.db_manager.execute_scalar = AsyncMock()
    return app_core

@pytest.fixture
def journal_entry_manager(
    mock_journal_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_fiscal_period_service: AsyncMock,
    mock_app_core: MagicMock
) -> JournalEntryManager:
    return JournalEntryManager(
        journal_service=mock_journal_service,
        account_service=mock_account_service,
        fiscal_period_service=mock_fiscal_period_service,
        app_core=mock_app_core
    )

@pytest.fixture
def valid_je_create_dto() -> JournalEntryData:
    return JournalEntryData(
        journal_type="General",
        entry_date=date(2023, 1, 20),
        description="Test Entry",
        user_id=1,
        lines=[
            JournalEntryLineData(account_id=101, debit_amount=Decimal("150.00")),
            JournalEntryLineData(account_id=201, credit_amount=Decimal("150.00")),
        ]
    )

@pytest.fixture
def sample_posted_je() -> JournalEntry:
    je = JournalEntry(
        id=5, entry_no="JE-POSTED-01", entry_date=date(2023,1,10), is_posted=True, created_by_user_id=1, updated_by_user_id=1, fiscal_period_id=1
    )
    je.lines = [
        JournalEntryLine(id=10, account_id=101, debit_amount=Decimal(100)),
        JournalEntryLine(id=11, account_id=201, credit_amount=Decimal(100))
    ]
    return je

# --- Test Cases ---

async def test_create_journal_entry_success(
    journal_entry_manager: JournalEntryManager,
    mock_fiscal_period_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_app_core: MagicMock,
    valid_je_create_dto: JournalEntryData
):
    # Setup mocks for validation pass
    mock_fiscal_period_service.get_by_date.return_value = FiscalPeriod(id=1, name="Jan 2023", start_date=date(2023,1,1), end_date=date(2023,1,31), period_type="Month", status="Open", period_number=1, created_by_user_id=1, updated_by_user_id=1)
    mock_account_service.get_by_id.side_effect = lambda id: Account(id=id, is_active=True, code=str(id), name=f"Acc {id}", account_type="Asset", created_by_user_id=1, updated_by_user_id=1)
    mock_app_core.db_manager.execute_scalar.return_value = "JE00001"
    
    # Mock the final save call
    async def mock_save(je_orm):
        je_orm.id = 1 # Simulate DB assigning an ID
        return je_orm
    # The manager doesn't call service.save, it works with the session directly
    # So we need to mock the session on the db_manager used inside create_journal_entry
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    journal_entry_manager.app_core.db_manager.session.return_value.__aenter__.return_value = mock_session

    result = await journal_entry_manager.create_journal_entry(valid_je_create_dto)

    assert result.is_success
    assert result.value is not None
    assert result.value.entry_no == "JE00001"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()

async def test_create_journal_entry_no_open_period(journal_entry_manager: JournalEntryManager, mock_fiscal_period_service: AsyncMock, valid_je_create_dto: JournalEntryData):
    mock_fiscal_period_service.get_by_date.return_value = None
    mock_session = AsyncMock()
    journal_entry_manager.app_core.db_manager.session.return_value.__aenter__.return_value = mock_session

    result = await journal_entry_manager.create_journal_entry(valid_je_create_dto)

    assert not result.is_success
    assert "No open fiscal period" in result.errors[0]

async def test_post_journal_entry_success(journal_entry_manager: JournalEntryManager, mock_session: AsyncMock, sample_posted_je: JournalEntry):
    sample_posted_je.is_posted = False # Start as draft for the test
    mock_session.get.side_effect = [
        sample_posted_je, # First get for the JE itself
        FiscalPeriod(id=1, status="Open") # Second get for the fiscal period
    ]

    result = await journal_entry_manager.post_journal_entry(5, user_id=1, session=mock_session)
    
    assert result.is_success
    assert result.value.is_posted is True
    assert result.value.updated_by_user_id == 1
    mock_session.add.assert_called_once_with(sample_posted_je)
    
async def test_reverse_journal_entry_success(journal_entry_manager: JournalEntryManager, mock_session: AsyncMock, sample_posted_je: JournalEntry):
    # Setup
    mock_session.get.return_value = sample_posted_je
    mock_fiscal_period_service = journal_entry_manager.fiscal_period_service
    mock_fiscal_period_service.get_by_date.return_value = FiscalPeriod(id=2, status="Open") # Mock for reversal date's period
    journal_entry_manager.app_core.db_manager.execute_scalar.return_value = "JE-REV-01" # Mock sequence for reversal JE

    # Mock the create_journal_entry call within the reversal method
    reversal_je_mock = MagicMock(spec=JournalEntry, id=6)
    journal_entry_manager.create_journal_entry = AsyncMock(return_value=Result.success(reversal_je_mock))

    reversal_date = date(2023, 2, 1)
    reversal_desc = "Reversal"
    user_id = 2

    # Execute
    result = await journal_entry_manager.reverse_journal_entry(sample_posted_je.id, reversal_date, reversal_desc, user_id)
    
    # Assert
    assert result.is_success
    assert result.value == reversal_je_mock
    # Check that original entry was modified
    assert sample_posted_je.is_reversed is True
    assert sample_posted_je.reversing_entry_id == 6
    assert sample_posted_je.updated_by_user_id == 2
    # Check that the create call was correct
    create_call_args = journal_entry_manager.create_journal_entry.call_args.args[0]
    assert isinstance(create_call_args, JournalEntryData)
    assert create_call_args.lines[0].credit_amount == sample_posted_je.lines[0].debit_amount
    assert create_call_args.lines[1].debit_amount == sample_posted_je.lines[1].credit_amount

```

***

### Updated Project Test Guide

Here is the complete and updated replacement for the `project_test_guide.md` file.

***

# Project Test Guide: SG Bookkeeper

This guide provides instructions on how to set up the testing environment and run the automated tests for the SG Bookkeeper application. A comprehensive test suite is crucial for maintaining code quality, ensuring correctness of business logic, and preventing regressions.

## 1. Prerequisites

*   **Python Environment**: Ensure you have Python (version specified in `pyproject.toml`, e.g., 3.9+) and Poetry installed.
*   **Dependencies**: All development dependencies, including testing libraries (`pytest`, `pytest-asyncio`, `pytest-cov`, `unittest.mock`), should be installed. If you set up the project using `poetry install --with dev` (recommended) or `poetry install` (if dev dependencies are not in a separate group), these should already be available in your project's virtual environment.

## 2. Test Structure

The tests are organized within the `tests/` root directory, mirroring the application's structure to facilitate navigation and maintenance.

*   **`tests/conftest.py`**:
    *   This file is used for project-wide pytest fixtures and configuration. It might contain shared setup/teardown logic or helper fixtures accessible by all tests.

*   **`tests/unit/`**:
    *   Contains unit tests designed to test individual modules, classes, or functions in isolation. These tests heavily utilize mocks for external dependencies (like services or the database) to ensure the component's logic is tested independently.
    *   Subdirectories further organize these tests by application module:
        *   `core/`: Unit tests for critical core components, such as the `SecurityManager`.
        *   `accounting/`: Unit tests for accounting-related business logic managers, like the `JournalEntryManager`.
        *   `business_logic/`: Unit tests for core business process orchestrators, such as the `CustomerManager`.
        *   `tax/`: Unit tests for tax-related components (e.g., `TaxCalculator`, `GSTManager`).
        *   `utils/`: Unit tests for utility classes (e.g., `SequenceGenerator`) and validation rules in Pydantic models.
        *   `services/`: A comprehensive suite of tests for the data access layer classes (e.g., `AccountService`, `BankReconciliationService`, `CustomerService`, etc.).
        *   `reporting/`: Unit tests for reporting logic components (e.g., `DashboardManager`, `FinancialStatementGenerator`).

*   **`tests/integration/`**:
    *   Contains integration tests that verify interactions between multiple components. These tests might involve a real (test) database to ensure components work together correctly.
    *   Currently, a basic structure exists, with more comprehensive integration tests planned.

*   **`tests/ui/`**:
    *   Intended for UI-level functional tests, likely using frameworks like `pytest-qt`.
    *   Currently, a basic structure exists, with UI test implementation planned for the future.

## 3. Running Tests

All tests are run using `pytest` from the root directory of the project. Ensure your Poetry virtual environment is activated (e.g., by running `poetry shell` in the project root) or prepend commands with `poetry run`.

### 3.1. Running All Tests

To run all discovered tests (unit, integration, UI):

```bash
poetry run pytest
```

Or, if your Poetry shell is activated:

```bash
pytest
```

### 3.2. Running Specific Test Files or Directories

You can target specific parts of the test suite:

*   Run all tests in a directory (e.g., `tests/unit/services/`):
    ```bash
    poetry run pytest tests/unit/services/
    ```
*   Run a specific test file (e.g., `tests/unit/tax/test_tax_calculator.py`):
    ```bash
    poetry run pytest tests/unit/tax/test_tax_calculator.py
    ```
*   Run a specific test function within a file using `::test_function_name`:
    ```bash
    poetry run pytest tests/unit/core/test_security_manager.py::test_authenticate_user_success
    ```
*   Run tests based on markers (if defined in tests, e.g., `@pytest.mark.slow`):
    ```bash
    poetry run pytest -m slow
    ```

### 3.3. Test Verbosity

For more detailed output from pytest:

*   Show individual test names as they run:
    ```bash
    poetry run pytest -v
    ```
*   Show even more verbose output, including captured standard output from tests:
    ```bash
    poetry run pytest -vv
    ```

### 3.4. Test Coverage

To generate a test coverage report (requires the `pytest-cov` plugin, which is included in dev dependencies):

*   Print a coverage summary to the console for the `app` directory:
    ```bash
    poetry run pytest --cov=app tests/
    ```
*   Generate an HTML coverage report for a more detailed, browsable view:
    ```bash
    poetry run pytest --cov=app --cov-report=html tests/
    ```
    This will create an `htmlcov/` directory in your project root. Open `htmlcov/index.html` in a web browser to view the report.

### 3.5. Running Asynchronous Tests

Tests involving `async def` functions are automatically discovered and run by `pytest` when `pytest-asyncio` is installed (it is a dev dependency). `pytest-asyncio` is configured with `asyncio_mode = auto` in `pyproject.toml`, which handles most asynchronous test cases seamlessly.

## 4. Viewing Test Results

Pytest provides immediate feedback in the console:
*   `.` (dot): Indicates a passed test.
*   `F`: Indicates a test that failed an assertion.
*   `E`: Indicates an error occurred during test setup or execution (not an assertion failure).
*   `s`: Indicates a skipped test (e.g., marked with `@pytest.mark.skip` or `pytest.skip()`).
*   `x`: Indicates an "expected failure" (marked with `@pytest.mark.xfail`).

For `F` and `E` results, pytest will print detailed information, including tracebacks and assertion differences, to help diagnose the issue.

## 5. Writing New Tests

When adding new tests, adhere to the following conventions to maintain consistency and quality.

*   **Location**:
    *   Place new unit tests in the appropriate subdirectory under `tests/unit/`.
    *   Integration tests go into `tests/integration/`.
    *   UI tests go into `tests/ui/`.
*   **File Naming**: Test files must start with `test_` (e.g., `test_my_new_feature.py`).
*   **Function Naming**: Test functions must start with `test_` (e.g., `def test_specific_behavior():`).
*   **Class Naming**: If using classes to group tests, class names must start with `Test` (e.g., `class TestMyComponent:`).
*   **Fixtures**: Utilize `pytest` fixtures (defined in `conftest.py` or locally in test files) for setting up test preconditions and managing resources. This is the preferred way to provide mocked objects to tests.
*   **Mocking Strategy**:
    *   For **Service Layer** tests, mock the database session (`AsyncSession`) and its methods (`get`, `execute`, etc.).
    *   For **Manager Layer** tests, mock the *Service Layer* dependencies. Do not mock the database directly. The goal is to test the manager's orchestration and business logic in isolation from the data access implementation.
*   **Assertions**: Use standard Python `assert` statements for checks.
*   **Expected Exceptions**: To test for expected exceptions, use `with pytest.raises(ExceptionType):`.
*   **Asynchronous Tests**: For testing asynchronous code, define test functions with `async def`. Use `AsyncMock` from `unittest.mock` for mocking coroutines.

By following these guidelines, we aim to build and maintain a comprehensive and robust suite of automated tests, ensuring the quality and stability of the SG Bookkeeper application.

---
https://drive.google.com/file/d/14GI0Jpi1ZCxjckpC0WPEG7YNdf3D-Vfp/view?usp=sharing, https://drive.google.com/file/d/1FmPfEv5XKMhn3JaojHSvp_wmUe9jH_kz/view?usp=sharing, https://drive.google.com/file/d/1GTT2tW3WV4H-8oDTeYEbFnpHsHKleBnA/view?usp=sharing, https://drive.google.com/file/d/1GVnNEvV_JL-RfhiLcilpuTGpE_L2EVSB/view?usp=sharing, https://drive.google.com/file/d/1GWA2Cy5so8LafVd3hrehbWlnZtZCu96l/view?usp=sharing, https://drive.google.com/file/d/1Nc73m3B6VqapO6fKmQhZsz0XqBRC6qLx/view?usp=sharing, https://drive.google.com/file/d/1OFECl1W0TBgualvPFvzb1QC7TjbeS63t/view?usp=sharing, https://drive.google.com/file/d/1aUUJN_6Wzg62RWOOpSHepTTM8-906Nab/view?usp=sharing, https://drive.google.com/file/d/1c3LTmRz47pvqw6MkqE5akustMqGG384E/view?usp=sharing, https://drive.google.com/file/d/1fVRlxEjtkFpTafU6-MrRkTNhJ8ROqHRS/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221ky-GUobTN6gjyn85sXTPYJRKdg4YATwW%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1t_7xdLQGnvDNwIDz9JRwAlVdm0OjPIVR/view?usp=sharing

