# File: tests/unit/business_logic/test_customer_manager.py
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
