# File: app/models/account.py
# Updated based on reference schema
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint, Date, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List, Optional 
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
# Forward declare related models to avoid circular imports at module load time
# JournalEntryLine, BudgetDetail will be strings in Mapped type hints

class Account(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'accounts'
    __table_args__ = (
         CheckConstraint("account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_accounts_account_type'),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True) # Increased length
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    sub_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tax_treatment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    
    # New fields from reference schema
    report_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_control_account: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bank_account: Mapped[bool] = mapped_column(Boolean, default=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    opening_balance_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    # UserAuditMixin provides created_by, updated_by. Ensure they are FKs.
    # SQLAlchemy handles FKs automatically if UserAuditMixin.created_by is Mapped[int] = mapped_column(ForeignKey(...))
    # The reference schema has created_by/updated_by as FKs to core.users.id.
    # This needs to be reflected in UserAuditMixin or here directly if UserAuditMixin is too generic.
    # For now, assuming UserAuditMixin's Mapped[int] will be mapped to INTEGER NOT NULL REFERENCES core.users(id)
    # by Alembic or schema definition. Explicit FKs here:
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
        
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    
    journal_lines: Mapped[List["JournalEntryLine"]] = relationship(back_populates="account") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="account") # type: ignore

    def to_dict(self): 
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'account_type': self.account_type,
            'sub_type': self.sub_type,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'description': self.description,
            'report_group': self.report_group,
            'is_control_account': self.is_control_account,
            'is_bank_account': self.is_bank_account,
            'opening_balance': self.opening_balance,
            'opening_balance_date': self.opening_balance_date,
        }
