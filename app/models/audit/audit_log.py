# File: app/models/audit/audit_log.py
# New model for audit.audit_log table
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey # Added ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base
# from app.models.core.user import User # Changed to app.models.core.user
import datetime
from typing import Optional, Dict, Any

class AuditLog(Base):
    __tablename__ = 'audit_log'
    __table_args__ = {'schema': 'audit'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entity_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # user: Mapped[Optional["User"]] = relationship("User") # If User model from core is accessible
