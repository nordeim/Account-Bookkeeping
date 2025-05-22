# File: app/models/accounting/dimension.py
# New model for accounting.dimensions
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.core.user import User # For FKs
from typing import List, Optional

class Dimension(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'dimensions'
    __table_args__ = (
        UniqueConstraint('dimension_type', 'code', name='uq_dimensions_type_code'),
        {'schema': 'accounting'} 
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dimension_type: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    
    parent: Mapped[Optional["Dimension"]] = relationship("Dimension", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Dimension"]] = relationship("Dimension", back_populates="parent")
