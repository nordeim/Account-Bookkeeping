<think>
The application is stable, and recent feature enhancements (Bank Reconciliation drafts/unmatching, Dashboard KPIs, documentation updates) are complete and validated. The user now wants to proceed with the **"Automated Testing (Continued - CRITICAL)"** roadmap item.

Specifically, the focus is on:
1.  Expanding **unit test coverage** for remaining services and all managers.
2.  Beginning setup and implementation of **integration tests** for core workflows.

This is a substantial undertaking. For a single step, I should focus on a manageable chunk. Expanding unit tests for services is a good, incremental way to proceed.

**Chosen Focus for this Step: Unit Testing for Key Business Services**

Let's target a few key business services that haven't been explicitly tested yet, particularly those involved in core transactional flows. From the README and previous test file analysis, services like `SalesInvoiceService`, `PurchaseInvoiceService`, `PaymentService`, and further testing for `BankAccountService` and `BankTransactionService` (beyond what might have been touched by Bank Rec tests) are good candidates.

For this iteration, I will focus on creating unit tests for:
*   **`SalesInvoiceService`**
*   **`PurchaseInvoiceService`**

These are critical as they handle the creation, update, and retrieval of core financial documents.

**1. Deeply Understand Requirements for Testing these Services:**

*   **`SalesInvoiceService` / `PurchaseInvoiceService`**:
    *   **`get_by_id()`**: Test finding an invoice, not finding one. Ensure eager loading options are respected if they were specified (though unit tests often mock the direct return).
    *   **`get_all()`**: Test returning a list, empty list. Check ordering if specified.
    *   **`get_all_summary()`**: This is a key method for UI listings.
        *   Test with various filters: `customer_id`/`vendor_id`, `status`, date ranges.
        *   Test pagination (if `page` and `page_size` are effective, though the current service methods load all for `page_size = -1` which is fine for now).
        *   Verify the returned `SalesInvoiceSummaryData` / `PurchaseInvoiceSummaryData` DTOs have correct fields.
    *   **`get_by_invoice_no()` / `get_by_internal_ref_no()` / `get_by_vendor_and_vendor_invoice_no()`**: Test finding and not finding.
    *   **`save()` (and by extension `add()`/`update()`)**:
        *   Test that `session.add()`, `session.flush()`, `session.refresh()` are called.
        *   Verify the returned object is the one passed in (potentially with DB-generated ID/timestamps).
    *   **`delete()`**: Test successful deletion (for Drafts) and failure/exception for non-Drafts.
    *   **`get_outstanding_invoices_for_customer()` / `get_outstanding_invoices_for_vendor()` (for aging)**:
        *   Test with various invoice states (paid, partially paid, unpaid, voided, different due dates relative to `as_of_date`).
        *   Verify only correct invoices are returned.

**2. Systematic Diagnosis & Design Considerations for Tests:**

*   **Test File Structure**:
    *   `tests/unit/services/test_sales_invoice_service.py`
    *   `tests/unit/services/test_purchase_invoice_service.py`
*   **Mocking**:
    *   `DatabaseManager` and its `AsyncSession` will be mocked.
    *   `session.execute()` will be the primary mock target, configured to return `AsyncMock` instances that simulate SQLAlchemy's result objects (with `scalars().first()`, `scalars().all()`, `mappings().all()`).
    *   `session.get()` will be mocked for `get_by_id` tests.
    *   `ApplicationCore` (`app_core` argument to services) will be a `MagicMock`, primarily for the logger if used by the service.
*   **Fixtures**:
    *   Reusable `mock_session`, `mock_db_manager`, `mock_app_core`.
    *   Fixtures for sample ORM objects (`SalesInvoice`, `SalesInvoiceLine`, `PurchaseInvoice`, `PurchaseInvoiceLine`, `Customer`, `Vendor`).
*   **Async Tests**: All test methods will be `async def` and use `@pytest.mark.asyncio`.
*   **Focus**: Test the service logic, not SQLAlchemy's behavior. Assume SQLAlchemy works. Mock what SQLAlchemy would return.

