<think>
Excellent! The application startup and shutdown are now clean after adding `pydantic[email]` to `pyproject.toml` and running `poetry lock` and `poetry install`. This confirms the `ImportError: email-validator is not installed` has been resolved.

**Current Project Status Recap:**

*   **Core Architecture**: Stable. Async/Qt bridge functional.
*   **Database & ORM**: Comprehensive and functional. Audit triggers in place.
*   **Settings UI**: Company settings and Fiscal Year/Period management functional.
*   **Chart of Accounts UI**: Functional.
*   **Journal Entries UI & Backend**: Substantially complete and functional.
*   **GST Functionality**:
    *   Backend: Data aggregation and finalization logic in `GSTManager` is implemented.
    *   UI: UI in `ReportsWidget` to prepare, view, save draft, and finalize GST returns.
*   **Financial Reports UI**: UI in `ReportsWidget` to select, generate, view on-screen, and export standard financial reports (BS, P&L, TB).
*   **Cross-Cutting Concerns**: Audit trigger context, sequence generation, icon loading, Pydantic email validation dependency are addressed.

**Next Step Identification - Closing Gaps / Commonly Needed Features:**

The user requests to "proceed with the next step in your plan."
The previous plan was "Enhancement Execution Plan: Basic Customer Management Module", which was broken down into:
*   **Phase A: Backend for Customer Management (Current Focus)**
    *   A1. Create Pydantic DTOs for Customer (Done in the turn before last - `app/utils/pydantic_models.py` updated)
    *   A2. Define `ICustomerRepository` Interface (Next)
    *   A3. Implement `CustomerService` (Next)
    *   A4. Create `CustomerManager` (Next)
    *   A5. Integrate into `ApplicationCore` (Next)
*   **Phase B: Frontend UI for Customer Management** (Future)

So, the immediate next step within Phase A is **A2: Define `ICustomerRepository` Interface**. Then A3, A4, A5.

**Plan for this Turn: Implement Backend for Customer Management (Interfaces, Service, Manager, Core Integration)**

**Objective:** Create the necessary backend components (`ICustomerRepository`, `CustomerService`, `CustomerManager`) to support basic CRUD operations for Customers and integrate them into the `ApplicationCore`.

**Detailed Plan & Checklist:**

**A2. Define `ICustomerRepository` Interface**
   *   **Goal:** Specify the contract for customer data access.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `Customer` ORM model import.
        *   [ ] Define `CustomerSummaryData` DTO import (from `app.utils.pydantic_models`).
        *   [ ] Define `ICustomerRepository(IRepository[Customer, int])`.
        *   [ ] Declare methods:
            *   `get_by_code(self, code: str) -> Optional[Customer]`
            *   `get_all_summary(self, active_only: bool = True) -> List[CustomerSummaryData]` (Returns DTO directly for type safety)
            *   `search_customers(self, search_term: str, active_only: bool = True) -> List[CustomerSummaryData]`

**A3. Implement `CustomerService`**
   *   **Goal:** Provide concrete data access logic for `Customer` entities.
   *   **New File:** `app/services/business_services.py` (This file will host services for business entities like Customer, Vendor, Product).
   *   **Checklist & Tasks:**
        *   [ ] Create `CustomerService(ICustomerRepository)`.
        *   [ ] Implement `__init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None)`.
        *   [ ] Implement `get_by_id(customer_id: int)`: Eager load `currency` and `receivables_account`.
        *   [ ] Implement `get_all()`: Fetches all `Customer` ORM objects.
        *   [ ] Implement `get_all_summary(active_only: bool = True)`:
            *   Select specific columns for summary (`id`, `customer_code`, `name`, `email`, `phone`, `is_active`).
            *   Apply `is_active` filter if `active_only` is true.
            *   Order by name or code.
            *   Map SQLAlchemy result rows to `CustomerSummaryData` DTOs.
        *   [ ] Implement `get_by_code(code: str)`.
        *   [ ] Implement `save(customer: Customer)`: Handles insert/update. `TimestampMixin` handles `created_at`/`updated_at`. Manager will set audit user IDs.
        *   [ ] Implement `add(entity: Customer)` -> `return await self.save(entity)`.
        *   [ ] Implement `update(entity: Customer)` -> `return await self.save(entity)`.
        *   [ ] Implement `delete(customer_id: int)`: Should raise `NotImplementedError` as per pattern for hard delete. Deactivation is handled by manager.
        *   [ ] Implement `search_customers(...)`: Basic search on name, code, email. Returns `List[CustomerSummaryData]`.

