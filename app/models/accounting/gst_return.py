# File: app/models/accounting/gst_return.py
# (Moved from app/models/gst_return.py and updated)
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry

class GSTReturn(Base, TimestampMixin):
    __tablename__ = 'gst_returns'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Submitted', 'Amended')", name='ck_gst_returns_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    return_period: Mapped[str] = mapped_column(String(20), unique=True, nullable=False) 
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    filing_due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    standard_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    zero_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    exempt_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    total_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    taxable_purchases: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    output_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    input_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_adjustments: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_payable: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(20), default='Draft')
    submission_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # No back_populates needed for one-to-one/opt-one
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