**3. Implementation Options Exploration (Test Design):**

*   For methods like `get_all_summary` which build specific DTOs, ensure the mocked `session.execute().mappings().all()` returns data that can be correctly validated into these DTOs by the test.
*   When testing `save`, mock `session.refresh` to simulate how SQLAlchemy might update the passed-in ORM object (e.g., assign an ID, update timestamps).

**Chosen Implementation Strategy:**
Standard unit testing with `pytest` and `unittest.mock`. Create comprehensive test cases for each public method of the targeted services.

**Detailed Execution Plan & Checklist:**

**Phase 1: Setup Test Files and Common Fixtures**
1.  **Create Test Files**:
    *   Checklist:
        *   [ ] `tests/unit/services/test_sales_invoice_service.py`
        *   [ ] `tests/unit/services/test_purchase_invoice_service.py`
2.  **Common Fixtures (can be in individual files or `conftest.py`)**:
    *   Checklist:
        *   [ ] `mock_session`: `AsyncMock` for `AsyncSession`.
        *   [ ] `mock_db_manager`: `MagicMock` for `DatabaseManager`.
        *   [ ] `mock_app_core`: `MagicMock` for `ApplicationCore` (with mocked logger).
        *   [ ] Sample ORM object fixtures (e.g., `sample_customer`, `sample_sales_invoice_orm`, `sample_purchase_invoice_orm`). These should include related objects if the service method loads them (e.g., `SalesInvoice` with `Customer` for summary).

**Phase 2: Unit Tests for `SalesInvoiceService`**
1.  **Create `tests/unit/services/test_sales_invoice_service.py`**:
    *   Checklist for methods:
        *   [ ] `test_get_by_id_found()`
        *   [ ] `test_get_by_id_not_found()`
        *   [ ] `test_get_all_returns_list()`
        *   [ ] `test_get_all_returns_empty_list()`
        *   [ ] `test_get_all_summary_no_filters()`
        *   [ ] `test_get_all_summary_with_customer_filter()`
        *   [ ] `test_get_all_summary_with_status_filter()`
        *   [ ] `test_get_all_summary_with_date_filter()`
        *   [ ] `test_get_all_summary_combined_filters()`
        *   [ ] `test_get_all_summary_pagination()` (if pagination is fully implemented in service, current version fetches all if page_size < 0)
        *   [ ] `test_get_all_summary_returns_correct_dto_structure()`
        *   [ ] `test_get_by_invoice_no_found()`
        *   [ ] `test_get_by_invoice_no_not_found()`
        *   [ ] `test_save_new_invoice()` (covers `add`)
        *   [ ] `test_save_updated_invoice()` (covers `update`)
        *   [ ] `test_delete_invoice_not_supported()` (asserts `NotImplementedError`)
        *   [ ] `test_get_outstanding_invoices_for_customer_various_scenarios()` (multiple cases for aging)

**Phase 3: Unit Tests for `PurchaseInvoiceService`**
1.  **Create `tests/unit/services/test_purchase_invoice_service.py`**:
    *   Checklist for methods (similar to `SalesInvoiceService`):
        *   [ ] `test_get_by_id_found()`
        *   [ ] `test_get_by_id_not_found()`
        *   [ ] `test_get_all_returns_list()`
        *   [ ] `test_get_all_summary_no_filters()`
        *   [ ] `test_get_all_summary_with_vendor_filter()`
        *   [ ] `test_get_all_summary_with_status_filter()`
        *   [ ] `test_get_all_summary_with_date_filter()`
        *   [ ] `test_get_by_internal_ref_no_found()`
        *   [ ] `test_get_by_vendor_and_vendor_invoice_no_found()`
        *   [ ] `test_save_new_invoice()`
        *   [ ] `test_save_updated_invoice()`
        *   [ ] `test_delete_draft_invoice_success()`
        *   [ ] `test_delete_non_draft_invoice_fails()`
        *   [ ] `test_get_outstanding_invoices_for_vendor_various_scenarios()`

