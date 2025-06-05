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
