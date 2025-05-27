# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.accounting.account import Account # For FK relationship
from app.models.accounting.currency import Currency # For FK relationship
from app.services import ICustomerRepository # Import the interface
from app.utils.pydantic_models import CustomerSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerService(ICustomerRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(
                selectinload(Customer.currency),
                selectinload(Customer.receivables_account),
                selectinload(Customer.created_by_user),
                selectinload(Customer.updated_by_user)
            ).where(Customer.id == customer_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[Customer]:
        """ Fetches all customer ORM objects. Use with caution for large datasets. """
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50  # Default page_size
                             ) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only:
                conditions.append(Customer.is_active == True)
            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(
                    or_(
                        Customer.customer_code.ilike(search_pattern), # type: ignore
                        Customer.name.ilike(search_pattern), # type: ignore
                        Customer.email.ilike(search_pattern) # type: ignore
                    )
                )
            
            stmt = select(
                Customer.id,
                Customer.customer_code,
                Customer.name,
                Customer.email,
                Customer.phone,
                Customer.is_active
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(Customer.name)
            
            if page_size > 0 : # Enable pagination if page_size is positive
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            # Pydantic models expect dicts or ORM objects with from_attributes=True
            # result.mappings().all() gives List[RowMapping], which are dict-like
            return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]


    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, customer: Customer) -> Customer:
        """ Handles both create and update for Customer ORM objects. """
        async with self.db_manager.session() as session:
            session.add(customer)
            await session.flush() # Ensure IDs are populated, relationships processed
            await session.refresh(customer) # Get any DB-generated values
            return customer

    async def add(self, entity: Customer) -> Customer:
        return await self.save(entity)

    async def update(self, entity: Customer) -> Customer:
        return await self.save(entity)

    async def delete(self, customer_id: int) -> bool:
        # Hard delete is typically not desired for entities with financial history.
        # Deactivation (soft delete) is handled by the manager.
        self.app_core.logger.warning(f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation.") # type: ignore
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")