This is a good set of tests to start with for these two critical services.
I will generate these two new test files.
</think>

Excellent! The application is stable, and the dashboard enhancements are in place. Now, we will proceed with the critical roadmap item: **"Automated Testing (Continued - CRITICAL)"**.

As planned, we'll focus on expanding unit test coverage, starting with two key business services:
1.  **`SalesInvoiceService`**
2.  **`PurchaseInvoiceService`**

I will create new test files for these services in the `tests/unit/services/` directory. These tests will use `pytest` and `unittest.mock.AsyncMock` to mock dependencies like the database session and other services, allowing us to test the logic within each service method in isolation.

---
**1. New File: `tests/unit/services/test_sales_invoice_service.py`**
---
```python
# File: tests/unit/services/test_sales_invoice_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.business_services import SalesInvoiceService
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import SalesInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum
import logging # For logger spec

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
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
def sales_invoice_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> SalesInvoiceService:
    return SalesInvoiceService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_customer_orm() -> Customer:
    return Customer(id=1, customer_code="CUS001", name="Test Customer", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_sales_invoice_orm(sample_customer_orm: Customer) -> SalesInvoice:
    return SalesInvoice(
        id=1, invoice_no="INV001", customer_id=sample_customer_orm.id, customer=sample_customer_orm,
        invoice_date=date(2023, 1, 15), due_date=date(2023, 2, 15),
        currency_code="SGD", total_amount=Decimal("109.00"), amount_paid=Decimal("0.00"),
        status=InvoiceStatusEnum.DRAFT.value, created_by_user_id=1, updated_by_user_id=1,
        lines=[
            SalesInvoiceLine(id=1, invoice_id=1, description="Item A", quantity=Decimal(1), unit_price=Decimal(100), line_total=Decimal(109), tax_amount=Decimal(9))
        ]
    )

# --- Test Cases ---

async def test_get_by_id_found(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_sales_invoice_orm: SalesInvoice):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_sales_invoice_orm
    result = await sales_invoice_service.get_by_id(1)
    assert result == sample_sales_invoice_orm
    mock_session.execute.assert_awaited_once()

async def test_get_by_id_not_found(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    result = await sales_invoice_service.get_by_id(99)
    assert result is None

async def test_get_all_summary(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_sales_invoice_orm: SalesInvoice):
    mock_row = MagicMock()
    mock_row._asdict.return_value = { # Simulate RowMapping._asdict()
        "id": sample_sales_invoice_orm.id,
        "invoice_no": sample_sales_invoice_orm.invoice_no,
        "invoice_date": sample_sales_invoice_orm.invoice_date,
        "due_date": sample_sales_invoice_orm.due_date,
        "customer_name": sample_sales_invoice_orm.customer.name,
        "total_amount": sample_sales_invoice_orm.total_amount,
        "amount_paid": sample_sales_invoice_orm.amount_paid,
        "status": sample_sales_invoice_orm.status,
        "currency_code": sample_sales_invoice_orm.currency_code,
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result_dtos = await sales_invoice_service.get_all_summary()
    assert len(result_dtos) == 1
    assert isinstance(result_dtos[0], SalesInvoiceSummaryData)
    assert result_dtos[0].invoice_no == "INV001"

async def test_save_new_invoice(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_customer_orm: Customer):
    new_invoice = SalesInvoice(
        customer_id=sample_customer_orm.id, invoice_date=date(2023, 3, 1), due_date=date(2023, 3, 31),
        currency_code="SGD", total_amount=Decimal("200.00"), status=InvoiceStatusEnum.DRAFT.value,
        created_by_user_id=1, updated_by_user_id=1
    )
    # Simulate what refresh would do after save
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 10 # Simulate ID generated by DB
        obj.invoice_no = "INV002" # Simulate sequence generation
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        if attribute_names and 'lines' in attribute_names and not hasattr(obj, 'lines_loaded_flag'): # Mock simple line loading
             obj.lines = [SalesInvoiceLine(id=1, description="Test", quantity=1, unit_price=100, line_total=100)]
             obj.lines_loaded_flag = True
    mock_session.refresh.side_effect = mock_refresh

    result = await sales_invoice_service.save(new_invoice)
    
    mock_session.add.assert_called_once_with(new_invoice)
    mock_session.flush.assert_awaited_once()
    # Refresh will be called twice if lines are present and invoice.id is set
    assert mock_session.refresh.await_count >= 1 
    assert result.id == 10
    assert result.invoice_no == "INV002"

async def test_get_outstanding_invoices_for_customer(
    sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_sales_invoice_orm: SalesInvoice
):
    # Make sample invoice outstanding
    sample_sales_invoice_orm.status = InvoiceStatusEnum.APPROVED.value
    sample_sales_invoice_orm.amount_paid = Decimal("50.00")
    sample_sales_invoice_orm.total_amount = Decimal("109.00")
    sample_sales_invoice_orm.invoice_date = date(2023, 1, 1)
    sample_sales_invoice_orm.due_date = date(2023, 1, 31)


    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_sales_invoice_orm]
    
    as_of = date(2023, 2, 1) # Invoice is overdue
    results = await sales_invoice_service.get_outstanding_invoices_for_customer(customer_id=1, as_of_date=as_of)

    assert len(results) == 1
    assert results[0].id == sample_sales_invoice_orm.id
    mock_session.execute.assert_awaited_once()
    # Can add more assertions on the query conditions if needed
```

