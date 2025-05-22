# File: app/models/accounting/budget.py
# (Moved from app/models/budget.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.fiscal_period import FiscalPeriod 
from app.models.accounting.dimension import Dimension 
from app.models.core.user import User
from typing import List, Optional 
from decimal import Decimal 

class Budget(Base, TimestampMixin): 
    __tablename__ = 'budgets'
    __table_args__ = {'schema': 'accounting'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    fiscal_year_obj: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="budgets")
    details: Mapped[List["BudgetDetail"]] = relationship("BudgetDetail", back_populates="budget", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class BudgetDetail(Base, TimestampMixin): 
    __tablename__ = 'budget_details'
    __table_args__ = (
        # Reference schema has COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0) in UNIQUE.
        # This means NULLs are treated as 0 for uniqueness.
        # This is harder to model directly in SQLAlchemy UniqueConstraint if DB doesn't support function-based indexes for it directly.
        # For PostgreSQL, function-based unique indexes are possible.
        # For now, simple UniqueConstraint. DB schema will have the COALESCE logic.
        UniqueConstraint('budget_id', 'account_id', 'fiscal_period_id', 'dimension1_id', 'dimension2_id', name='uq_budget_details_key_dims_nullable'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.budgets.id', ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    budget: Mapped["Budget"] = relationship("Budget", back_populates="details")
    account: Mapped["Account"] = relationship("Account", back_populates="budget_details")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod", back_populates="budget_details")
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

# Add back-populates to Account and FiscalPeriod
Account.budget_details = relationship("BudgetDetail", back_populates="account") # type: ignore
FiscalPeriod.budget_details = relationship("BudgetDetail", back_populates="fiscal_period") # type: ignore
