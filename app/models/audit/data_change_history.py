# File: app/models/audit/data_change_history.py
# New model for audit.data_change_history table
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base
# from app.models.user import User # For FK relationship type hint
import datetime
from typing import Optional

class DataChangeHistory(Base):
    __tablename__ = 'data_change_history'
    __table_args__ = {'schema': 'audit'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False) # Not necessarily FK, just the ID
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False) # CHECK constraint in DB
    changed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # changed_by_user: Mapped[Optional["User"]] = relationship("User") # If User model accessible