---
**2. New File: `tests/unit/services/test_purchase_invoice_service.py`**
---
```python
# File: tests/unit/services/test_purchase_invoice_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.business_services import PurchaseInvoiceService
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.business.vendor import Vendor
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import PurchaseInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock() # For delete test
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
def purchase_invoice_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> PurchaseInvoiceService:
    return PurchaseInvoiceService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_vendor_orm() -> Vendor:
    return Vendor(id=1, vendor_code="VEN001", name="Test Vendor", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_purchase_invoice_orm(sample_vendor_orm: Vendor) -> PurchaseInvoice:
    return PurchaseInvoice(
        id=1, invoice_no="PI001", vendor_id=sample_vendor_orm.id, vendor=sample_vendor_orm,
        vendor_invoice_no="VINV001", invoice_date=date(2023, 1, 10), due_date=date(2023, 2, 10),
        currency_code="SGD", total_amount=Decimal("55.00"), amount_paid=Decimal("0.00"),
        status=InvoiceStatusEnum.DRAFT.value, created_by_user_id=1, updated_by_user_id=1,
        lines=[
            PurchaseInvoiceLine(id=1, invoice_id=1, description="Material X", quantity=Decimal(5), unit_price=Decimal(10), line_total=Decimal(55), tax_amount=Decimal(5))
        ]
    )

# --- Test Cases ---
async def test_get_pi_by_id_found(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_purchase_invoice_orm
    result = await purchase_invoice_service.get_by_id(1)
    assert result == sample_purchase_invoice_orm
    mock_session.execute.assert_awaited_once()

async def test_get_all_pi_summary(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    mock_row = MagicMock()
    mock_row._asdict.return_value = {
        "id": sample_purchase_invoice_orm.id,
        "invoice_no": sample_purchase_invoice_orm.invoice_no,
        "vendor_invoice_no": sample_purchase_invoice_orm.vendor_invoice_no,
        "invoice_date": sample_purchase_invoice_orm.invoice_date,
        "vendor_name": sample_purchase_invoice_orm.vendor.name,
        "total_amount": sample_purchase_invoice_orm.total_amount,
        "status": sample_purchase_invoice_orm.status,
        "currency_code": sample_purchase_invoice_orm.currency_code,
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result_dtos = await purchase_invoice_service.get_all_summary()
    assert len(result_dtos) == 1
    assert isinstance(result_dtos[0], PurchaseInvoiceSummaryData)
    assert result_dtos[0].invoice_no == "PI001"

async def test_save_new_pi(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_vendor_orm: Vendor):
    new_pi = PurchaseInvoice(
        vendor_id=sample_vendor_orm.id, vendor_invoice_no="VINV002", invoice_date=date(2023, 4, 1), 
        due_date=date(2023, 4, 30), currency_code="SGD", total_amount=Decimal("300.00"), 
        status=InvoiceStatusEnum.DRAFT.value, created_by_user_id=1, updated_by_user_id=1
    )
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 20 # Simulate ID
        obj.invoice_no = "PI002" # Simulate internal ref no
    mock_session.refresh.side_effect = mock_refresh

    result = await purchase_invoice_service.save(new_pi)
    mock_session.add.assert_called_once_with(new_pi)
    assert result.id == 20
    assert result.invoice_no == "PI002"

async def test_delete_draft_pi_success(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    sample_purchase_invoice_orm.status = InvoiceStatusEnum.DRAFT.value # Ensure it's draft
    mock_session.get.return_value = sample_purchase_invoice_orm
    
    result = await purchase_invoice_service.delete(1)
    assert result is True
    mock_session.get.assert_awaited_once_with(PurchaseInvoice, 1)
    mock_session.delete.assert_awaited_once_with(sample_purchase_invoice_orm)

async def test_delete_non_draft_pi_fails(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    sample_purchase_invoice_orm.status = InvoiceStatusEnum.APPROVED.value # Not draft
    mock_session.get.return_value = sample_purchase_invoice_orm
    
    with pytest.raises(ValueError) as excinfo:
        await purchase_invoice_service.delete(1)
    assert "Only Draft invoices can be deleted" in str(excinfo.value)
    mock_session.delete.assert_not_called()

async def test_get_outstanding_invoices_for_vendor(
    purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice
):
    sample_purchase_invoice_orm.status = InvoiceStatusEnum.APPROVED.value
    sample_purchase_invoice_orm.amount_paid = Decimal("20.00")
    sample_purchase_invoice_orm.total_amount = Decimal("55.00")
    sample_purchase_invoice_orm.invoice_date = date(2023, 1, 1)
    
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_purchase_invoice_orm]
    
    as_of = date(2023, 2, 1)
    results = await purchase_invoice_service.get_outstanding_invoices_for_vendor(vendor_id=1, as_of_date=as_of)

    assert len(results) == 1
    assert results[0].id == sample_purchase_invoice_orm.id
```

