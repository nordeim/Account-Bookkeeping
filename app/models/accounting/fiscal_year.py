# File: app/models/accounting/fiscal_year.py
# (Previously generated as app/models/fiscal_year.py, reviewed and confirmed)
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import DATERANGE # For GIST constraint if modeled in SQLAlchemy
# from sqlalchemy.sql.functions import GenericFunction # For functions like `daterange`
# from sqlalchemy.sql import literal_column
from app.models.base import Base, TimestampMixin # UserAuditMixin handled directly
from app.models.core.user import User
import datetime
from typing import List, Optional

class FiscalYear(Base, TimestampMixin):
    __tablename__ = 'fiscal_years'
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='fy_date_range_check'),
        # The EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
        # is a database-level constraint. SQLAlchemy doesn't model EXCLUDE directly in Core/ORM easily.
        # It's enforced by the DB schema from schema.sql.
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[Optional[int]] = mapped_column("closed_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by",Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by",Integer, ForeignKey('core.users.id'), nullable=False)

    # Relationships
    closed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[closed_by_user_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    fiscal_periods: Mapped[List["FiscalPeriod"]] = relationship("FiscalPeriod", back_populates="fiscal_year") # type: ignore
    budgets: Mapped[List["Budget"]] = relationship("Budget", back_populates="fiscal_year_obj") # type: ignore
