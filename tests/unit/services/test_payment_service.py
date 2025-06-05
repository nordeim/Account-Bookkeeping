# File: tests/unit/services/test_payment_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.business_services import PaymentService
from app.models.business.payment import Payment, PaymentAllocation
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.bank_account import BankAccount
from app.models.accounting.currency import Currency
from app.models.accounting.journal_entry import JournalEntry
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import PaymentSummaryData
from app.common.enums import PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum, InvoiceStatusEnum
import logging

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_app_core() -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def payment_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> PaymentService:
    return PaymentService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_customer_orm() -> Customer:
    return Customer(id=1, name="Test Customer Inc.", customer_code="CUST001", created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_vendor_orm() -> Vendor:
    return Vendor(id=2, name="Test Vendor Ltd.", vendor_code="VEND001", created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_payment_orm(sample_customer_orm: Customer) -> Payment:
    return Payment(
        id=1, payment_no="PAY001", 
        payment_type=PaymentTypeEnum.CUSTOMER_PAYMENT.value,
        payment_method=PaymentMethodEnum.BANK_TRANSFER.value,
        payment_date=date(2023, 5, 15),
        entity_type=PaymentEntityTypeEnum.CUSTOMER.value,
        entity_id=sample_customer_orm.id,
        amount=Decimal("100.00"), currency_code="SGD",
        status=PaymentStatusEnum.DRAFT.value,
        created_by_user_id=1, updated_by_user_id=1,
        allocations=[] # Assuming no allocations by default for simplicity in some tests
    )

# --- Test Cases ---

async def test_get_payment_by_id_found(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_payment_orm
    result = await payment_service.get_by_id(1)
    assert result == sample_payment_orm
    assert result is not None # For mypy
    assert result.payment_no == "PAY001"
    mock_session.execute.assert_awaited_once()

async def test_get_payment_by_id_not_found(payment_service: PaymentService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    result = await payment_service.get_by_id(99)
    assert result is None

async def test_get_all_payments(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_payment_orm]
    result = await payment_service.get_all()
    assert len(result) == 1
    assert result[0].payment_no == "PAY001"

async def test_get_by_payment_no_found(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_payment_orm
    result = await payment_service.get_by_payment_no("PAY001")
    assert result is not None
    assert result.id == 1

async def test_get_all_summary_no_filters(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_row_mapping = MagicMock()
    mock_row_mapping._asdict.return_value = {
        "id": sample_payment_orm.id, "payment_no": sample_payment_orm.payment_no,
        "payment_date": sample_payment_orm.payment_date, "payment_type": sample_payment_orm.payment_type,
        "payment_method": sample_payment_orm.payment_method, "entity_type": sample_payment_orm.entity_type,
        "entity_id": sample_payment_orm.entity_id, "amount": sample_payment_orm.amount,
        "currency_code": sample_payment_orm.currency_code, "status": sample_payment_orm.status,
        "entity_name": "Test Customer Inc." # This would be result of subquery in real scenario
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row_mapping]
    
    summaries = await payment_service.get_all_summary()
    assert len(summaries) == 1
    assert isinstance(summaries[0], PaymentSummaryData)
    assert summaries[0].payment_no == "PAY001"
    assert summaries[0].entity_name == "Test Customer Inc."

async def test_save_new_payment(payment_service: PaymentService, mock_session: AsyncMock, sample_customer_orm: Customer):
    new_payment = Payment(
        payment_type=PaymentTypeEnum.CUSTOMER_PAYMENT.value,
        payment_method=PaymentMethodEnum.CASH.value,
        payment_date=date(2023, 6, 1),
        entity_type=PaymentEntityTypeEnum.CUSTOMER.value,
        entity_id=sample_customer_orm.id,
        amount=Decimal("50.00"), currency_code="SGD",
        status=PaymentStatusEnum.DRAFT.value,
        created_by_user_id=1, updated_by_user_id=1
    )
    # Simulate ORM refresh after save
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 2 # Simulate ID generation
        obj.payment_no = "PAY002" # Simulate sequence/logic setting this
        if attribute_names and 'allocations' in attribute_names:
            obj.allocations = [] # Simulate allocations list refresh
    mock_session.refresh.side_effect = mock_refresh

    result = await payment_service.save(new_payment)
    
    mock_session.add.assert_called_once_with(new_payment)
    mock_session.flush.assert_awaited_once()
    # Refresh is called twice if allocations is not None
    mock_session.refresh.assert_any_call(new_payment)
    if hasattr(new_payment, 'allocations') and new_payment.allocations is not None :
        mock_session.refresh.assert_any_call(new_payment, attribute_names=['allocations'])
    
    assert result.id == 2
    assert result.payment_no == "PAY002"

async def test_save_updated_payment(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    sample_payment_orm.reference = "Updated Ref"
    
    result = await payment_service.save(sample_payment_orm)
    
    mock_session.add.assert_called_once_with(sample_payment_orm)
    assert result.reference == "Updated Ref"

async def test_delete_draft_payment_success(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    sample_payment_orm.status = PaymentStatusEnum.DRAFT.value # Ensure it's draft
    mock_session.get.return_value = sample_payment_orm
    
    deleted = await payment_service.delete(1)
    assert deleted is True
    mock_session.get.assert_awaited_once_with(Payment, 1)
    mock_session.delete.assert_awaited_once_with(sample_payment_orm)

async def test_delete_non_draft_payment_fails(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    sample_payment_orm.status = PaymentStatusEnum.APPROVED.value # Not draft
    mock_session.get.return_value = sample_payment_orm
    
    deleted = await payment_service.delete(1)
    assert deleted is False
    mock_session.get.assert_awaited_once_with(Payment, 1)
    mock_session.delete.assert_not_called()
    # Check logger warning if app_core.logger was properly injected and used in service
    payment_service.logger.warning.assert_called_once()


async def test_delete_payment_not_found(payment_service: PaymentService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    deleted = await payment_service.delete(99)
    assert deleted is False
