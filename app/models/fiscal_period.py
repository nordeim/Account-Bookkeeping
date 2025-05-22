# File: app/models/fiscal_period.py
# Updated to link to FiscalYear and other changes from reference schema
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.fiscal_year import FiscalYear # Import FiscalYear
from typing import Optional

class FiscalPeriod(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'fiscal_periods'
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'period_type', 'period_number', name='fp_unique_period_dates'), # Updated unique constraint
        CheckConstraint('start_date <= end_date', name='fp_date_range_check'),
        CheckConstraint("period_type IN ('Month', 'Quarter', 'Year')", name='ck_fp_period_type'),
        CheckConstraint("status IN ('Open', 'Closed', 'Archived')", name='ck_fp_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True) # autoincrement for SERIAL
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False) # New FK
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False) 
    status: Mapped[str] = mapped_column(String(10), nullable=False, default='Open')
    period_number: Mapped[int] = mapped_column(Integer, nullable=False) # New
    is_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin

    # Relationships
    fiscal_year: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="fiscal_periods")
    # journal_entries: Mapped[List["JournalEntry"]] = relationship("JournalEntry", back_populates="fiscal_period") # Defined in JE
