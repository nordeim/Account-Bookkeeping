# File: app/models/accounting/recurring_pattern.py
# (Moved from app/models/recurring_pattern.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, List # Added List
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.journal_entry import JournalEntry # For relationship type hint
from app.models.core.user import User

class RecurringPattern(Base, TimestampMixin):
    __tablename__ = 'recurring_patterns'
    __table_args__ = (
        CheckConstraint("frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')", name='ck_recurring_patterns_frequency'),
        CheckConstraint("day_of_month BETWEEN 1 AND 31", name='ck_recurring_patterns_day_of_month'),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name='ck_recurring_patterns_day_of_week'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=False)
    
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    last_generated_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    next_generation_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    template_journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", foreign_keys=[template_entry_id], back_populates="template_for_patterns")
    generated_journal_entries: Mapped[List["JournalEntry"]] = relationship("JournalEntry", foreign_keys="JournalEntry.recurring_pattern_id", back_populates="generated_from_pattern")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