**A4. Create `CustomerManager`**
   *   **Goal:** Encapsulate business logic for customer management.
   *   **New Directory and File:** `app/business_logic/customer_manager.py` (Or `app/customers/customer_manager.py` if preferred, but `business_logic` seems like a good top-level for various business entity managers). Let's go with `app/business_logic/customer_manager.py` for now.
   *   **Checklist & Tasks:**
        *   [ ] Create `CustomerManager(__init__(self, customer_service: CustomerService, app_core: "ApplicationCore"))`.
        *   [ ] Implement `get_customer_for_dialog(customer_id: int) -> Optional[Customer]`: Calls `customer_service.get_by_id()`.
        *   [ ] Implement `get_customers_for_listing(filters: Optional[Dict[str, Any]] = None) -> Result[List[CustomerSummaryData]]`:
            *   Handles filters (e.g., search term, active status).
            *   If search term present, calls `customer_service.search_customers()`.
            *   Else, calls `customer_service.get_all_summary()`.
            *   Returns `Result.success(list_of_dto)`.
        *   [ ] Implement `create_customer(dto: CustomerCreateData) -> Result[Customer]`:
            *   Validate customer code uniqueness (`customer_service.get_by_code()`).
            *   (Future) Validate `receivables_account_id` exists and is appropriate type.
            *   Map `CustomerCreateData` to `Customer` ORM.
            *   Set `created_by_user_id = dto.user_id`, `updated_by_user_id = dto.user_id`.
            *   Call `customer_service.save()`.
        *   [ ] Implement `update_customer(customer_id: int, dto: CustomerUpdateData) -> Result[Customer]`:
            *   Fetch existing `Customer`.
            *   Validate code uniqueness if changed.
            *   Update ORM fields. Set `updated_by_user_id = dto.user_id`.
            *   Call `customer_service.save()`.
        *   [ ] Implement `toggle_customer_active_status(customer_id: int, user_id: int) -> Result[Customer]`:
            *   Fetch customer. Toggle `is_active`. Set `updated_by_user_id`. Save.

**A5. Integrate into `app/core/application_core.py`**
   *   **Goal:** Make new Customer services and managers accessible.
   *   **File to Update:** `app/core/application_core.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `CustomerService` (from `app.services.business_services`) and `CustomerManager` (from `app.business_logic.customer_manager`).
        *   [ ] Add private instance variables (e.g., `self._customer_service: Optional[CustomerService]`, `self._customer_manager: Optional[CustomerManager]`).
        *   [ ] Instantiate them in `ApplicationCore.startup()`.
        *   [ ] Expose them via properties (`app_core.customer_service`, `app_core.customer_manager`).
   *   **File to Update:** `app/services/__init__.py`
        *   [ ] Export `CustomerService` and `ICustomerRepository`.
   *   **File to Create/Update:** `app/business_logic/__init__.py`
        *   [ ] Create if directory is new. Export `CustomerManager`.

This is a good chunk of work focusing purely on the backend for Customer management.
I will proceed step-by-step, starting with A2 (Interface), then A3 (Service), then A4 (Manager), and finally A5 (Core Integration).
I will also need to create the new directory `app/business_logic/` and its `__init__.py`, and the new file `app/services/business_services.py`.
</think>

Excellent! The application is stable and running, indicating the previous fixes and features (including GST UI groundwork and Financial Reports UI) were successfully integrated.

As per your direction, we'll now proceed with the next step in the plan: **"Basic UI for "Stubbed" Business Modules (Customers, Vendors, Products)"**, starting with **Customer Management**. This involves building out the backend (Service, Manager) and then the frontend (TableModel, Dialog, Widget).

**Enhancement Execution Plan: Implement Basic Customer Management Module - Phase A (Backend)**

**Overall Objective (Phase A):** Create the backend infrastructure (`ICustomerRepository` interface, `CustomerService` implementation, `CustomerManager` business logic) for managing Customer data, and integrate these components into the `ApplicationCore`.

---
**A1. Update `app/utils/pydantic_models.py` with Customer DTOs**
*(This step was completed in the previous turn where I provided the updated `pydantic_models.py` file that included `CustomerBaseData`, `CustomerCreateData`, `CustomerUpdateData`, `CustomerData`, and `CustomerSummaryData`. I will assume that version is now in your codebase.)*

---
**A2. Define `ICustomerRepository` Interface**

**Goal:** Specify the contract for customer data access operations.
**File to Update:** `app/services/__init__.py`

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
from app.models.business.customer import Customer # New Import

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData # New Import


# --- Existing Interfaces ---
class IAccountRepository(IRepository[Account, int]):
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

class IJournalEntryRepository(IRepository[JournalEntry, int]):
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


class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]):
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]):
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]):
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]):
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]):
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]):
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]):
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]):
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

# --- NEW: Customer Repository Interface ---
class ICustomerRepository(IRepository[Customer, int]):
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass # Returns DTO

    # save method for create/update will come from IRepository via CustomerService inheriting it.

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
# CustomerService will be in business_services.py, imported later

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", "ICustomerRepository", # Added ICustomerRepository
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    # CustomerService will be added to __all__ once defined.
]
```
**Validation for `app/services/__init__.py`:**
*   Added `from app.models.business.customer import Customer`.
*   Added `from app.utils.pydantic_models import CustomerSummaryData`.
*   Defined `ICustomerRepository(IRepository[Customer, int])` with the planned methods:
    *   `get_by_code(self, code: str) -> Optional[Customer]`
    *   `get_all_summary(self, active_only: bool = True, search_term: Optional[str] = None, page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]`: Changed from `search_customers` to be part of `get_all_summary` with optional `search_term` and added basic pagination parameters. This is more conventional for fetching list data.
