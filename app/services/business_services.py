# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from decimal import Decimal
import logging # Added for basic logger fallback

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product # New Import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode # For Product.tax_code_obj relationship
from app.services import ICustomerRepository, IVendorRepository, IProductRepository # New Import IProductRepository
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData # New Import ProductSummaryData
from app.common.enums import ProductTypeEnum # New Import for product_type_filter

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerService(ICustomerRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)


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
            await session.flush(); await session.refresh(customer) 
            return customer

    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        log_msg = f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")

class VendorService(IVendorRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(
                selectinload(Vendor.currency), selectinload(Vendor.payables_account),
                selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)
            ).where(Vendor.id == vendor_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[Vendor]:
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
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern))) # type: ignore
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt)
            return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, vendor: Vendor) -> Vendor:
        async with self.db_manager.session() as session:
            session.add(vendor); await session.flush(); await session.refresh(vendor); return vendor
    async def add(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def update(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def delete(self, vendor_id: int) -> bool:
        log_msg = f"Hard delete attempted for Vendor ID {vendor_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")


# --- NEW: ProductService Implementation ---
class ProductService(IProductRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)


    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(
                selectinload(Product.sales_account),
                selectinload(Product.purchase_account),
                selectinload(Product.inventory_account),
                selectinload(Product.tax_code_obj), # Eager load TaxCode via relationship
                selectinload(Product.created_by_user),
                selectinload(Product.updated_by_user)
            ).where(Product.id == product_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[Product]:
        """ Fetches all product/service ORM objects. Use with caution for large datasets. """
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only:
                conditions.append(Product.is_active == True)
            if product_type_filter:
                conditions.append(Product.product_type == product_type_filter.value) # Compare with enum's value
            if search_term:
                search_pattern = f"%{search_term}%"
                conditions.append(
                    or_(
                        Product.product_code.ilike(search_pattern), # type: ignore
                        Product.name.ilike(search_pattern),         # type: ignore
                        Product.description.ilike(search_pattern)   # type: ignore
                    )
                )
            
            stmt = select(
                Product.id, Product.product_code, Product.name,
                Product.product_type, Product.sales_price, Product.purchase_price, 
                Product.is_active
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(Product.product_type, Product.name) # Default order
            
            if page_size > 0: # Enable pagination
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, product: Product) -> Product:
        """ Handles both create and update for Product ORM objects. """
        async with self.db_manager.session() as session:
            session.add(product)
            await session.flush()
            await session.refresh(product)
            return product

    async def add(self, entity: Product) -> Product:
        return await self.save(entity)

    async def update(self, entity: Product) -> Product:
        return await self.save(entity)

    async def delete(self, product_id: int) -> bool:
        log_msg = f"Hard delete attempted for Product/Service ID {product_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")
