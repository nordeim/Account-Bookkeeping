# File: app/models/tax_code.py
# Updated for reference schema (length of code, FKs for created_by/updated_by)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account
# from app.models.user import User # For relationship

class TaxCode(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'tax_codes'
    __table_args__ = (
        CheckConstraint("tax_type IN ('GST', 'Income Tax', 'Withholding Tax')", name='ck_tax_codes_tax_type'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True) # Length same as before
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False) 
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    affects_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

    affects_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[affects_account_id])
    # created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    # updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by])
