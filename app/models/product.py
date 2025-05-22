# File: app/models/product.py
# Updated for reference schema
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account
# from app.models.business.inventory_movement import InventoryMovement # String hint

class Product(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint("product_type IN ('Inventory', 'Service', 'Non-Inventory')", name='ck_products_product_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    product_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # New
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # New
    sales_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    sales_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    purchase_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    inventory_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True) # FK to tax_codes.code
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_stock_level: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True) # New
    reorder_point: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True) # New

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

    sales_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[sales_account_id])
    purchase_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[purchase_account_id])
    inventory_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[inventory_account_id])
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code]) # type: ignore

    # inventory_movements: Mapped[List["InventoryMovement"]] = relationship(back_populates="product") # Define in InventoryMovement
    # sales_invoice_lines: Mapped[List["SalesInvoiceLine"]] = relationship(back_populates="product") # Define in SalesInvoiceLine
    # purchase_invoice_lines: Mapped[List["PurchaseInvoiceLine"]] = relationship(back_populates="product") # Define in PurchaseInvoiceLine
