<think>
The application continues its perfect streak of launching and shutting down cleanly! This is excellent news and confirms that adding the `ISalesInvoiceRepository` interface to `app/services/__init__.py` along with its necessary imports was successful and did not introduce any issues at startup.

**Current Step: Enhancement Execution Plan: Basic Sales Invoicing - Phase A (Backend - Part 1)**

We have completed for Sales Invoice Backend:
*   A1. Create Pydantic DTOs for Sales Invoice (Done).
*   A2. Define `ISalesInvoiceRepository` Interface (Done).

The plan for Sales Invoice Backend (Part 1) was:
*   A3. Implement `SalesInvoiceService` (in `app/services/business_services.py`). (Next)

So, the immediate next step is **A3: Implement `SalesInvoiceService`**. This service will provide the concrete data access logic for `SalesInvoice` and `SalesInvoiceLine` entities and will be added to the existing `app/services/business_services.py` file.

**Plan for A3: Implement `SalesInvoiceService`**
   *   **Goal:** Provide data access logic for `SalesInvoice` entities, implementing the `ISalesInvoiceRepository` interface.
   *   **File to Update:** `app/services/business_services.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `SalesInvoice`, `SalesInvoiceLine` ORM models, `ISalesInvoiceRepository` interface, `SalesInvoiceSummaryData` DTO, and `InvoiceStatusEnum`.
        *   [ ] Create `SalesInvoiceService(ISalesInvoiceRepository)` class.
        *   [ ] Implement `__init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None)`.
        *   [ ] Implement `get_by_id(invoice_id: int) -> Optional[SalesInvoice]`:
            *   Eager load related entities: `SalesInvoice.lines` (and their `product`, `tax_code_obj`), `SalesInvoice.customer`, `SalesInvoice.currency`, `SalesInvoice.journal_entry`, `SalesInvoice.created_by_user`, `SalesInvoice.updated_by_user`.
        *   [ ] Implement `get_all() -> List[SalesInvoice]`: Fetches all `SalesInvoice` ORM objects (use with caution).
        *   [ ] Implement `get_all_summary(customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None, page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]`:
            *   Select specific columns for summary (`id`, `invoice_no`, `invoice_date`, `due_date`, `customer.name` (requires join), `total_amount`, `amount_paid`, `status`).
            *   Join with `Customer` table to fetch `customer.name`.
            *   Apply filters: `customer_id`, `status` (using enum value), `invoice_date` range.
            *   Order by `invoice_date` desc, `invoice_no` desc.
            *   Implement pagination.
            *   Map SQLAlchemy result rows to `SalesInvoiceSummaryData` DTOs.
        *   [ ] Implement `get_by_invoice_no(invoice_no: str) -> Optional[SalesInvoice]`.
        *   [ ] Implement `save(invoice: SalesInvoice) -> SalesInvoice`: Handles insert/update. Ensure `cascade="all, delete-orphan"` on `SalesInvoice.lines` relationship in the ORM model handles line persistence.
        *   [ ] Implement `add(entity: SalesInvoice) -> SalesInvoice` (delegates to `save`).
        *   [ ] Implement `update(entity: SalesInvoice) -> SalesInvoice` (delegates to `save`).
        *   [ ] Implement `delete(invoice_id: int) -> bool`: Raises `NotImplementedError`. Deletion/voiding logic will be in the manager and will likely update status rather than hard delete.

</think>

This is fantastic! The application's stability is consistently maintained.

We are proceeding with **Phase A: Backend for Sales Invoice Creation**.
Steps A1 (Sales Invoice DTOs) and A2 (ISalesInvoiceRepository Interface) are complete.
The next step is **A3: Implement `SalesInvoiceService`**.

This service will be added to `app/services/business_services.py` and will provide the data access logic for `SalesInvoice` and `SalesInvoiceLine` entities.

---
**A3. Update `app/services/business_services.py` to Implement `SalesInvoiceService`**

```python
# app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload # Added joinedload
from decimal import Decimal
import logging 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine # New Import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import ICustomerRepository, IVendorRepository, IProductRepository, ISalesInvoiceRepository # New Import ISalesInvoiceRepository
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData, SalesInvoiceSummaryData # New Import SalesInvoiceSummaryData
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum # New Import InvoiceStatusEnum
from datetime import date # For date type hints

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerService(ICustomerRepository):
    # ... (CustomerService implementation remains unchanged from previous version)
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(selectinload(Customer.currency),selectinload(Customer.receivables_account),selectinload(Customer.created_by_user),selectinload(Customer.updated_by_user)).where(Customer.id == customer_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Customer.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Customer.customer_code.ilike(search_pattern), Customer.name.ilike(search_pattern), Customer.email.ilike(search_pattern) ))
            stmt = select(Customer.id, Customer.customer_code, Customer.name, Customer.email, Customer.phone, Customer.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Customer.name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer); await session.flush(); await session.refresh(customer); return customer
    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        log_msg = f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")