*   Added `ICustomerRepository` to `__all__`.

---
**A3. Implement `CustomerService`**

**Goal:** Provide concrete data access logic for `Customer` entities.
**New File:** `app/services/business_services.py`

```python
# app/services/business_services.py
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

```
**Validation for `app/services/business_services.py` (CustomerService):**
*   Created new file `app/services/business_services.py`.
*   `CustomerService` implements `ICustomerRepository`.
*   `get_by_id`: Eager loads `currency` and `receivables_account` as these are useful for dialogs. Also loads audit users.
*   `get_all()`: Basic method to fetch all ORM objects.
*   `get_all_summary()`:
    *   Selects specific columns for the summary.
    *   Applies `is_active` filter.
    *   Applies search term filter (case-insensitive) on code, name, and email.
    *   Adds ordering by name.
    *   Adds basic pagination (`limit`, `offset`).
    *   Maps the SQLAlchemy result rows (using `result.mappings().all()`) directly to `CustomerSummaryData` DTOs.
*   `get_by_code()`: Implemented.
*   `save()`: Standard implementation for SQLAlchemy add/flush/refresh.
*   `add()` and `update()`: Delegate to `save()`.
*   `delete()`: Raises `NotImplementedError`, indicating deactivation should be used. Added logging.

---
Next, I'll add `CustomerService` and `ICustomerRepository` to the `__all__` list in `app/services/__init__.py` and proceed with `CustomerManager`.

**Update `app/services/__init__.py` (export new service)**

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

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData


# --- Existing Interfaces (condensed for brevity) ---
class IAccountRepository(IRepository[Account, int]): # ... (methods as before)
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

class IJournalEntryRepository(IRepository[JournalEntry, int]): # ... (methods as before)
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

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): # ... (methods as before)
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): # ... (methods as before)
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): # ... (methods as before)
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): # ... (methods as before)
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): # ... (methods as before)
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): # ... (methods as before)
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): # ... (methods as before)
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): # ... (methods as before)
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): # ... (methods as before)
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): # ... (methods as before)
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]):
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import CustomerService # New Import

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", "ICustomerRepository",
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", # Added CustomerService
]
```
**Validation for `app/services/__init__.py` (export update):**
*   Added `from .business_services import CustomerService`.
*   Added `CustomerService` to `__all__`.

This step provides the basic data access layer for Customers. Next, the `CustomerManager`.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing

