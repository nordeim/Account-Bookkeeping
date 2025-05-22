# File: app/models/vendor.py
# Updated for reference schema
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
from decimal import Decimal
import datetime

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account
from app.models.currency import Currency

class Vendor(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'vendors'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    vendor_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True) # New
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False) # Was in PRD
    gst_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    withholding_tax_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    withholding_tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5,2), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default='Singapore')
    payment_terms: Mapped[int] = mapped_column(Integer, default=30) 
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD') # Added FK
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    vendor_since: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True) # New
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    payables_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True) # New

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code]) # type: ignore
    payables_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[payables_account_id]) # type: ignore
    # purchase_invoices: Mapped[List["PurchaseInvoice"]] = relationship(back_populates="vendor") # Define in PurchaseInvoice
