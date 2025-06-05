<think>
The application is launching successfully, and the Dashboard KPIs, including AR/AP Aging and Current Ratio, are displayed correctly. The unit tests for `DashboardManager` and the new service methods (`CustomerService.get_ar_aging_summary`, `VendorService.get_ap_aging_summary`, `AccountService.get_total_balance_by_account_category_and_type_pattern`) have been created and validated.

We are continuing with the roadmap item: **"Automated Testing (Continued - CRITICAL)"**.
The immediate sub-task is to:
*   Expand unit test coverage to all remaining services (especially business services like `SalesInvoiceService`, `PaymentService`, remaining `BankAccountService`/`BankTransactionService` methods) and all managers.

From the previous step, I've provided tests for `SalesInvoiceService` and `PurchaseInvoiceService` and the new dashboard-related service methods.

Now, let's focus on creating unit tests for other key business services that were part of the provided codebase snippets and have significant logic or are critical to application flow. Good candidates are:
*   **`PaymentService`**
*   **`BankAccountService`** (expand on existing tests if any, cover all public methods)
*   **`BankTransactionService`** (expand on existing tests if any, cover all public methods)
*   **`InventoryMovementService`**

And then move to managers. For this iteration, I will focus on **`PaymentService`** first as it involves multiple related entities (Payments, Allocations, linking to Invoices, potential JEs).

**1. Deeply Understand Requirements for Testing `PaymentService`:**

*   **`PaymentService` Methods (from `app/services/business_services.py` in `project_codebase_files_set-4.md` and its interface in `app/services/__init__.py`):**
    *   `get_by_id(self, id_val: int) -> Optional[Payment]`: Test found, not found. Check eager loading of `allocations`, `bank_account`, etc.
    *   `get_all(self) -> List[Payment]`: Test returns list, empty list, order.
    *   `get_by_payment_no(self, payment_no: str) -> Optional[Payment]`: Test found, not found.
    *   `get_all_summary(...)`: Test various filters (`entity_type`, `entity_id`, `status`, date range), pagination (though current impl. is simplified), correct DTO structure.
    *   `save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment`: Test new payment, update payment. Check `session.add`, `flush`, `refresh`.
    *   `add(self, entity: Payment) -> Payment`: Delegates to `save`.
    *   `update(self, entity: Payment) -> Payment`: Delegates to `save`.
    *   `delete(self, id_val: int) -> bool`: Test deleting a "Draft" payment, test failure for non-draft.

**2. Systematic Diagnosis & Design Considerations for Tests:**

*   **Test File**: `tests/unit/services/test_payment_service.py`.
*   **Mocking**:
    *   `DatabaseManager` and `AsyncSession`.
    *   `session.execute()` for queries, `session.get()` for `get_by_id`.
    *   `ApplicationCore` (mocked) for logger if used.
*   **Fixtures**:
    *   `mock_session`, `mock_db_manager`, `mock_app_core`.
    *   Sample ORM objects: `Payment`, `PaymentAllocation`, `BankAccount`, `Currency`, `JournalEntry`, `Customer`, `Vendor`.
*   **Async Tests**: All tests `async def` and `@pytest.mark.asyncio`.
*   **Focus**: Test service logic, mock DB interactions.

**3. Implementation Options Exploration (Test Design):**

*   **`get_all_summary()`**: This is complex due to the `case` statement for `entity_name`.
    *   Mock `session.execute().mappings().all()` to return a list of `MagicMock` row objects where each row mock has an `_asdict()` method returning the dictionary structure expected by `PaymentSummaryData.model_validate()`.
    *   Test different `entity_type` values to ensure the `case` statement is covered (or at least that the DTO validation works).
*   **`save()`**:
    *   When saving a new `Payment`, simulate `session.refresh` setting the `id` and `payment_no` (if `payment_no` is DB-generated, though it seems to be set by manager).
    *   When saving an existing `Payment`, ensure updates are reflected.
    *   The `session` argument in `save()` is optional. Test both paths (with explicit session and without, relying on `db_manager.session()`).

**Chosen Implementation Strategy:**
Standard unit tests using `pytest` and `unittest.mock`. Create focused tests for each public method.

**Detailed Execution Plan & Checklist:**

