# File: app/models/journal_entry.py
# Updated for reference schema (recurring_patterns separate, new fields, FKs)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func
from typing import List, Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account
from app.models.fiscal_period import FiscalPeriod
from app.models.core.dimension import Dimension # For journal_entry_lines FKs

# RecurringPattern moved to its own file: app/models/recurring_pattern.py

class JournalEntry(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    entry_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    journal_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    entry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False) # If this JE is a template
    recurring_pattern_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.recurring_patterns.id'), nullable=True) # Link if generated from a pattern
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversing_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', use_alter=True, name='fk_je_reversing_entry_id'), nullable=True)
    
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # New
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # New

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    
    fiscal_period: Mapped["FiscalPeriod"] = relationship() # Simplified, back_populates could be added in FiscalPeriod
    lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    # recurring_pattern relationship defined in recurring_pattern.py due to its FK to JE for template
    # For the recurring_pattern_id FK on this JE (if it was generated from a pattern):
    generated_from_pattern: Mapped[Optional["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys=[recurring_pattern_id]) # type: ignore
    
    reversing_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversing_entry_id], uselist=False, post_update=True) # type: ignore

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
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD') # String(3) for CHAR(3), Added FK
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), default=Decimal(1))
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True) # FK to tax_codes.code
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
        
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines")
    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code]) # type: ignore
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code]) # type: ignore
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id]) # type: ignore
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id]) # type: ignore
    
    @validates('debit_amount', 'credit_amount')
    def validate_amounts(self, key, value):
        value_decimal = Decimal(str(value)) 
        if key == 'debit_amount' and value_decimal > Decimal(0):
            self.credit_amount = Decimal(0)
        elif key == 'credit_amount' and value_decimal > Decimal(0):
            self.debit_amount = Decimal(0)
        return value_decimal