class VendorService(IVendorRepository):
    # ... (VendorService implementation remains unchanged from previous version)
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(selectinload(Vendor.currency), selectinload(Vendor.payables_account),selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)).where(Vendor.id == vendor_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern)))
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code); result = await session.execute(stmt); return result.scalars().first()
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

class ProductService(IProductRepository):
    # ... (ProductService implementation remains unchanged from previous version)
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(selectinload(Product.sales_account),selectinload(Product.purchase_account),selectinload(Product.inventory_account),selectinload(Product.tax_code_obj),selectinload(Product.created_by_user),selectinload(Product.updated_by_user)).where(Product.id == product_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,product_type_filter: Optional[ProductTypeEnum] = None,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Product.is_active == True)
            if product_type_filter: conditions.append(Product.product_type == product_type_filter.value)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Product.product_code.ilike(search_pattern), Product.name.ilike(search_pattern), Product.description.ilike(search_pattern)))
            stmt = select(Product.id, Product.product_code, Product.name, Product.product_type, Product.sales_price, Product.purchase_price, Product.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Product.product_type, Product.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, product: Product) -> Product:
        async with self.db_manager.session() as session:
            session.add(product); await session.flush(); await session.refresh(product); return product
    async def add(self, entity: Product) -> Product: return await self.save(entity)
    async def update(self, entity: Product) -> Product: return await self.save(entity)
    async def delete(self, product_id: int) -> bool:
        log_msg = f"Hard delete attempted for Product/Service ID {product_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")


# --- NEW: SalesInvoiceService Implementation ---
class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),
                selectinload(SalesInvoice.customer),
                selectinload(SalesInvoice.currency),
                selectinload(SalesInvoice.journal_entry), # For posted invoices
                selectinload(SalesInvoice.created_by_user),
                selectinload(SalesInvoice.updated_by_user)
            ).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[SalesInvoice]:
        """ Fetches all sales invoice ORM objects. Use with caution for large datasets. """
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt)
            # Eager load lines if this method is used broadly, otherwise expect N+1 for lines.
            # For now, no explicit line loading here for performance on `get_all`.
            return list(result.scalars().all())

    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None:
                conditions.append(SalesInvoice.customer_id == customer_id)
            if status:
                conditions.append(SalesInvoice.status == status.value)
            if start_date:
                conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date:
                conditions.append(SalesInvoice.invoice_date <= end_date)
            
            # Select specific columns for summary and join with Customer for customer_name
            stmt = select(
                SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date,
                Customer.name.label("customer_name"), # Label for DTO mapping
                SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status
            ).join(Customer, SalesInvoice.customer_id == Customer.id) # Assuming Customer model is imported
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            
            if page_size > 0: # Enable pagination
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            # Map SQLAlchemy result (RowMapping) to Pydantic DTO
            return [SalesInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(
                selectinload(SalesInvoice.lines) # Load lines when fetching by specific number
            ).where(SalesInvoice.invoice_no == invoice_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, invoice: SalesInvoice) -> SalesInvoice:
        """ Handles both create and update for SalesInvoice ORM objects.
            Assumes lines are managed via cascade on SalesInvoice.lines relationship.
        """
        async with self.db_manager.session() as session:
            session.add(invoice)
            await session.flush() # Populates IDs, processes cascades if lines are new
            await session.refresh(invoice) # Get DB defaults like created_at
            # Eager load lines after save to ensure they are part of the returned object graph
            if invoice.id and invoice.lines: # Check if lines were part of the save graph
                await session.refresh(invoice, attribute_names=['lines'])
                # for line in invoice.lines: # Optionally refresh each line too
                #     await session.refresh(line)
            return invoice

    async def add(self, entity: SalesInvoice) -> SalesInvoice:
        return await self.save(entity)

    async def update(self, entity: SalesInvoice) -> SalesInvoice:
        return await self.save(entity)

    async def delete(self, invoice_id: int) -> bool:
        # Sales invoices are typically not hard-deleted, but voided or cancelled.
        # This logic will be in the SalesInvoiceManager.
        log_msg = f"Hard delete attempted for Sales Invoice ID {invoice_id}. Not implemented; use void/cancel."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")

```
**Validation for `app/services/business_services.py` (SalesInvoiceService addition):**
*   **Imports**: Added `SalesInvoice`, `SalesInvoiceLine`, `ISalesInvoiceRepository`, `SalesInvoiceSummaryData`, `InvoiceStatusEnum`, and `date`.
*   **`SalesInvoiceService` Class**:
    *   Created `SalesInvoiceService(ISalesInvoiceRepository)`.
    *   `__init__`: Standard setup.
    *   `get_by_id()`: Implemented with eager loading for lines (including their product and tax code), customer, currency, journal entry, and audit users. This is comprehensive for a dialog view.
    *   `get_all()`: Basic implementation to fetch all `SalesInvoice` ORMs.
    *   `get_all_summary()`:
        *   Selects specific columns required for `SalesInvoiceSummaryData`.
        *   Includes a `join(Customer, SalesInvoice.customer_id == Customer.id)` to fetch `Customer.name`.
        *   Applies filters: `customer_id`, `status` (using `status.value`), `invoice_date` range.
        *   Orders by invoice date and number (descending).
        *   Implements basic pagination.
        *   Maps results to `SalesInvoiceSummaryData` DTOs.
    *   `get_by_invoice_no()`: Implemented with line eager loading.
    *   `save()`: Handles insert/update. Relies on `cascade="all, delete-orphan"` on `SalesInvoice.lines` relationship for line persistence. Refreshes invoice and its lines after flush.
    *   `add()`, `update()`: Delegate to `save()`.
    *   `delete()`: Raises `NotImplementedError`, as invoices should typically be voided or cancelled via manager logic.
*   No changes were made to the existing `CustomerService`, `VendorService`, or `ProductService` classes.

This file now contains the service implementation for Sales Invoices.

---
**Next, update `app/services/__init__.py` to export `SalesInvoiceService`.**

```python
# app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict 
from datetime import date
from decimal import Decimal 

T = TypeVar('T') 
ID = TypeVar('ID') 

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id_val: ID) -> Optional[T]: pass
    @abstractmethod
    async def get_all(self) -> List[T]: pass
    @abstractmethod
    async def add(self, entity: T) -> T: pass
    @abstractmethod
    async def update(self, entity: T) -> T: pass
    @abstractmethod
    async def delete(self, id_val: ID) -> bool: pass

# --- ORM Model Imports ---
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType 
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate 
from app.models.core.sequence import Sequence 
from app.models.core.configuration import Configuration 
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData, SalesInvoiceSummaryData

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum


# --- Existing Interfaces (condensed for brevity) ---
class IAccountRepository(IRepository[Account, int]): # ...
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass
    @abstractmethod
    async def save(self, account: Account) -> Account: pass 
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass 
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]: pass

class IJournalEntryRepository(IRepository[JournalEntry, int]): # ...
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
    @abstractmethod
    async def get_all_summary(self, start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): # ...
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): # ...
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): # ...
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): # ... 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): # ...
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): # ...
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): # ... 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): # ...
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): # ...
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): # ...
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]): # ... 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass

class IVendorRepository(IRepository[Vendor, int]): # ... 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

class IProductRepository(IRepository[Product, int]): # ... 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
    @abstractmethod
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]: pass

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import CustomerService, VendorService, ProductService, SalesInvoiceService # New Import for SalesInvoiceService

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", # Added SalesInvoiceService
]
```
**Validation for `app/services/__init__.py` (export SalesInvoiceService):**
*   Added `from .business_services import ..., SalesInvoiceService`.
*   Added `SalesInvoiceService` to the `__all__` list.

This completes step A3 (Implement `SalesInvoiceService`) and the related export update. The next backend step for Sales Invoicing is A4: Create `SalesInvoiceManager`.
