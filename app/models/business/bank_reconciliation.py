# File: app/models/business/bank_reconciliation.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime
from decimal import Decimal
from typing import Optional, List

from app.models.base import Base, TimestampMixin # UserAuditMixin will be handled by direct FKs for created_by
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
# from app.models.business.bank_transaction import BankTransaction # Needed for back_populates

class BankReconciliation(Base, TimestampMixin):
    __tablename__ = 'bank_reconciliations'
    __table_args__ = (
        UniqueConstraint('bank_account_id', 'statement_date', name='uq_bank_reconciliation_account_statement_date'),
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
    
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    # updated_by is implicitly handled by TimestampMixin if updated_at is sufficient. 
    # If explicit updated_by is needed, add UserAuditMixin or direct fields. Schema has created_by only.

    # Relationships
    bank_account: Mapped["BankAccount"] = relationship("BankAccount") # back_populates on BankAccount if needed
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    
    # Link to BankTransaction records reconciled by this instance
    reconciled_transactions: Mapped[List["BankTransaction"]] = relationship(
        "BankTransaction", 
        back_populates="reconciliation_instance"
    ) # type: ignore

    def __repr__(self) -> str:
        return f"<BankReconciliation(id={self.id}, bank_account_id={self.bank_account_id}, stmt_date={self.statement_date}, diff={self.reconciled_difference})>"

# Add back_populates to BankAccount and BankTransaction
BankAccount.reconciliations = relationship("BankReconciliation", order_by=BankReconciliation.statement_date.desc(), back_populates="bank_account") # type: ignore

# BankTransaction model needs to be imported here to add the relationship,
# or this relationship definition should be moved to bank_transaction.py to avoid circular imports.
# For now, let's assume BankTransaction will be updated separately or this implies it.
# This is better defined in bank_transaction.py.
# from app.models.business.bank_transaction import BankTransaction
# BankTransaction.reconciliation_instance = relationship("BankReconciliation", back_populates="reconciled_transactions")
