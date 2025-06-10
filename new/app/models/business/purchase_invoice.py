# File: app/models/business/purchase_invoice.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.currency import Currency
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension

if TYPE_CHECKING:
    from app.models.business.vendor import Vendor

class PurchaseInvoice(Base, TimestampMixin):
    __tablename__ = 'purchase_invoices'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Approved', 'Partially Paid', 'Paid', 'Overdue', 'Disputed', 'Voided')", name='ck_purchase_invoices_status'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.vendors.id'), nullable=False)
    vendor_invoice_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="purchase_invoices")
    currency: Mapped["Currency"] = relationship("Currency")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry")
    lines: Mapped[List["PurchaseInvoiceLine"]] = relationship("PurchaseInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class PurchaseInvoiceLine(Base, TimestampMixin):
    __tablename__ = 'purchase_invoice_lines'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.purchase_invoices.id', ondelete="CASCADE"), nullable=False)
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

    invoice: Mapped["PurchaseInvoice"] = relationship("PurchaseInvoice", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="purchase_invoice_lines")
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
