# File: app/models/company_setting.py
# Updated based on reference schema
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
# from app.models.user import User # For relationship type hint
import datetime
from typing import Optional

class CompanySetting(Base, TimestampMixin):
    __tablename__ = 'company_settings'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True) # autoincrement for SERIAL
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True) # New
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registration_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False) # New
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[str] = mapped_column(String(50), default='Singapore') # Was Optional
    country: Mapped[str] = mapped_column(String(50), default='Singapore') # Was Optional
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1) # CHECK constraint in DB
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1) # CHECK constraint in DB
    base_currency: Mapped[str] = mapped_column(String(3), default='SGD') # No FK to currencies in ref schema
    tax_id_label: Mapped[str] = mapped_column(String(50), default='UEN') # New
    date_format: Mapped[str] = mapped_column(String(20), default='yyyy-MM-dd') # New
    
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True) # New

    # updated_by_user: Mapped[Optional["User"]] = relationship() # Relationship for updated_by