---
**3. New File: `tests/unit/services/test_customer_service_dashboard_ext.py`**
---
```python
# File: tests/unit/services/test_customer_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date, timedelta

from app.services.business_services import CustomerService
from app.models.business.sales_invoice import SalesInvoice
from app.common.enums import InvoiceStatusEnum
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
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
def customer_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> CustomerService:
    return CustomerService(db_manager=mock_db_manager, app_core=mock_app_core)

def create_mock_sales_invoice(id: int, due_date: date, total_amount: Decimal, amount_paid: Decimal, status: InvoiceStatusEnum) -> MagicMock:
    inv = MagicMock(spec=SalesInvoice)
    inv.id = id
    inv.due_date = due_date
    inv.total_amount = total_amount
    inv.amount_paid = amount_paid
    inv.status = status.value
    inv.invoice_date = due_date - timedelta(days=30) # Assume invoice date is 30 days before due date
    return inv

async def test_get_ar_aging_summary_no_invoices(customer_service: CustomerService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    today = date(2023, 10, 15)
    summary = await customer_service.get_ar_aging_summary(as_of_date=today)
    expected = {"Current": Decimal(0), "1-30 Days": Decimal(0), "31-60 Days": Decimal(0), "61-90 Days": Decimal(0), "91+ Days": Decimal(0)}
    assert summary == expected

async def test_get_ar_aging_summary_various_scenarios(customer_service: CustomerService, mock_session: AsyncMock):
    today = date(2023, 10, 15)
    mock_invoices = [
        # Current (due today or future)
        create_mock_sales_invoice(1, today, Decimal("100"), Decimal("0"), InvoiceStatusEnum.APPROVED),
        create_mock_sales_invoice(2, today + timedelta(days=10), Decimal("50"), Decimal("0"), InvoiceStatusEnum.APPROVED),
        # 1-30 Days Overdue
        create_mock_sales_invoice(3, today - timedelta(days=1), Decimal("200"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        create_mock_sales_invoice(4, today - timedelta(days=30), Decimal("150"), Decimal("50"), InvoiceStatusEnum.PARTIALLY_PAID), # Outstanding 100
        # 31-60 Days Overdue
        create_mock_sales_invoice(5, today - timedelta(days=31), Decimal("300"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        create_mock_sales_invoice(6, today - timedelta(days=60), Decimal("250"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        # 61-90 Days Overdue
        create_mock_sales_invoice(7, today - timedelta(days=61), Decimal("400"), Decimal("100"), InvoiceStatusEnum.PARTIALLY_PAID), # Outstanding 300
        create_mock_sales_invoice(8, today - timedelta(days=90), Decimal("350"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        # 91+ Days Overdue
        create_mock_sales_invoice(9, today - timedelta(days=91), Decimal("500"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        create_mock_sales_invoice(10, today - timedelta(days=120), Decimal("450"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        # Paid / Voided (should be ignored)
        create_mock_sales_invoice(11, today - timedelta(days=5), Decimal("50"), Decimal("50"), InvoiceStatusEnum.PAID),
        create_mock_sales_invoice(12, today - timedelta(days=5), Decimal("60"), Decimal("0"), InvoiceStatusEnum.VOIDED),
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = mock_invoices
    
    summary = await customer_service.get_ar_aging_summary(as_of_date=today)
    
    assert summary["Current"] == Decimal("150.00") # 100 + 50
    assert summary["1-30 Days"] == Decimal("300.00") # 200 + 100
    assert summary["31-60 Days"] == Decimal("550.00") # 300 + 250
    assert summary["61-90 Days"] == Decimal("650.00") # 300 + 350
    assert summary["91+ Days"] == Decimal("950.00") # 500 + 450
```

