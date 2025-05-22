# File: app/models/customer.py
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

class Customer(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'customers'
    __table_args__ = {'schema': 'business'} 

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    customer_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True) # New
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False) # Was in PRD, now in ref schema
    gst_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default='Singapore')
    credit_terms: Mapped[int] = mapped_column(Integer, default=30) 
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD') # Added FK
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    customer_since: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True) # New
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receivables_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True) # New

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code]) # type: ignore
    receivables_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[receivables_account_id]) # type: ignore
    # sales_invoices: Mapped[List["SalesInvoice"]] = relationship(back_populates="customer") # Define in SalesInvoice
