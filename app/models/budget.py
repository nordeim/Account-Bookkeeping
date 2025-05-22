# File: app/models/budget.py
# Updated budget to link to FiscalYear instead of integer year
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account 
from app.models.fiscal_year import FiscalYear # Changed from fiscal_year: Mapped[int]
from app.models.fiscal_period import FiscalPeriod # For BudgetDetail
from app.models.core.dimension import Dimension # For BudgetDetail, assuming Dimension model exists now
from typing import List, Optional 
from decimal import Decimal 

class Budget(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'budgets'
    __table_args__ = {'schema': 'accounting'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Changed from fiscal_year: Mapped[int] to FK
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin

    fiscal_year_obj: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="budgets") # Renamed relationship
    details: Mapped[List["BudgetDetail"]] = relationship("BudgetDetail", back_populates="budget", cascade="all, delete-orphan")

class BudgetDetail(Base, TimestampMixin, UserAuditMixin): # Added UserAuditMixin as per reference schema
    __tablename__ = 'budget_details'
    __table_args__ = (
        UniqueConstraint('budget_id', 'account_id', 'fiscal_period_id', 'dimension1_id', 'dimension2_id', name='uq_budget_details_key_dims'), # Updated unique constraint
        # Check constraint for period handled by fiscal_period_id FK if periods are constrained.
        # If period was an integer 1-12, a CHECK constraint would be here.
        # The reference schema uses fiscal_period_id.
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.budgets.id', ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False) # No ondelete specified in ref schema, assume RESTRICT/NO ACTION
    # Changed from period: Mapped[int] to fiscal_period_id
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # New fields from reference schema
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False) # From UserAuditMixin

    budget: Mapped["Budget"] = relationship("Budget", back_populates="details")
    account: Mapped["Account"] = relationship("Account", back_populates="budget_details")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod") # New relationship
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id]) # type: ignore
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id]) # type: ignore
