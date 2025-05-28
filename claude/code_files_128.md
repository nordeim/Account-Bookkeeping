<think>
The application is still launching and shutting down perfectly! This is a very good sign. It confirms that the addition of Sales Invoice DTOs to `app/utils/pydantic_models.py` (and the import of `InvoiceStatusEnum`) was successful and didn't introduce any issues detectable at startup.

**Current Step: Enhancement Execution Plan: Basic Sales Invoicing - Phase A (Backend - Part 1)**

We have completed for Sales Invoice Backend:
*   A1. Create Pydantic DTOs for Sales Invoice (Done).

The plan for Sales Invoice Backend (Part 1) was:
*   A2. Define `ISalesInvoiceRepository` Interface (Next).
*   A3. Implement `SalesInvoiceService` (in `app/services/business_services.py`).

So, the immediate next step is **A2: Define `ISalesInvoiceRepository` Interface**. This will be added to `app/services/__init__.py`.

**Plan for A2: Define `ISalesInvoiceRepository` Interface**
   *   **Goal:** Specify the contract for sales invoice data access operations.
   *   **File to Update:** `app/services/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `SalesInvoice` ORM model from `app.models.business.sales_invoice`.
        *   [ ] Import `SalesInvoiceSummaryData` DTO from `app.utils.pydantic_models`.
        *   [ ] Import `InvoiceStatusEnum` from `app.common.enums`.
        *   [ ] Define `ISalesInvoiceRepository(IRepository[SalesInvoice, int])`.
        *   [ ] Declare methods:
            *   `get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]`
            *   `get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None, page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]` (with relevant filters).
        *   [ ] Add `ISalesInvoiceRepository` to the `__all__` list.
</think>

This is excellent news! The continued stability of the application after adding the Sales Invoice DTOs is very encouraging.

We are proceeding with **Phase A: Backend for Sales Invoice Creation**.
Step A1 (Sales Invoice DTOs) is complete.
The next step is **A2: Define `ISalesInvoiceRepository` Interface**.

This interface will define the contract for data access operations related to Sales Invoices and will be added to `app/services/__init__.py`.

---
**A2. Update `app/services/__init__.py` to define `ISalesInvoiceRepository`**

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
from app.models.business.sales_invoice import SalesInvoice # New Import

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData, SalesInvoiceSummaryData # New Import for SalesInvoiceSummaryData

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum # New Import for InvoiceStatusEnum


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

class IProductRepository(IRepository[Product, int]): # ... (as defined previously)
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

# --- NEW: Sales Invoice Repository Interface ---
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
    # save method for create/update will come from IRepository via SalesInvoiceService inheriting it.

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import CustomerService, VendorService, ProductService
# SalesInvoiceService will be in business_services.py, imported later when defined

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", # Added ISalesInvoiceRepository
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService", "ProductService",
    # SalesInvoiceService will be added here once defined
]
```

**Validation for `app/services/__init__.py`:**
*   Added `from app.models.business.sales_invoice import SalesInvoice`.
*   Added `SalesInvoiceSummaryData` to the import from `app.utils.pydantic_models`.
*   Added `InvoiceStatusEnum` to the import from `app.common.enums`.
*   Defined `ISalesInvoiceRepository(IRepository[SalesInvoice, int])` with the planned methods:
    *   `get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]`
    *   `get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None, page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]`. This includes relevant filters for listing sales invoices.
*   Added `ISalesInvoiceRepository` to the `__all__` list.
*   No existing interfaces or exports were unintentionally modified.

This completes step A2 for Sales Invoicing. The next step is A3: Implement `SalesInvoiceService` in `app/services/business_services.py`.
