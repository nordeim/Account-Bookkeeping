# File: app/models/business/bank_account.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.core.user import User
from typing import List, Optional, TYPE_CHECKING
import datetime
from decimal import Decimal

if TYPE_CHECKING:
    from app.models.business.bank_transaction import BankTransaction # For relationship type hint
    from app.models.business.payment import Payment # For relationship type hint
    from app.models.business.bank_reconciliation import BankReconciliation # New import

class BankAccount(Base, TimestampMixin):
    __tablename__ = 'bank_accounts'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    last_reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    last_reconciled_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True) # New field
    gl_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency")
    gl_account: Mapped["Account"] = relationship("Account", back_populates="bank_account_links")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    bank_transactions: Mapped[List["BankTransaction"]] = relationship("BankTransaction", back_populates="bank_account") 
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="bank_account") 
    reconciliations: Mapped[List["BankReconciliation"]] = relationship("BankReconciliation", order_by="desc(BankReconciliation.statement_date)", back_populates="bank_account")

# This back_populates was already in the base file for BankAccount, ensuring it's correctly set up.
# Account.bank_account_links = relationship("BankAccount", back_populates="gl_account") 