---
**4. New File: `tests/unit/services/test_vendor_service_dashboard_ext.py`**
---
```python
# File: tests/unit/services/test_vendor_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date, timedelta

from app.services.business_services import VendorService
from app.models.business.purchase_invoice import PurchaseInvoice
from app.common.enums import InvoiceStatusEnum
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
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
def vendor_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> VendorService:
    return VendorService(db_manager=mock_db_manager, app_core=mock_app_core)

def create_mock_purchase_invoice(id: int, due_date: date, total_amount: Decimal, amount_paid: Decimal, status: InvoiceStatusEnum) -> MagicMock:
    inv = MagicMock(spec=PurchaseInvoice)
    inv.id = id
    inv.due_date = due_date
    inv.total_amount = total_amount
    inv.amount_paid = amount_paid
    inv.status = status.value
    inv.invoice_date = due_date - timedelta(days=30)
    return inv

async def test_get_ap_aging_summary_no_invoices(vendor_service: VendorService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    today = date(2023, 10, 15)
    summary = await vendor_service.get_ap_aging_summary(as_of_date=today)
    expected = {"Current": Decimal(0), "1-30 Days": Decimal(0), "31-60 Days": Decimal(0), "61-90 Days": Decimal(0), "91+ Days": Decimal(0)}
    assert summary == expected

async def test_get_ap_aging_summary_various_scenarios(vendor_service: VendorService, mock_session: AsyncMock):
    today = date(2023, 10, 15)
    mock_invoices = [
        create_mock_purchase_invoice(1, today, Decimal("1000"), Decimal("0"), InvoiceStatusEnum.APPROVED),
        create_mock_purchase_invoice(2, today - timedelta(days=15), Decimal("500"), Decimal("100"), InvoiceStatusEnum.PARTIALLY_PAID), # 400 in 1-30
        create_mock_purchase_invoice(3, today - timedelta(days=45), Decimal("750"), Decimal("0"), InvoiceStatusEnum.OVERDUE), # 750 in 31-60
        create_mock_purchase_invoice(4, today - timedelta(days=75), Decimal("200"), Decimal("0"), InvoiceStatusEnum.OVERDUE), # 200 in 61-90
        create_mock_purchase_invoice(5, today - timedelta(days=100), Decimal("300"), Decimal("0"), InvoiceStatusEnum.OVERDUE),# 300 in 91+
        create_mock_purchase_invoice(6, today + timedelta(days=5), Decimal("600"), Decimal("0"), InvoiceStatusEnum.APPROVED), # 600 in Current
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = mock_invoices
    
    summary = await vendor_service.get_ap_aging_summary(as_of_date=today)
    
    assert summary["Current"] == Decimal("1600.00") # 1000 + 600
    assert summary["1-30 Days"] == Decimal("400.00")
    assert summary["31-60 Days"] == Decimal("750.00")
    assert summary["61-90 Days"] == Decimal("200.00")
    assert summary["91+ Days"] == Decimal("300.00")
```

