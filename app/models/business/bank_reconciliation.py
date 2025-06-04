# File: app/models/business/bank_reconciliation.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, UniqueConstraint, DateTime, CheckConstraint # Added CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING # Added TYPE_CHECKING

from app.models.base import Base, TimestampMixin 
from app.models.business.bank_account import BankAccount
from app.models.core.user import User

if TYPE_CHECKING: # To handle circular dependency for type hint
    from app.models.business.bank_transaction import BankTransaction

class BankReconciliation(Base, TimestampMixin):
    __tablename__ = 'bank_reconciliations'
    __table_args__ = (
        UniqueConstraint('bank_account_id', 'statement_date', name='uq_bank_reconciliation_account_statement_date'),
        CheckConstraint("status IN ('Draft', 'Finalized')", name='ck_bank_reconciliations_status'), # New constraint
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    statement_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    statement_ending_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    calculated_book_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reconciled_difference: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reconciliation_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Draft', nullable=False) # New field
    
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    # updated_by_user_id is handled by TimestampMixin's onupdate for updated_at. 
    # If explicit user ID needed, add UserAuditMixin or direct Mapped column. Schema uses created_by only for this table.

    # Relationships
    bank_account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="reconciliations") # Updated back_populates
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    
    reconciled_transactions: Mapped[List["BankTransaction"]] = relationship(
        "BankTransaction", 
        back_populates="reconciliation_instance"
    )

    def __repr__(self) -> str:
        return f"<BankReconciliation(id={self.id}, bank_account_id={self.bank_account_id}, stmt_date={self.statement_date}, diff={self.reconciled_difference}, status='{self.status}')>"

# Ensure BankAccount model has the correct back_populates for reconciliations if not already set.
# This is typically done in the BankAccount model file itself to avoid circular import issues at runtime
# for model definition, but for completeness of understanding:
# BankAccount.reconciliations = relationship("BankReconciliation", order_by=BankReconciliation.statement_date.desc(), back_populates="bank_account")
