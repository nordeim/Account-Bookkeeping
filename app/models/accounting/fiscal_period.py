# File: app/models/accounting/fiscal_period.py
# (Moved from app/models/fiscal_period.py and updated)
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.core.user import User
from typing import Optional, List

class FiscalPeriod(Base, TimestampMixin):
    __tablename__ = 'fiscal_periods'
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'period_type', 'period_number', name='fp_unique_period_dates'),
        CheckConstraint('start_date <= end_date', name='fp_date_range_check'),
        CheckConstraint("period_type IN ('Month', 'Quarter', 'Year')", name='ck_fp_period_type'),
        CheckConstraint("status IN ('Open', 'Closed', 'Archived')", name='ck_fp_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False) 
    status: Mapped[str] = mapped_column(String(10), nullable=False, default='Open')
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    fiscal_year: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="fiscal_periods")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    journal_entries: Mapped[List["JournalEntry"]] = relationship(back_populates="fiscal_period") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="fiscal_period") # type: ignore
