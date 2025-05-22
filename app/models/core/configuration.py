# File: app/models/core/configuration.py
# New model for core.configuration table
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
# from app.models.user import User # For FK relationship
import datetime
from typing import Optional

class Configuration(Base, TimestampMixin):
    __tablename__ = 'configuration'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    config_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)

    # updated_by_user: Mapped[Optional["User"]] = relationship("User") # If User accessible