---
**5. New File: `tests/unit/services/test_account_service_dashboard_ext.py`**
---
```python
# File: tests/unit/services/test_account_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date

from app.services.account_service import AccountService
from app.models.accounting.account import Account as AccountModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.services.journal_service import JournalService # For mocking
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_journal_service() -> AsyncMock:
    return AsyncMock(spec=JournalService)

@pytest.fixture
def mock_app_core(mock_journal_service: AsyncMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.journal_service = mock_journal_service # Inject mock journal_service
    return app_core

@pytest.fixture
def account_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> AccountService:
    return AccountService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Accounts
@pytest.fixture
def current_asset_accounts() -> List[AccountModel]:
    return [
        AccountModel(id=1, code="1010", name="Cash", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=2, code="1020", name="AR", account_type="Asset", sub_type="Accounts Receivable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=3, code="1030", name="Inventory", account_type="Asset", sub_type="Inventory", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

@pytest.fixture
def current_liability_accounts() -> List[AccountModel]:
    return [
        AccountModel(id=4, code="2010", name="AP", account_type="Liability", sub_type="Accounts Payable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=5, code="2020", name="GST Payable", account_type="Liability", sub_type="GST Payable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

@pytest.fixture
def non_current_asset_account() -> AccountModel:
     return AccountModel(id=6, code="1500", name="Equipment", account_type="Asset", sub_type="Fixed Asset", is_active=True, created_by_user_id=1,updated_by_user_id=1)


async def test_get_total_balance_current_assets(
    account_service: AccountService, 
    mock_session: AsyncMock, 
    mock_journal_service: AsyncMock,
    current_asset_accounts: List[AccountModel]
):
    mock_session.execute.return_value.scalars.return_value.all.return_value = current_asset_accounts
    
    # Mock balances for these accounts
    def get_balance_side_effect(acc_id, as_of_date):
        if acc_id == 1: return Decimal("1000.00")
        if acc_id == 2: return Decimal("5000.00")
        if acc_id == 3: return Decimal("12000.00")
        return Decimal("0.00")
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect

    # Test for a specific subtype that matches one of the accounts
    total = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset", 
        account_type_name_like="Cash and Cash Equivalents", # Exact match for first account's sub_type
        as_of_date=date.today()
    )
    assert total == Decimal("1000.00")

    # Test with a pattern matching multiple accounts
    # Reset side effect for a new call scenario
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect
    total_current = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset",
        # Using a pattern that should ideally match multiple current asset subtypes based on your DashboardManager's lists
        # For this test, we assume these sub_types are fetched if they match "Current Asset%"
        # A more precise test might involve mocking specific `sub_type` names from `CURRENT_ASSET_SUBTYPES`
        account_type_name_like="Current Asset%", # Example, this might need adjustment based on actual CoA data
        as_of_date=date.today()
    )
    # This test depends on how broadly "Current Asset%" matches the sub_types in current_asset_accounts
    # If only AccountModel(sub_type="Current Asset") existed, the result would be based on that.
    # Given the current sample data, "Current Asset%" likely won't match any sub_type.
    # This test highlights the dependency on the `account_type_name_like` parameter and the data.
    # To make it robust, let's assume we are looking for "Cash and Cash Equivalents" and "Accounts Receivable"
    # This requires a more flexible `get_total_balance_by_sub_types` or multiple calls.
    
    # Let's test with actual subtypes from DashboardManager's CURRENT_ASSET_SUBTYPES logic
    # This test simulates how DashboardManager would sum up.
    
    # Mock setup for this specific scenario:
    # Accounts that match CURRENT_ASSET_SUBTYPES
    matching_accounts = [
        AccountModel(id=1, sub_type="Cash and Cash Equivalents", account_type="Asset", is_active=True, code="CASH", name="Cash", created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=2, sub_type="Accounts Receivable", account_type="Asset", is_active=True, code="AR", name="AR", created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=7, sub_type="Fixed Asset", account_type="Asset", is_active=True, code="FA", name="FA", created_by_user_id=1, updated_by_user_id=1) # Non-current
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = matching_accounts
    
    def get_balance_for_current_asset_test(acc_id, as_of_date):
        if acc_id == 1: return Decimal("200") # Cash
        if acc_id == 2: return Decimal("300") # AR
        if acc_id == 7: return Decimal("1000") # FA
        return Decimal(0)
    mock_journal_service.get_account_balance.side_effect = get_balance_for_current_asset_test
    
    # Simulate DashboardManager's iteration and summation
    from app.reporting.dashboard_manager import CURRENT_ASSET_SUBTYPES # Import the list
    
    calculated_current_assets = Decimal(0)
    for acc_subtype in CURRENT_ASSET_SUBTYPES:
        # This relies on the `account_type_name_like` to be an exact match here
        # The actual AccountService method takes one pattern. 
        # To test the sum for dashboard, we need to call it for each subtype or adapt it.
        # Let's adapt the test to reflect how AccountService.get_total_balance_by_account_category_and_type_pattern
        # would be called for a single subtype from the list.
        
        # Test for one specific subtype from the list
        mock_session.execute.return_value.scalars.return_value.all.return_value = [matching_accounts[0]] # Only cash account
        mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: Decimal("200") if acc_id == 1 else Decimal(0)
        sum_for_cash_subtype = await account_service.get_total_balance_by_account_category_and_type_pattern(
            account_category="Asset",
            account_type_name_like="Cash and Cash Equivalents", # Exact subtype
            as_of_date=date.today()
        )
        assert sum_for_cash_subtype == Decimal("200.00")

        mock_session.execute.return_value.scalars.return_value.all.return_value = [matching_accounts[1]] # Only AR account
        mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: Decimal("300") if acc_id == 2 else Decimal(0)
        sum_for_ar_subtype = await account_service.get_total_balance_by_account_category_and_type_pattern(
            account_category="Asset",
            account_type_name_like="Accounts Receivable", # Exact subtype
            as_of_date=date.today()
        )
        assert sum_for_ar_subtype == Decimal("300.00")


async def test_get_total_balance_no_matching_accounts(
    account_service: AccountService, mock_session: AsyncMock, mock_journal_service: AsyncMock
):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [] # No accounts match criteria
    
    total = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset", 
        account_type_name_like="NonExistentSubType%", 
        as_of_date=date.today()
    )
    assert total == Decimal("0.00")
    mock_journal_service.get_account_balance.assert_not_called() # Should not be called if no accounts found
```

