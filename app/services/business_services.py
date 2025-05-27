# app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor # New Import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.services import ICustomerRepository, IVendorRepository # New Import IVendorRepository
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData # New Import VendorSummaryData

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
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only:
                conditions.append(Customer.is_active == True)
            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(
                    or_(
                        Customer.customer_code.ilike(search_pattern), 
                        Customer.name.ilike(search_pattern), 
                        Customer.email.ilike(search_pattern) 
                    )
                )
            
            stmt = select(
                Customer.id, Customer.customer_code, Customer.name,
                Customer.email, Customer.phone, Customer.is_active
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(Customer.name)
            
            if page_size > 0 : 
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer)
            await session.flush() 
            await session.refresh(customer) 
            return customer

    async def add(self, entity: Customer) -> Customer:
        return await self.save(entity)

    async def update(self, entity: Customer) -> Customer:
        return await self.save(entity)

    async def delete(self, customer_id: int) -> bool:
        if self.app_core and self.app_core.logger: # Check if logger exists
            self.app_core.logger.warning(f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation.")
        else: # Fallback print
            print(f"Warning: Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation.")
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")

# --- NEW: VendorService Implementation ---
class VendorService(IVendorRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(__name__) # Basic fallback logger

    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(
                selectinload(Vendor.currency),
                selectinload(Vendor.payables_account),
                selectinload(Vendor.created_by_user),
                selectinload(Vendor.updated_by_user)
            ).where(Vendor.id == vendor_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[Vendor]:
        """ Fetches all vendor ORM objects. Use with caution for large datasets. """
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only:
                conditions.append(Vendor.is_active == True)
            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(
                    or_(
                        Vendor.vendor_code.ilike(search_pattern), # type: ignore
                        Vendor.name.ilike(search_pattern),       # type: ignore
                        Vendor.email.ilike(search_pattern)        # type: ignore
                    )
                )
            
            stmt = select(
                Vendor.id, Vendor.vendor_code, Vendor.name,
                Vendor.email, Vendor.phone, Vendor.is_active
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(Vendor.name) # Default order
            
            if page_size > 0: # Enable pagination
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, vendor: Vendor) -> Vendor:
        """ Handles both create and update for Vendor ORM objects. """
        async with self.db_manager.session() as session:
            session.add(vendor)
            await session.flush()
            await session.refresh(vendor)
            return vendor

    async def add(self, entity: Vendor) -> Vendor:
        return await self.save(entity)

    async def update(self, entity: Vendor) -> Vendor:
        return await self.save(entity)

    async def delete(self, vendor_id: int) -> bool:
        log_msg = f"Hard delete attempted for Vendor ID {vendor_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")

# Need to import logging for the fallback logger in VendorService
import logging

