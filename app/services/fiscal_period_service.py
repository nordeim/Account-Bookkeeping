# File: app/services/fiscal_period_service.py
# Updated to use FiscalYear model
from typing import List, Optional
from datetime import date
from sqlalchemy import select, extract # Added extract
from app.models.accounting.fiscal_period import FiscalPeriod # Corrected path
from app.models.accounting.fiscal_year import FiscalYear # New import
from app.core.database_manager import DatabaseManager
from app.services import IFiscalPeriodRepository

class FiscalPeriodService(IFiscalPeriodRepository):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_by_id(self, period_id: int) -> Optional[FiscalPeriod]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalPeriod, period_id)

    async def get_all(self) -> List[FiscalPeriod]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalPeriod).order_by(FiscalPeriod.start_date)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalPeriod) -> FiscalPeriod:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: FiscalPeriod) -> FiscalPeriod:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity
            
    async def delete(self, id_val: int) -> bool:
        period = await self.get_by_id(id_val)
        if period and period.status != 'Archived': 
             async with self.db_manager.session() as session:
                await session.delete(period)
             return True
        return False

    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.start_date <= target_date,
                FiscalPeriod.end_date >= target_date,
                FiscalPeriod.status == 'Open' 
            ).order_by(FiscalPeriod.start_date.desc()) 
            result = await session.execute(stmt)
            return result.scalars().first()
            
    async def get_fiscal_year(self, year_value: int) -> Optional[FiscalYear]: # Changed return type to FiscalYear
        """Gets the FiscalYear ORM object for the specified accounting year (e.g., 2023 for FY2023)."""
        async with self.db_manager.session() as session:
            # Assumes year_name is like "FY2023" or just "2023"
            # This needs a robust way to map an integer year to a FiscalYear record.
            # For now, assuming year_name contains the year as a string.
            # Option 1: year_name is "YYYY"
            # stmt = select(FiscalYear).where(FiscalYear.year_name == str(year_value))
            # Option 2: year_value is contained in year_name
            stmt = select(FiscalYear).where(FiscalYear.year_name.like(f"%{year_value}%")) # type: ignore
            # Option 3: Check if year_value falls within start_date and end_date
            # stmt = select(FiscalYear).where(
            #    extract('year', FiscalYear.start_date) <= year_value,
            #    extract('year', FiscalYear.end_date) >= year_value
            # )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]:
        async with self.db_manager.session() as session:
            conditions = [FiscalPeriod.fiscal_year_id == fiscal_year_id]
            if period_type:
                conditions.append(FiscalPeriod.period_type == period_type)
            stmt = select(FiscalPeriod).where(*conditions).order_by(FiscalPeriod.period_number)
            result = await session.execute(stmt)
            return list(result.scalars().all())
