# File: app/models/accounting/journal_entry.py
# (Moved from app/models/journal_entry.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func
from typing import List, Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.core.user import User
from app.models.accounting.currency import Currency
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension
# from app.models.accounting.recurring_pattern import RecurringPattern # Forward reference with string

class JournalEntry(Base, TimestampMixin):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    entry_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    journal_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    entry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_pattern_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.recurring_patterns.id'), nullable=True)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversing_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', use_alter=True, name='fk_je_reversing_entry_id'), nullable=True)
    
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod", back_populates="journal_entries")
    lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    generated_from_pattern: Mapped[Optional["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys=[recurring_pattern_id], back_populates="generated_journal_entries") # type: ignore
    
    reversing_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversing_entry_id], uselist=False, post_update=True) # type: ignore
    template_for_patterns: Mapped[List["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys="RecurringPattern.template_entry_id", back_populates="template_journal_entry") # type: ignore


    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class JournalEntryLine(Base, TimestampMixin): 
    __tablename__ = 'journal_entry_lines'
    __table_args__ = (
        CheckConstraint(
            " (debit_amount > 0 AND credit_amount = 0) OR "
            " (credit_amount > 0 AND debit_amount = 0) OR "
            " (debit_amount = 0 AND credit_amount = 0) ", 
            name='jel_check_debit_credit'
        ),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    journal_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD')
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), default=Decimal(1))
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
        
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines")
    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code])
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
    
    @validates('debit_amount', 'credit_amount')
    def validate_amounts(self, key, value):
        value_decimal = Decimal(str(value)) 
        if key == 'debit_amount' and value_decimal > Decimal(0):
            self.credit_amount = Decimal(0)
        elif key == 'credit_amount' and value_decimal > Decimal(0):
            self.debit_amount = Decimal(0)
        return value_decimal

# Update Account relationships for journal_lines
Account.journal_lines = relationship("JournalEntryLine", back_populates="account") # type: ignore
