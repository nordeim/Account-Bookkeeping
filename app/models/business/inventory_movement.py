# File: app/models/business/inventory_movement.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin 
from app.models.business.product import Product
from app.models.core.user import User # For created_by FK
import datetime
from decimal import Decimal
from typing import Optional

class InventoryMovement(Base, TimestampMixin): 
    __tablename__ = 'inventory_movements'
    __table_args__ = (
        CheckConstraint("movement_type IN ('Purchase', 'Sale', 'Adjustment', 'Transfer', 'Return', 'Opening')", name='ck_inventory_movements_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.products.id'), nullable=False)
    movement_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,4), nullable=True)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="inventory_movements")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
