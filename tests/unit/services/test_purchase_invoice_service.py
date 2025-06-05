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
