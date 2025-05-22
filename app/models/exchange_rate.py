# File: app/models/exchange_rate.py
# Updated based on reference schema
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.currency import Currency 
# from app.models.user import User # For relationship
import datetime 
from decimal import Decimal 
from typing import Optional

class ExchangeRate(Base, TimestampMixin):
    __tablename__ = 'exchange_rates'
    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', 'rate_date', name='uq_exchange_rates_pair_date'), # Column names from ref schema
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    # Changed from_currency_code to from_currency to match ref schema column name
    from_currency_code: Mapped[str] = mapped_column("from_currency", String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    to_currency_code: Mapped[str] = mapped_column("to_currency", String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    rate_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)
    
    created_by_user_id: Mapped[Optional[int]] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=True)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True)

    from_currency_obj: Mapped["Currency"] = relationship("Currency", foreign_keys=[from_currency_code]) # Renamed relationship
    to_currency_obj: Mapped["Currency"] = relationship("Currency", foreign_keys=[to_currency_code]) # Renamed relationship
    # created_by_user: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_user_id])
    # updated_by_user: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by_user_id])
