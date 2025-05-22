# File: app/models/account_type.py
# Updated based on reference schema
from sqlalchemy import Column, Integer, String, Boolean, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin # Added TimestampMixin
from typing import Optional

class AccountType(Base, TimestampMixin): # Added TimestampMixin as per ref schema having created/updated_at
    __tablename__ = 'account_types'
    __table_args__ = (
        CheckConstraint("category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_account_types_category'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False) 
    is_debit_balance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False) # New
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
