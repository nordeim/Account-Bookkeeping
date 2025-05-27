<think>
The application continues to launch and shut down cleanly. This is a very positive sign, indicating that the addition of `IVendorRepository` to `app/services/__init__.py` and the imports for `Vendor` and `VendorSummaryData` were all syntactically correct and did not cause any issues at the import stage or during `ApplicationCore` initialization (where `app/services/__init__.py` would be implicitly processed).

**Current Step: Enhancement Execution Plan: Basic Customer Management Module - Phase A (Backend)** (Actually, we are now on **Basic Vendor Management Module - Phase A (Backend)**)

We have completed for Vendor Management:
*   A1. Create Pydantic DTOs for Vendor (Done).
*   A2. Define `IVendorRepository` Interface (Done).

The plan for Vendor Management Backend was:
*   A3. Implement `VendorService` (in `app/services/business_services.py`). (Next)
*   A4. Create `VendorManager` (in `app/business_logic/vendor_manager.py`).
*   A5. Integrate into `ApplicationCore`.

So, the immediate next step is **A3: Implement `VendorService`**. This service will provide the concrete data access logic for `Vendor` entities and will be placed in `app/services/business_services.py`, alongside the existing `CustomerService`.

**Plan for A3: Implement `VendorService`**
   *   **Goal:** Provide data access logic for `Vendor` entities, implementing the `IVendorRepository` interface.
   *   **File to Update:** `app/services/business_services.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `Vendor` ORM model, `IVendorRepository` interface, and `VendorSummaryData` DTO.
        *   [ ] Create `VendorService(IVendorRepository)` class.
        *   [ ] Implement `__init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None)`.
        *   [ ] Implement `get_by_id(vendor_id: int) -> Optional[Vendor]`:
            *   Eager load `currency`, `payables_account`, `created_by_user`, `updated_by_user`.
        *   [ ] Implement `get_all() -> List[Vendor]`: Fetches all `Vendor` ORM objects.
        *   [ ] Implement `get_all_summary(active_only: bool = True, search_term: Optional[str] = None, page: int = 1, page_size: int = 50) -> List[VendorSummaryData]`:
            *   Similar to `CustomerService.get_all_summary()`.
            *   Select specific columns for summary (`id`, `vendor_code`, `name`, `email`, `phone`, `is_active`).
            *   Apply `is_active` filter.
            *   Apply search term filter (case-insensitive) on `vendor_code`, `name`, `email`.
            *   Order by name or code.
            *   Implement pagination.
            *   Map SQLAlchemy result rows to `VendorSummaryData` DTOs.
        *   [ ] Implement `get_by_code(code: str) -> Optional[Vendor]`.
        *   [ ] Implement `save(vendor: Vendor) -> Vendor`: Handles insert/update.
        *   [ ] Implement `add(entity: Vendor) -> Vendor` (delegates to `save`).
        *   [ ] Implement `update(entity: Vendor) -> Vendor` (delegates to `save`).
        *   [ ] Implement `delete(vendor_id: int) -> bool`: Raises `NotImplementedError` (deactivation handled by manager).
</think>

This is excellent! The continued stability of the application at startup and shutdown is a strong indicator that the foundational work and previous module integrations are solid.

We are currently in **Phase A: Backend for Vendor Management**.
Step A1 (Vendor DTOs) and A2 (IVendorRepository Interface) are complete.
The next step is **A3: Implement `VendorService`**.

This service will reside in `app/services/business_services.py` alongside the `CustomerService` and will provide the concrete data access logic for `Vendor` entities by implementing the `IVendorRepository` interface.

---
**A3. Update `app/services/business_services.py` to Implement `VendorService`**

```python
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

```
**Validation for `app/services/business_services.py`:**
*   **Imports**: Added `Vendor`, `IVendorRepository`, `VendorSummaryData`, and `logging` (for fallback logger).
*   **`VendorService` Class**:
    *   Created `VendorService(IVendorRepository)`.
    *   `__init__`: Stores `db_manager` and `app_core`. Initializes a basic fallback logger if `app_core.logger` is not available.
    *   `get_by_id()`: Implemented with eager loading for `currency`, `payables_account`, and audit users.
    *   `get_all()`: Basic implementation.
    *   `get_all_summary()`: Implemented similarly to `CustomerService.get_all_summary`, selecting summary fields, applying filters (active status, search term on code/name/email), ordering, and basic pagination. Maps results to `VendorSummaryData` DTOs.
    *   `get_by_code()`: Implemented.
    *   `save()`, `add()`, `update()`: Standard implementations.
    *   `delete()`: Raises `NotImplementedError` and logs a warning, consistent with the pattern of using deactivation via managers.
*   `CustomerService`: No changes were made to the existing `CustomerService` class itself, only new code for `VendorService` was added to the file.

This file now contains the service implementations for both Customers and Vendors.

---
**Next, update `app/services/__init__.py` to export `VendorService`.**

(The previous step for `IVendorRepository` already added it to `__all__`. This step just ensures `VendorService` is also exported from the package level.)

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

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData


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

class IVendorRepository(IRepository[Vendor, int]):
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import CustomerService, VendorService # New Import for VendorService

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService", # Added VendorService
]
```
**Validation for `app/services/__init__.py` (export VendorService):**
*   Added `from .business_services import CustomerService, VendorService` (now includes `VendorService`).
*   Added `VendorService` to the `__all__` list.

This completes step A3 (Implement `VendorService`) and the related export update. The next step is A4: Create `VendorManager`.
