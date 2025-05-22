# File: app/models/core/sequence.py
# New model for core.sequences table
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin # Only TimestampMixin, no UserAuditMixin for this
from typing import Optional

class Sequence(Base, TimestampMixin):
    __tablename__ = 'sequences'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sequence_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    prefix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    next_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    increment_by: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_value: Mapped[int] = mapped_column(Integer, default=2147483647, nullable=False) # Max int4
    cycle: Mapped[bool] = mapped_column(Boolean, default=False)
    format_template: Mapped[str] = mapped_column(String(50), default='{PREFIX}{VALUE}{SUFFIX}')
