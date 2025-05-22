# File: app/models/business/product.py
# (Moved from app/models/product.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List 
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.models.core.user import User

class Product(Base, TimestampMixin):
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
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sales_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    sales_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    purchase_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    inventory_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_stock_level: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    reorder_point: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    sales_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[sales_account_id], back_populates="product_sales_links")
    purchase_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[purchase_account_id], back_populates="product_purchase_links")
    inventory_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[inventory_account_id], back_populates="product_inventory_links")
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code]) # Add back_populates to TaxCode if needed

    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    inventory_movements: Mapped[List["InventoryMovement"]] = relationship("InventoryMovement", back_populates="product") # type: ignore
    sales_invoice_lines: Mapped[List["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="product") # type: ignore
    purchase_invoice_lines: Mapped[List["PurchaseInvoiceLine"]] = relationship("PurchaseInvoiceLine", back_populates="product") # type: ignore
