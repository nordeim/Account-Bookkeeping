<think>
The application continues to launch and shut down cleanly! This is a great sign. It indicates that adding the Product DTOs to `app/utils/pydantic_models.py` and importing `ProductTypeEnum` was successful and didn't break any existing import chains or cause issues during Pydantic model schema generation at startup.

**Current Step: Enhancement Execution Plan: Basic Product/Service Management Module - Phase A (Backend)**

We have completed for Product/Service Management:
*   A1. Create Pydantic DTOs for Product (Done).

The plan for Product/Service Management Backend is:
*   A2. Define `IProductRepository` Interface (Next).
*   A3. Implement `ProductService` (in `app/services/business_services.py`).
*   A4. Create `ProductManager` (in `app/business_logic/product_manager.py`).
*   A5. Integrate into `ApplicationCore`.

So, the immediate next step is **A2: Define `IProductRepository` Interface**. This will be added to `app/services/__init__.py`.

**Plan for A2: Define `IProductRepository` Interface**
   *   **Goal:** Specify the contract for product/service data access.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `Product` ORM model from `app.models.business.product`.
        *   [ ] Import `ProductSummaryData` DTO from `app.utils.pydantic_models`.
        *   [ ] Import `ProductTypeEnum` from `app.common.enums`.
        *   [ ] Define `IProductRepository(IRepository[Product, int])`.
        *   [ ] Declare methods:
            *   `get_by_code(self, code: str) -> Optional[Product]`
            *   `get_all_summary(self, active_only: bool = True, product_type_filter: Optional[ProductTypeEnum] = None, search_term: Optional[str] = None, page: int = 1, page_size: int = 50) -> List[ProductSummaryData]`
        *   [ ] Add `IProductRepository` to the `__all__` list.
</think>

This is excellent! The application's continued stability after adding the Product DTOs is very positive.

We are proceeding with **Phase A: Backend for Product/Service Management**.
Step A1 (Product DTOs) is complete.
The next step is **A2: Define `IProductRepository` Interface**.

This interface will specify the contract for data access operations related to Products and Services and will be added to `app/services/__init__.py`.

---
**A2. Update `app/services/__init__.py` to define `IProductRepository`**

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
from app.models.business.product import Product # New Import

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData # New Import for ProductSummaryData

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ProductTypeEnum # New Import


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

class IVendorRepository(IRepository[Vendor, int]): # ... (as defined previously)
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

# --- NEW: Product/Service Repository Interface ---
class IProductRepository(IRepository[Product, int]):
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None, # Filter by product type
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import CustomerService, VendorService
# ProductService will be in business_services.py, imported later when defined

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository", # Added IProductRepository
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService",
    # ProductService will be added here once defined
]
```

**Validation for `app/services/__init__.py`:**
*   Added `from app.models.business.product import Product`.
*   Added `ProductSummaryData` to the import from `app.utils.pydantic_models`.
*   Added `from app.common.enums import ProductTypeEnum`.
*   Defined `IProductRepository(IRepository[Product, int])` with the planned methods:
    *   `get_by_code(self, code: str) -> Optional[Product]`
    *   `get_all_summary(self, active_only: bool = True, product_type_filter: Optional[ProductTypeEnum] = None, search_term: Optional[str] = None, page: int = 1, page_size: int = 50) -> List[ProductSummaryData]`. Added `product_type_filter`.
*   Added `IProductRepository` to the `__all__` list.
*   No existing interfaces or exports were unintentionally modified.

This completes step A2 for Product/Service Management. The next step is A3: Implement `ProductService` in `app/services/business_services.py`.