**Phase 1: Unit Tests for `PaymentService`**
1.  **Create `tests/unit/services/test_payment_service.py`**:
    *   Checklist for methods:
        *   [ ] `test_get_payment_by_id_found()`: Mock `session.execute().scalars().first()` to return a `Payment` ORM. Assert correct object and eager loads.
        *   [ ] `test_get_payment_by_id_not_found()`: Mock return `None`.
        *   [ ] `test_get_all_payments_returns_list()`: Mock `session.execute().scalars().all()`. Check list and order.
        *   [ ] `test_get_all_payments_returns_empty_list()`.
        *   [ ] `test_get_payment_by_payment_no_found()`: Mock `session.execute().scalars().first()`.
        *   [ ] `test_get_payment_by_payment_no_not_found()`.
        *   [ ] `test_get_all_summary_no_filters()`: Mock `session.execute().mappings().all()`. Verify DTO conversion and basic data.
        *   [ ] `test_get_all_summary_with_entity_type_filter()`: Test with `CUSTOMER` and `VENDOR`.
        *   [ ] `test_get_all_summary_with_status_filter()`.
        *   [ ] `test_get_all_summary_with_date_filters()`.
        *   [ ] `test_save_new_payment()`: Mock `session.add, flush, refresh`. Check if object is returned with simulated ID.
        *   [ ] `test_save_updated_payment()`: Fetch mock, modify, save, check updates.
        *   [ ] `test_delete_draft_payment_success()`: Mock `session.get` to return a draft payment, mock `session.delete`.
        *   [ ] `test_delete_non_draft_payment_fails()`: Mock `session.get` to return an approved payment. Check logger warning and `False` return.
        *   [ ] `test_delete_payment_not_found()`.

This plan targets `PaymentService`. After this, I will evaluate the next service from the list (e.g., `BankAccountService`) or await user feedback.

I will now generate the `tests/unit/services/test_payment_service.py` file.
</think>

Excellent, the application is running smoothly with the enhanced dashboard. We are making great progress!

As per your direction, we will continue with the roadmap item: **"Automated Testing (Continued - CRITICAL)"**.
The plan is to expand unit test coverage for key business services. For this step, I will focus on creating unit tests for **`PaymentService`**. This service is crucial as it handles payment records and their allocations.

**Detailed Execution Plan & Checklist for `PaymentService` Unit Tests:**

1.  **Create Test File**: `tests/unit/services/test_payment_service.py`.
2.  **Setup Common Fixtures**:
    *   `mock_session`: An `AsyncMock` for `sqlalchemy.ext.asyncio.AsyncSession`.
    *   `mock_db_manager`: A `MagicMock` for `DatabaseManager`, configured to return `mock_session`.
    *   `mock_app_core`: A `MagicMock` for `ApplicationCore`, providing a mocked logger.
    *   `payment_service`: An instance of `PaymentService` initialized with mocked dependencies.
    *   Sample ORM Fixtures: `sample_payment_orm`, `sample_customer_orm`, `sample_vendor_orm` to simulate data returned from the database.
3.  **Implement Test Cases for each public method in `PaymentService`**:
    *   **`get_by_id()`**:
        *   Test case for when a `Payment` is found (mock `session.execute().scalars().first()` to return a payment).
        *   Test case for when a `Payment` is not found (mock return `None`).
        *   Verify that `selectinload` options are correctly applied in the query if possible (though direct query assertion is complex with mocks, focus on service behavior).
    *   **`get_all()`**:
        *   Test case for returning a list of `Payment` objects.
        *   Test case for returning an empty list.
        *   Verify ordering if specified in the service method.
    *   **`get_by_payment_no()`**:
        *   Test case for finding a `Payment` by its `payment_no`.
        *   Test case for not finding a `Payment`.
    *   **`get_all_summary()`**:
        *   Test case with no filters.
        *   Test cases for each filter: `entity_type`, `entity_id`, `status`, `start_date`, `end_date`.
        *   Test case for combined filters.
        *   Verify the structure and content of the returned `PaymentSummaryData` DTOs.
        *   Mock `session.execute().mappings().all()` to provide appropriate row data for `PaymentSummaryData.model_validate()`.
    *   **`save()` (covering `add` and `update`)**:
        *   Test saving a new `Payment` entity (mock `session.add, flush, refresh`; simulate ID and timestamp generation on `refresh`).
        *   Test updating an existing `Payment` entity.
        *   Test the optional `session` parameter: one test where it's provided, one where it's not (service uses its own).
    *   **`delete()`**:
        *   Test deleting a `Payment` that is in 'Draft' status (should succeed).
        *   Test attempting to delete a `Payment` that is not in 'Draft' status (should fail and log a warning).
        *   Test attempting to delete a non-existent `Payment` (should return `False`).

---
**1. New File: `tests/unit/services/test_payment_service.py`**
---
```python
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
```

