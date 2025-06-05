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
