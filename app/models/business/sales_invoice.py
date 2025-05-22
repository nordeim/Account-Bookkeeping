# File: app/models/business/sales_invoice.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.business.customer import Customer # Corrected import path
from app.models.accounting.currency import Currency # Corrected import path
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension
from typing import List, Optional
import datetime
from decimal import Decimal

class SalesInvoice(Base, TimestampMixin):
    __tablename__ = 'sales_invoices'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided')", name='ck_sales_invoices_status'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.customers.id'), nullable=False)
    invoice_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15,6), default=Decimal(1))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(20), default='Draft', nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    terms_and_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="sales_invoices")
    currency: Mapped["Currency"] = relationship("Currency")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # Simplified relationship
    lines: Mapped[List["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class SalesInvoiceLine(Base, TimestampMixin):
    __tablename__ = 'sales_invoice_lines'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.sales_invoices.id', ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('business.products.id'), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5,2), default=Decimal(0))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    
    invoice: Mapped["SalesInvoice"] = relationship("SalesInvoice", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="sales_invoice_lines")
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])

# Add back_populates to Customer and Product:
Customer.sales_invoices = relationship("SalesInvoice", back_populates="customer") # type: ignore
Product.sales_invoice_lines = relationship("SalesInvoiceLine", back_populates="product") # type: ignore
