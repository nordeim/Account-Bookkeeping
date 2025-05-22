# File: app/models/accounting/currency.py
# (Moved from app/models/currency.py and fields updated)
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.core.user import User 
from typing import Optional

class Currency(Base, TimestampMixin):
    __tablename__ = 'currencies'
    __table_args__ = {'schema': 'accounting'}

    code: Mapped[str] = mapped_column(String(3), primary_key=True) 
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    format_string: Mapped[str] = mapped_column(String(20), default='#,##0.00') 

    created_by_user_id: Mapped[Optional[int]] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=True)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])
