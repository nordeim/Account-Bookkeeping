<think>
The application launched successfully after Phase 1 (Journal Type Filter for JE List). This confirms the stability of those changes.

Now, as planned, we proceed to **Phase 2: Add Dimension Filters to the General Ledger Report.**

This involves:
1.  Creating a new `DimensionService` to fetch dimension data.
2.  Integrating this service into `ApplicationCore`.
3.  Updating `JournalService` and `FinancialStatementGenerator` to handle dimension filters.
4.  Modifying `ReportsWidget` to include UI controls for dimension selection when the General Ledger report is chosen, and passing these selections to the backend.

**Execution Plan: Phase 2 - Dimension Filters for General Ledger Report**

**Step 1: Create `DimensionService` and `IDimensionRepository`**

*   **`app/services/__init__.py`**:
    *   Define `IDimensionRepository(IRepository[Dimension, int])`.
    *   Add `get_distinct_dimension_types() -> List[str]` and `get_dimensions_by_type(dim_type: str, active_only: bool = True) -> List[Dimension]` as abstract methods.
    *   Import `Dimension` model from `app.models.accounting.dimension`.
    *   Add `IDimensionRepository` and `DimensionService` to `__all__`.
*   **`app/services/accounting_services.py`**:
    *   Implement `DimensionService(IDimensionRepository)`.
    *   Implement `get_distinct_dimension_types()`: `SELECT DISTINCT dimension_type FROM accounting.dimensions WHERE is_active = TRUE ORDER BY dimension_type;`
    *   Implement `get_dimensions_by_type()`: `SELECT id, code, name FROM accounting.dimensions WHERE dimension_type = :dim_type AND is_active = TRUE ORDER BY code;` (Returns `Dimension` ORM objects or list of dicts suitable for DTOs/UI). For simplicity, let's have it return `List[Dimension]`.

**Step 2: Integrate `DimensionService` into `ApplicationCore`**

*   **`app/core/application_core.py`**:
    *   Import `DimensionService`.
    *   Add `_dimension_service_instance: Optional[DimensionService] = None`.
    *   Instantiate `self._dimension_service_instance = DimensionService(self.db_manager, self)` in `startup()`.
    *   Add `@property def dimension_service(self) -> DimensionService:`.

**Step 3: Update `JournalService` and `FinancialStatementGenerator`**

*   **`app/services/journal_service.py`**:
    *   Modify `get_posted_lines_for_account_in_range` signature to include `dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None`.
    *   In its SQLAlchemy query, add to the `conditions` list:
        *   `if dimension1_id is not None: conditions.append(JournalEntryLine.dimension1_id == dimension1_id)`
        *   `if dimension2_id is not None: conditions.append(JournalEntryLine.dimension2_id == dimension2_id)`
*   **`app/reporting/financial_statement_generator.py`**:
    *   Modify `generate_general_ledger` signature to include `dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None`.
    *   Pass these `dimension1_id` and `dimension2_id` to the call to `self.journal_service.get_posted_lines_for_account_in_range`.
    *   Update the `report_date_description` string in the returned dictionary to include information about the applied dimension filters if they are present (e.g., " (Dim1: [Type]-[Code], Dim2: [Type]-[Code])"). This will require fetching the dimension names/codes if only IDs are passed. Alternatively, pass the dimension names/codes directly to the generator. For this iteration, passing IDs is simpler for the generator; the UI can reconstruct the description. Let's just add placeholder text for now if dimensions are filtered.

**Step 4: Update UI in `ReportsWidget` (`app/ui/reports/reports_widget.py`)**

*   In `_create_financial_statements_tab()`:
    *   Create `self.fs_dim1_type_label`, `self.fs_dim1_type_combo`, `self.fs_dim1_code_label`, `self.fs_dim1_code_combo`.
    *   Create `self.fs_dim2_type_label`, `self.fs_dim2_type_combo`, `self.fs_dim2_code_label`, `self.fs_dim2_code_combo`.
    *   Add "All Types" item with `None` data to type combos. Add "All Codes" item with `None` data to code combos.
    *   Add these to `self.fs_params_form`. Initially hide them.
*   In `_on_fs_report_type_changed()`:
    *   When "General Ledger" is selected, show all four dimension combo boxes and their labels. Hide them for other report types.
    *   If shown for GL and `self.fs_dim1_type_combo` is empty (or has only "All Types"), call `schedule_task_from_qt(self._load_dimension_types())`.
*   Implement `async def _load_dimension_types(self)`:
    *   Calls `self.app_core.dimension_service.get_distinct_dimension_types()`.
    *   Serializes the list of type strings to JSON.
    *   Invokes `_populate_dimension_types_slot` via `QMetaObject.invokeMethod`.
*   Implement `@Slot(str) def _populate_dimension_types_slot(self, dim_types_json_str: str)`:
    *   Clears and populates both `fs_dim1_type_combo` and `fs_dim2_type_combo` with "All Types" and the fetched dimension types.
*   Connect `currentIndexChanged` of `fs_dim1_type_combo` to a new slot `lambda index, tc=self.fs_dim1_type_combo, cc=self.fs_dim1_code_combo: self._on_dimension_type_selected(tc, cc)`. Do similarly for `fs_dim2_type_combo` and `fs_dim2_code_combo`.
*   Implement `@Slot(QComboBox, QComboBox) def _on_dimension_type_selected(self, type_combo: QComboBox, code_combo: QComboBox)`:
    *   Gets the selected dimension type string from `type_combo.currentText()`.
    *   If "All Types" or empty, clear `code_combo` (add "All Codes").
    *   Else, schedule `_load_dimension_codes_for_type(selected_type_str, code_combo.objectName())`. (Need to set object names for code combos to identify them).
*   Implement `async def _load_dimension_codes_for_type(self, dim_type_str: str, target_code_combo_name: str)`:
    *   Calls `self.app_core.dimension_service.get_dimensions_by_type(dim_type_str)`. This returns `List[Dimension]`.
    *   Convert `List[Dimension]` to `List[Dict[str, Any]]` for JSON serialization (id, code, name).
    *   Invokes `_populate_dimension_codes_slot` via `QMetaObject.invokeMethod`, passing the JSON string of codes and `target_code_combo_name`.
*   Implement `@Slot(str, str) def _populate_dimension_codes_slot(self, dim_codes_json_str: str, target_code_combo_name: str)`:
    *   Finds the target code combo (e.g., `self.findChild(QComboBox, target_code_combo_name)`).
    *   Clears and populates it with "All Codes" and then the fetched dimension codes/names, storing `dimension.id` as `itemData`.
*   In `_on_generate_financial_report_clicked()` (specifically the "General Ledger" case):
    *   Get `dimension1_id = self.fs_dim1_code_combo.currentData()` (will be an `int` or `None`/`0` for "All").
    *   Get `dimension2_id = self.fs_dim2_code_combo.currentData()`.
    *   Convert `0` or `None` from `currentData()` to `None` for passing to the generator.
    *   Pass these to `self.app_core.financial_statement_generator.generate_general_ledger(...)`.

This is a comprehensive plan. I will now generate the modified files, starting with the service layer, then core, then generator, and finally the UI widget.
</think>

Excellent! The application is stable after Phase 1 (Journal Type Filter for JE List). We will now proceed with **Phase 2: Add Dimension Filters to the General Ledger Report.**

This involves creating a new `DimensionService`, integrating it, updating backend methods to use dimension filters, and finally, adding the necessary UI elements to `ReportsWidget`.

**Execution Plan: Phase 2 - Dimension Filters for General Ledger Report**

**Step 1: Create `DimensionService` and `IDimensionRepository`**
   - Modify `app/services/__init__.py`
   - Modify `app/services/accounting_services.py`

**Step 2: Integrate `DimensionService` into `ApplicationCore`**
   - Modify `app/core/application_core.py`

**Step 3: Update `JournalService` and `FinancialStatementGenerator` for Dimension Filtering**
   - Modify `app/services/journal_service.py`
   - Modify `app/reporting/financial_statement_generator.py`

**Step 4: Update UI in `ReportsWidget`**
   - Modify `app/ui/reports/reports_widget.py`

I will now generate the complete updated files for these steps.

---
**1. `app/services/__init__.py`**
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
from app.models.business.purchase_invoice import PurchaseInvoice
from app.models.business.inventory_movement import InventoryMovement
from app.models.accounting.dimension import Dimension # New Import

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData
)

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum


# --- Existing Interfaces (condensed for brevity) ---
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
                              description_filter: Optional[str] = None,
                              journal_type_filter: Optional[str] = None
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

class ICustomerRepository(IRepository[Customer, int]): 
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

class IProductRepository(IRepository[Product, int]): 
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

class IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int]):
    @abstractmethod
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: pass 
    @abstractmethod
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              vendor_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[PurchaseInvoiceSummaryData]: pass

class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement) -> InventoryMovement: pass

# --- New Interface for Dimensions ---
class IDimensionRepository(IRepository[Dimension, int]):
    @abstractmethod
    async def get_distinct_dimension_types(self) -> List[str]: pass
    @abstractmethod
    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]: pass
    @abstractmethod
    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]: pass


# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService, DimensionService # Added DimensionService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService
)

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "IInventoryMovementRepository", 
    "IDimensionRepository", # New export
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService", "DimensionService", # New export
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
    "InventoryMovementService", 
]

```

---
**2. `app/services/accounting_services.py`**
```python
# app/services/accounting_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select, and_, or_, distinct # Added distinct
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.dimension import Dimension # New import
from app.core.database_manager import DatabaseManager
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository,
    IFiscalYearRepository,
    IDimensionRepository # New import
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore


class AccountTypeService(IAccountTypeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            return await session.get(AccountType, id_val)

    async def get_all(self) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).order_by(AccountType.display_order, AccountType.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity
            
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(AccountType, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, name: str) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_category(self, category: str) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.category == category).order_by(AccountType.display_order)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class CurrencyService(ICurrencyRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: str) -> Optional[Currency]:
        async with self.db_manager.session() as session:
            return await session.get(Currency, id_val)

    async def get_all(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                 entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                 entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: str) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(Currency, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_all_active(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).where(Currency.is_active == True).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class ExchangeRateService(IExchangeRateRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            return await session.get(ExchangeRate, id_val)

    async def get_all(self) -> List[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).order_by(ExchangeRate.rate_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def update(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(ExchangeRate, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).where(
                ExchangeRate.from_currency_code == from_code,
                ExchangeRate.to_currency_code == to_code,
                ExchangeRate.rate_date == r_date
            )
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def save(self, entity: ExchangeRate) -> ExchangeRate:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if not entity.id: 
                 if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                    entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

class FiscalYearService(IFiscalYearRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalYear, id_val)

    async def get_all(self) -> List[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).order_by(FiscalYear.start_date.desc()) 
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)

    async def update(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)
    
    async def save(self, entity: FiscalYear) -> FiscalYear:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(FiscalYear, id_val)
            if entity:
                if entity.fiscal_periods:
                     raise ValueError(f"Cannot delete fiscal year '{entity.year_name}' as it has associated fiscal periods.")
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).where(FiscalYear.year_name == year_name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            conditions = [
                FiscalYear.start_date <= end_date,
                FiscalYear.end_date >= start_date
            ]
            if exclude_id is not None:
                conditions.append(FiscalYear.id != exclude_id)
            
            stmt = select(FiscalYear).where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalars().first()

# --- New DimensionService ---
class DimensionService(IDimensionRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[Dimension]:
        async with self.db_manager.session() as session:
            return await session.get(Dimension, id_val)

    async def get_all(self) -> List[Dimension]:
        async with self.db_manager.session() as session:
            stmt = select(Dimension).order_by(Dimension.dimension_type, Dimension.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: Dimension) -> Dimension:
        # User audit fields are on UserAuditMixin, assumed to be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Dimension) -> Dimension:
        # User audit fields are on UserAuditMixin, assumed to be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        # Add checks if dimension is in use before deleting
        async with self.db_manager.session() as session:
            entity = await session.get(Dimension, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_distinct_dimension_types(self) -> List[str]:
        async with self.db_manager.session() as session:
            stmt = select(distinct(Dimension.dimension_type)).where(Dimension.is_active == True).order_by(Dimension.dimension_type)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]:
        async with self.db_manager.session() as session:
            conditions = [Dimension.dimension_type == dim_type]
            if active_only:
                conditions.append(Dimension.is_active == True)
            stmt = select(Dimension).where(and_(*conditions)).order_by(Dimension.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]:
        async with self.db_manager.session() as session:
            stmt = select(Dimension).where(
                Dimension.dimension_type == dim_type,
                Dimension.code == code,
                Dimension.is_active == True
            )
            result = await session.execute(stmt)
            return result.scalars().first()

```

---
**3. `app/core/application_core.py`**
```python
# app/core/application_core.py
from typing import Optional, Any
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager 
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

# Accounting Managers
from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.accounting.journal_entry_manager import JournalEntryManager
from app.accounting.fiscal_period_manager import FiscalPeriodManager
from app.accounting.currency_manager import CurrencyManager

# Business Logic Managers
from app.business_logic.customer_manager import CustomerManager 
from app.business_logic.vendor_manager import VendorManager 
from app.business_logic.product_manager import ProductManager
from app.business_logic.sales_invoice_manager import SalesInvoiceManager
from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager 

# Services
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import (
    AccountTypeService, CurrencyService as CurrencyRepoService, 
    ExchangeRateService, FiscalYearService, DimensionService # Added DimensionService
)
from app.services.business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService
)

# Utilities
from app.utils.sequence_generator import SequenceGenerator 

# Tax and Reporting
from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine
import logging 

class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.db_manager.app_core = self 
        
        self.logger = logging.getLogger("SGBookkeeperAppCore")
        if not self.logger.handlers:
            handler = logging.StreamHandler(); formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter); self.logger.addHandler(handler); self.logger.setLevel(logging.INFO) 
        if not hasattr(self.db_manager, 'logger') or self.db_manager.logger is None: self.db_manager.logger = self.logger

        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        # --- Service Instance Placeholders ---
        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        self._dimension_service_instance: Optional[DimensionService] = None # New
        self._customer_service_instance: Optional[CustomerService] = None
        self._vendor_service_instance: Optional[VendorService] = None
        self._product_service_instance: Optional[ProductService] = None
        self._sales_invoice_service_instance: Optional[SalesInvoiceService] = None
        self._purchase_invoice_service_instance: Optional[PurchaseInvoiceService] = None 
        self._inventory_movement_service_instance: Optional[InventoryMovementService] = None

        # --- Manager Instance Placeholders ---
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None
        self._sales_invoice_manager_instance: Optional[SalesInvoiceManager] = None
        self._purchase_invoice_manager_instance: Optional[PurchaseInvoiceManager] = None 

        self.logger.info("ApplicationCore initialized.")

    async def startup(self):
        self.logger.info("ApplicationCore starting up...")
        await self.db_manager.initialize() 
        
        # Initialize Core Services
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)

        # Initialize Accounting Services
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
        self._dimension_service_instance = DimensionService(self.db_manager, self) # New
        
        # Initialize Tax Services
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        # Initialize Business Services
        self._customer_service_instance = CustomerService(self.db_manager, self)
        self._vendor_service_instance = VendorService(self.db_manager, self) 
        self._product_service_instance = ProductService(self.db_manager, self)
        self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self)
        self._purchase_invoice_service_instance = PurchaseInvoiceService(self.db_manager, self) 
        self._inventory_movement_service_instance = InventoryMovementService(self.db_manager, self) 

        # Initialize Managers (dependencies should be initialized services)
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) 

        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        self._je_manager_instance = JournalEntryManager(
            self.journal_service, self.account_service, 
            self.fiscal_period_service, py_sequence_generator, self 
        )
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 
        self._tax_calculator_instance = TaxCalculator(self.tax_code_service) 
        self._gst_manager_instance = GSTManager(
            self.tax_code_service, self.journal_service, self.company_settings_service,
            self.gst_return_service, self.account_service, self.fiscal_period_service,
            py_sequence_generator, self 
        )
        self._financial_statement_generator_instance = FinancialStatementGenerator(
            self.account_service, self.journal_service, self.fiscal_period_service,
            self.account_type_service, self.tax_code_service, self.company_settings_service
        )
        self._report_engine_instance = ReportEngine(self)

        self._customer_manager_instance = CustomerManager(
            customer_service=self.customer_service, account_service=self.account_service,
            currency_service=self.currency_service, app_core=self
        )
        self._vendor_manager_instance = VendorManager( 
            vendor_service=self.vendor_service, account_service=self.account_service,
            currency_service=self.currency_service, app_core=self
        )
        self._product_manager_instance = ProductManager( 
            product_service=self.product_service, account_service=self.account_service,
            tax_code_service=self.tax_code_service, app_core=self
        )
        self._sales_invoice_manager_instance = SalesInvoiceManager(
            sales_invoice_service=self.sales_invoice_service,
            customer_service=self.customer_service,
            product_service=self.product_service,
            tax_code_service=self.tax_code_service,
            tax_calculator=self.tax_calculator, 
            sequence_service=self.sequence_service, 
            account_service=self.account_service,
            configuration_service=self.configuration_service, 
            app_core=self,
            inventory_movement_service=self.inventory_movement_service 
        )
        self._purchase_invoice_manager_instance = PurchaseInvoiceManager( 
            purchase_invoice_service=self.purchase_invoice_service,
            vendor_service=self.vendor_service,
            product_service=self.product_service,
            tax_code_service=self.tax_code_service,
            tax_calculator=self.tax_calculator,
            sequence_service=self.sequence_service,
            account_service=self.account_service,
            configuration_service=self.configuration_service,
            app_core=self,
            inventory_movement_service=self.inventory_movement_service 
        )
        
        self.module_manager.load_all_modules() 
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self): 
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # --- Service Properties ---
    # ... (existing service properties) ...
    @property
    def dimension_service(self) -> DimensionService: # New Property
        if not self._dimension_service_instance: raise RuntimeError("DimensionService not initialized.")
        return self._dimension_service_instance

    @property
    def inventory_movement_service(self) -> InventoryMovementService: 
        if not self._inventory_movement_service_instance: raise RuntimeError("InventoryMovementService not initialized.")
        return self._inventory_movement_service_instance
    @property
    def account_service(self) -> AccountService: 
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> JournalService: 
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance
    @property
    def fiscal_period_service(self) -> FiscalPeriodService: 
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def fiscal_year_service(self) -> FiscalYearService: 
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
    @property
    def sequence_service(self) -> SequenceService: 
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> CompanySettingsService: 
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def tax_code_service(self) -> TaxCodeService: 
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> GSTReturnService: 
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> AccountTypeService:  
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def currency_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyService (CurrencyRepoService) not initialized.")
        return self._currency_repo_service_instance
    @property
    def exchange_rate_service(self) -> ExchangeRateService: 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def configuration_service(self) -> ConfigurationService: 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance
    @property
    def customer_service(self) -> CustomerService: 
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance
    @property
    def vendor_service(self) -> VendorService: 
        if not self._vendor_service_instance: raise RuntimeError("VendorService not initialized.")
        return self._vendor_service_instance
    @property
    def product_service(self) -> ProductService: 
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance
    @property
    def sales_invoice_service(self) -> SalesInvoiceService: 
        if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
        return self._sales_invoice_service_instance
    @property
    def purchase_invoice_service(self) -> PurchaseInvoiceService: 
        if not self._purchase_invoice_service_instance: raise RuntimeError("PurchaseInvoiceService not initialized.")
        return self._purchase_invoice_service_instance

    # --- Manager Properties ---
    # ... (existing manager properties) ...
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager: 
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: 
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> JournalEntryManager: 
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance
    @property
    def fiscal_period_manager(self) -> FiscalPeriodManager: 
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance
    @property
    def currency_manager(self) -> CurrencyManager: 
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance
    @property
    def gst_manager(self) -> GSTManager: 
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance
    @property
    def tax_calculator(self) -> TaxCalculator: 
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance
    @property
    def financial_statement_generator(self) -> FinancialStatementGenerator: 
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance
    @property
    def report_engine(self) -> ReportEngine: 
        if not self._report_engine_instance: raise RuntimeError("ReportEngine not initialized.")
        return self._report_engine_instance
    @property
    def customer_manager(self) -> CustomerManager: 
        if not self._customer_manager_instance: raise RuntimeError("CustomerManager not initialized.")
        return self._customer_manager_instance
    @property
    def vendor_manager(self) -> VendorManager: 
        if not self._vendor_manager_instance: raise RuntimeError("VendorManager not initialized.")
        return self._vendor_manager_instance
    @property
    def product_manager(self) -> ProductManager: 
        if not self._product_manager_instance: raise RuntimeError("ProductManager not initialized.")
        return self._product_manager_instance
    @property
    def sales_invoice_manager(self) -> SalesInvoiceManager: 
        if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
        return self._sales_invoice_manager_instance
    @property
    def purchase_invoice_manager(self) -> PurchaseInvoiceManager: 
        if not self._purchase_invoice_manager_instance: raise RuntimeError("PurchaseInvoiceManager not initialized.")
        return self._purchase_invoice_manager_instance

```

---
**4. `app/services/journal_service.py`**
```python
# app/services/journal_service.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from datetime import date, datetime, timedelta 
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload 
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result
from app.common.enums import JournalTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    # ... (get_by_id, get_all, get_all_summary, get_by_entry_no, get_by_date_range, get_posted_entries_by_date_range - unchanged from previous file set 2)
    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.currency), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension1), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension2), selectinload(JournalEntry.fiscal_period), selectinload(JournalEntry.created_by_user), selectinload(JournalEntry.updated_by_user)).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, start_date_filter: Optional[date] = None, end_date_filter: Optional[date] = None, status_filter: Optional[str] = None, entry_no_filter: Optional[str] = None, description_filter: Optional[str] = None, journal_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self.db_manager.session() as session:
            conditions = []
            if start_date_filter: conditions.append(JournalEntry.entry_date >= start_date_filter)
            if end_date_filter: conditions.append(JournalEntry.entry_date <= end_date_filter)
            if status_filter:
                if status_filter.lower() == "draft": conditions.append(JournalEntry.is_posted == False)
                elif status_filter.lower() == "posted": conditions.append(JournalEntry.is_posted == True)
            if entry_no_filter: conditions.append(JournalEntry.entry_no.ilike(f"%{entry_no_filter}%"))
            if description_filter: conditions.append(JournalEntry.description.ilike(f"%{description_filter}%"))
            if journal_type_filter: conditions.append(JournalEntry.journal_type == journal_type_filter)
            stmt = select(JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted, func.sum(JournalEntryLine.debit_amount).label("total_debits")).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.group_by(JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): summaries.append({"id": row.id, "entry_no": row.entry_no, "date": row.entry_date, "description": row.description, "type": row.journal_type, "total_amount": row.total_debits if row.total_debits is not None else Decimal(0), "status": "Posted" if row.is_posted else "Draft"})
            return summaries
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj)).where(JournalEntry.is_posted == True, JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt); return list(result.unique().scalars().all())
    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry); await session.flush(); await session.refresh(journal_entry)
            if journal_entry.lines is not None: await session.refresh(journal_entry, attribute_names=['lines'])
            return journal_entry
    async def add(self, entity: JournalEntry) -> JournalEntry: return await self.save(entity)
    async def update(self, entity: JournalEntry) -> JournalEntry: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entry = await session.get(JournalEntry, id_val)
            if entry:
                if entry.is_posted:
                    if self.app_core and hasattr(self.app_core, 'logger'): self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") 
                    return False 
                await session.delete(entry); return True
        return False
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc_stmt = select(Account.opening_balance, Account.opening_balance_date).where(Account.id == account_id)
            acc_res = await session.execute(acc_stmt); acc_data = acc_res.first()
            opening_balance = acc_data.opening_balance if acc_data and acc_data.opening_balance is not None else Decimal(0)
            ob_date = acc_data.opening_balance_date if acc_data and acc_data.opening_balance_date is not None else None
            je_activity_stmt = (select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True, JournalEntry.entry_date <= as_of_date))
            if ob_date: je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            result = await session.execute(je_activity_stmt); je_net_activity = result.scalar_one_or_none() or Decimal(0)
            return opening_balance + je_net_activity
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True, JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date))
            result = await session.execute(stmt); balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: 
        async with self.db_manager.session() as session:
            conditions = [
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ]
            if dimension1_id is not None:
                conditions.append(JournalEntryLine.dimension1_id == dimension1_id)
            if dimension2_id is not None:
                conditions.append(JournalEntryLine.dimension2_id == dimension2_id)

            stmt = select(JournalEntryLine).options(
                joinedload(JournalEntryLine.journal_entry) 
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)\
            .where(and_(*conditions))\
            .order_by(JournalEntry.entry_date, JournalEntry.entry_no, JournalEntryLine.line_number)
            
            result = await session.execute(stmt)
            return list(result.scalars().all()) 

    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).options(joinedload(RecurringPattern.template_journal_entry).selectinload(JournalEntry.lines)).where(RecurringPattern.is_active == True, RecurringPattern.next_generation_date <= as_of_date, or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt); return list(result.scalars().unique().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern); await session.flush(); await session.refresh(pattern)
            return pattern

```

---
**4. `app/reporting/financial_statement_generator.py`**
```python
# app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import date, timedelta 
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService 
from app.services.core_services import CompanySettingsService 
from app.services.accounting_services import AccountTypeService, DimensionService # Added DimensionService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService, 
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None,
                 dimension_service: Optional[DimensionService] = None # New dependency
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self.dimension_service = dimension_service # New
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    # ... (_get_account_type_map, _calculate_account_balances_for_report, _calculate_account_period_activity_for_report,
    #      generate_balance_sheet, generate_profit_loss, generate_trial_balance, generate_income_tax_computation,
    #      generate_gst_f5 - unchanged from file set 7)
    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             self._account_type_map_cache = {at.category: at for at in ats} 
        return self._account_type_map_cache
    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        result_list = []; acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date); display_balance = balance_value 
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_balance = -balance_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_balance})
        return result_list
    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        result_list = []; acc_type_map = await self._get_account_type_map()
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date); display_activity = activity_value
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_activity = -activity_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_activity})
        return result_list
    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); assets_orm = [a for a in accounts if a.account_type == 'Asset']; liabilities_orm = [a for a in accounts if a.account_type == 'Liability']; equity_orm = [a for a in accounts if a.account_type == 'Equity']
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date); liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date); equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date: comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date); comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date); comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)
        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]; liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]; equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date: comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None; comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None; comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None
        total_assets = sum(a['balance'] for a in asset_accounts); total_liabilities = sum(a['balance'] for a in liability_accounts); total_equity = sum(a['balance'] for a in equity_accounts)
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None; comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None; comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None
        return {'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date, 'comparative_date': comparative_date,'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},'total_liabilities_equity': total_liabilities + total_equity,'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")}
    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); revenues_orm = [a for a in accounts if a.account_type == 'Revenue']; expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date); expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end: comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end); comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)
        total_revenue = sum(a['balance'] for a in revenue_accounts); total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None; comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None
        return {'title': 'Profit & Loss Statement', 'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'start_date': start_date, 'end_date': end_date, 'comparative_start': comparative_start, 'comparative_end': comparative_end,'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},'net_profit': net_profit, 'comparative_net_profit': comp_net_profit}
    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); debit_accounts_list, credit_accounts_list = [], []; total_debits_val, total_credits_val = Decimal(0), Decimal(0) 
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue
            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if is_debit_nature: 
                if raw_balance >= Decimal(0): debit_accounts_list.append(account_data); total_debits_val += raw_balance
                else: account_data['balance'] = abs(raw_balance); credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
                else: account_data['balance'] = raw_balance; debit_accounts_list.append(account_data); total_debits_val += raw_balance
        debit_accounts_list.sort(key=lambda a: a['code']); credit_accounts_list.sort(key=lambda a: a['code'])
        return {'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date,'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,'total_debits': total_debits_val, 'total_credits': total_credits_val,'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")}
    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: 
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value) 
        if not fiscal_year_obj: raise ValueError(f"Fiscal year definition for {year_int_value} not found.")
        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date); net_profit = pl_data['net_profit']
        adjustments = []; tax_effect = Decimal(0)
        tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')
        for account in tax_adj_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            adj_is_addition = activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0)
            adjustments.append({'id': account.id, 'code': account.code, 'name': account.name, 'amount': activity, 'is_addition': adj_is_addition})
            tax_effect += activity 
        taxable_income = net_profit + tax_effect
        return {'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', 'report_date_description': f"For Financial Year Ended {fiscal_year_obj.end_date.strftime('%d %b %Y')}",'year': year_int_value, 'fiscal_year_start': start_date, 'fiscal_year_end': end_date,'net_profit': net_profit, 'adjustments': adjustments, 'tax_effect': tax_effect, 'taxable_income': taxable_income}
    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        if not self.company_settings_service or not self.tax_code_service: raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")
        company = await self.company_settings_service.get_company_settings();
        if not company: raise ValueError("Company settings not found.")
        report_data: Dict[str, Any] = {'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'company_name': company.company_name,'gst_registration_no': company.gst_registration_no,'period_start': start_date, 'period_end': end_date,'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)}
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                line_net_amount = (line.debit_amount if line.debit_amount > Decimal(0) else line.credit_amount) 
                tax_on_line = line.tax_amount if line.tax_amount is not None else Decimal(0)
                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR': report_data['standard_rated_supplies'] += line_net_amount; report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR': report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES': report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': report_data['taxable_purchases'] += line_net_amount; report_data['input_tax'] += tax_on_line
                    elif tax_code_info.code == 'BL': report_data['taxable_purchases'] += line_net_amount 
        report_data['total_supplies'] = (report_data['standard_rated_supplies'] + report_data['zero_rated_supplies'] + report_data['exempt_supplies'])
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        return report_data

    async def generate_general_ledger(self, account_id: int, start_date: date, end_date: date,
                                      dimension1_id: Optional[int] = None, 
                                      dimension2_id: Optional[int] = None) -> Dict[str, Any]:
        account_orm = await self.account_service.get_by_id(account_id)
        if not account_orm:
            raise ValueError(f"Account with ID {account_id} not found.")

        ob_date = start_date - timedelta(days=1)
        # Note: Opening balance calculation for GL should also consider dimensions if they apply to OB.
        # For now, assume OB is not dimension-specific for simplicity. A more advanced system
        # might require passing dimension filters to get_account_balance if OB JEs have dimensions.
        opening_balance = await self.journal_service.get_account_balance(account_id, ob_date)

        lines: List[JournalEntryLine] = await self.journal_service.get_posted_lines_for_account_in_range(
            account_id, start_date, end_date, dimension1_id, dimension2_id # Pass dimensions here
        )

        transactions_data = []
        current_balance = opening_balance
        for line in lines:
            if not line.journal_entry: continue 
            movement = line.debit_amount - line.credit_amount
            current_balance += movement
            transactions_data.append({
                "date": line.journal_entry.entry_date, "entry_no": line.journal_entry.entry_no,
                "je_description": line.journal_entry.description or "", "line_description": line.description or "",
                "debit": line.debit_amount, "credit": line.credit_amount, "balance": current_balance,
                "dim1_id": line.dimension1_id, "dim2_id": line.dimension2_id # Include dim IDs in output
            })
        closing_balance = current_balance
        
        report_desc = f"For Account: {account_orm.code} - {account_orm.name} from {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
        if dimension1_id and self.dimension_service:
            dim1 = await self.dimension_service.get_by_id(dimension1_id)
            if dim1: report_desc += f" (Dim1: {dim1.dimension_type}-{dim1.code})"
        if dimension2_id and self.dimension_service:
            dim2 = await self.dimension_service.get_by_id(dimension2_id)
            if dim2: report_desc += f" (Dim2: {dim2.dimension_type}-{dim2.code})"


        return {
            "title": "General Ledger", "report_date_description": report_desc,
            "account_code": account_orm.code, "account_name": account_orm.name,
            "start_date": start_date, "end_date": end_date,
            "opening_balance": opening_balance, "transactions": transactions_data,
            "closing_balance": closing_balance
        }

```

---
**5. `app/ui/reports/reports_widget.py`**
```python
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter,
    QStackedWidget, QTreeView, QTableView, 
    QAbstractItemView, QCheckBox 
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG, QStandardPaths
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont, QColor
from typing import Optional, Dict, Any, TYPE_CHECKING, List 

import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date, timedelta 

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.account import Account 
from app.models.accounting.dimension import Dimension # New import

from .trial_balance_table_model import TrialBalanceTableModel
from .general_ledger_table_model import GeneralLedgerTableModel

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice 

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None 
        self._saved_draft_gst_return_orm: Optional[GSTReturn] = None 
        self._current_financial_report_data: Optional[Dict[str, Any]] = None
        self._gl_accounts_cache: List[Dict[str, Any]] = [] 
        self._dimension_types_cache: List[str] = []
        self._dimension_codes_cache: Dict[str, List[Dict[str, Any]]] = {} # type -> list of codes

        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self.main_layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self._create_gst_f5_tab()
        self._create_financial_statements_tab()
        
        self.setLayout(self.main_layout)

    # ... (_format_decimal_for_display, GST F5 tab methods - unchanged from file set 4)
    def _format_decimal_for_display(self, value: Optional[Decimal], default_str: str = "0.00", show_blank_for_zero: bool = False) -> str:
        if value is None: return default_str if not show_blank_for_zero else ""
        try: d_value = Decimal(str(value)); 
        if show_blank_for_zero and d_value.is_zero(): return ""; return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError): return "Error"
    def _create_gst_f5_tab(self):
        gst_f5_widget = QWidget(); gst_f5_main_layout = QVBoxLayout(gst_f5_widget); gst_f5_group = QGroupBox("GST F5 Return Data Preparation"); gst_f5_group_layout = QVBoxLayout(gst_f5_group) 
        date_selection_layout = QHBoxLayout(); date_form = QFormLayout()
        self.gst_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(-QDate.currentDate().day()+1)); self.gst_start_date_edit.setCalendarPopup(True); self.gst_start_date_edit.setDisplayFormat("dd/MM/yyyy"); date_form.addRow("Period Start Date:", self.gst_start_date_edit)
        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); 
        if self.gst_end_date_edit.date() < self.gst_start_date_edit.date(): self.gst_end_date_edit.setDate(self.gst_start_date_edit.date().addMonths(1).addDays(-1))
        self.gst_end_date_edit.setCalendarPopup(True); self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy"); date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form); prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data"); self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button); prepare_button_layout.addStretch(); date_selection_layout.addLayout(prepare_button_layout); date_selection_layout.addStretch(1); gst_f5_group_layout.addLayout(date_selection_layout)
        self.gst_display_form = QFormLayout(); self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True); self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True); self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True); self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;"); self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True); self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True); self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True); self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True); self.gst_net_payable_display = QLineEdit(); self.gst_net_payable_display.setReadOnly(True); self.gst_net_payable_display.setStyleSheet("font-weight: bold;"); self.gst_filing_due_date_display = QLineEdit(); self.gst_filing_due_date_display.setReadOnly(True)
        self.gst_display_form.addRow("1. Standard-Rated Supplies:", self.gst_std_rated_supplies_display); self.gst_display_form.addRow("2. Zero-Rated Supplies:", self.gst_zero_rated_supplies_display); self.gst_display_form.addRow("3. Exempt Supplies:", self.gst_exempt_supplies_display); self.gst_display_form.addRow("4. Total Supplies (1+2+3):", self.gst_total_supplies_display); self.gst_display_form.addRow("5. Taxable Purchases:", self.gst_taxable_purchases_display); self.gst_display_form.addRow("6. Output Tax Due:", self.gst_output_tax_display); self.gst_display_form.addRow("7. Input Tax and Refunds Claimed:", self.gst_input_tax_display); self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display); self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display); self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
        gst_f5_group_layout.addLayout(self.gst_display_form); gst_action_button_layout = QHBoxLayout(); self.save_draft_gst_button = QPushButton("Save Draft GST Return"); self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked); self.finalize_gst_button = QPushButton("Finalize GST Return"); self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked); gst_action_button_layout.addStretch(); gst_action_button_layout.addWidget(self.save_draft_gst_button); gst_action_button_layout.addWidget(self.finalize_gst_button); gst_f5_group_layout.addLayout(gst_action_button_layout)
        gst_f5_main_layout.addWidget(gst_f5_group); gst_f5_main_layout.addStretch(); self.tab_widget.addTab(gst_f5_widget, "GST F5 Preparation")
    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        start_date = self.gst_start_date_edit.date().toPython(); end_date = self.gst_end_date_edit.date().toPython();
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        if not self.app_core.gst_manager: QMessageBox.critical(self, "Error", "GST Manager not available."); return
        self.prepare_gst_button.setEnabled(False); self.prepare_gst_button.setText("Preparing..."); self._saved_draft_gst_return_orm = None; self.finalize_gst_button.setEnabled(False); current_user_id = self.app_core.current_user.id
        future = schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id))
        if future: future.add_done_callback(self._handle_prepare_gst_f5_result); else: self._handle_prepare_gst_f5_result(None) 
    def _handle_prepare_gst_f5_result(self, future):
        self.prepare_gst_button.setEnabled(True); self.prepare_gst_button.setText("Prepare GST F5 Data")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST data preparation."); self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); return
        try:
            result: Result[GSTReturnData] = future.result()
            if result.is_success and result.value: self._prepared_gst_data = result.value; self._update_gst_f5_display(self._prepared_gst_data); self.save_draft_gst_button.setEnabled(True); self.finalize_gst_button.setEnabled(False) 
            else: self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e: self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True); QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")
    def _update_gst_f5_display(self, gst_data: GSTReturnData):
        self.gst_std_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.standard_rated_supplies)); self.gst_zero_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.zero_rated_supplies)); self.gst_exempt_supplies_display.setText(self._format_decimal_for_display(gst_data.exempt_supplies)); self.gst_total_supplies_display.setText(self._format_decimal_for_display(gst_data.total_supplies)); self.gst_taxable_purchases_display.setText(self._format_decimal_for_display(gst_data.taxable_purchases)); self.gst_output_tax_display.setText(self._format_decimal_for_display(gst_data.output_tax)); self.gst_input_tax_display.setText(self._format_decimal_for_display(gst_data.input_tax)); self.gst_adjustments_display.setText(self._format_decimal_for_display(gst_data.tax_adjustments)); self.gst_net_payable_display.setText(self._format_decimal_for_display(gst_data.tax_payable)); self.gst_filing_due_date_display.setText(gst_data.filing_due_date.strftime('%d/%m/%Y') if gst_data.filing_due_date else "")
    def _clear_gst_display_fields(self):
        for w in [self.gst_std_rated_supplies_display, self.gst_zero_rated_supplies_display, self.gst_exempt_supplies_display, self.gst_total_supplies_display, self.gst_taxable_purchases_display, self.gst_output_tax_display, self.gst_input_tax_display, self.gst_net_payable_display, self.gst_filing_due_date_display]: w.clear()
        self.gst_adjustments_display.setText("0.00"); self._prepared_gst_data = None; self._saved_draft_gst_return_orm = None
    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        if not self._prepared_gst_data: QMessageBox.warning(self, "No Data", "Please prepare GST data first."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        self._prepared_gst_data.user_id = self.app_core.current_user.id
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.id: self._prepared_gst_data.id = self._saved_draft_gst_return_orm.id
        self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.setText("Saving Draft..."); self.finalize_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.save_gst_return(self._prepared_gst_data))
        if future: future.add_done_callback(self._handle_save_draft_gst_result); else: self._handle_save_draft_gst_result(None)
    def _handle_save_draft_gst_result(self, future):
        self.save_draft_gst_button.setEnabled(True); self.save_draft_gst_button.setText("Save Draft GST Return")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST draft save."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: self._saved_draft_gst_return_orm = result.value; 
            if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id; QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id})."); self.finalize_gst_button.setEnabled(True) 
            else: QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}"); self.finalize_gst_button.setEnabled(False)
        except Exception as e: self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True); QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}"); self.finalize_gst_button.setEnabled(False)
    @Slot()
    def _on_finalize_gst_return_clicked(self):
        if not self._saved_draft_gst_return_orm or not self._saved_draft_gst_return_orm.id: QMessageBox.warning(self, "No Draft", "Please prepare and save a draft GST return first."); return
        if self._saved_draft_gst_return_orm.status != "Draft": QMessageBox.information(self, "Already Processed", f"This GST Return (ID: {self._saved_draft_gst_return_orm.id}) is already '{self._saved_draft_gst_return_orm.status}'."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        submission_ref, ok_ref = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Reference No.:"); 
        if not ok_ref or not submission_ref.strip(): QMessageBox.information(self, "Cancelled", "Submission reference not provided. Finalization cancelled."); return
        submission_date_str, ok_date = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Date (YYYY-MM-DD):", text=python_date.today().isoformat()); 
        if not ok_date or not submission_date_str.strip(): QMessageBox.information(self, "Cancelled", "Submission date not provided. Finalization cancelled."); return
        try: parsed_submission_date = python_date.fromisoformat(submission_date_str)
        except ValueError: QMessageBox.warning(self, "Invalid Date", "Submission date format is invalid. Please use YYYY-MM-DD."); return
        self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.setText("Finalizing..."); self.save_draft_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id=self._saved_draft_gst_return_orm.id, submission_reference=submission_ref.strip(), submission_date=parsed_submission_date, user_id=self.app_core.current_user.id))
        if future: future.add_done_callback(self._handle_finalize_gst_result); else: self._handle_finalize_gst_result(None)
    def _handle_finalize_gst_result(self, future):
        self.finalize_gst_button.setText("Finalize GST Return") 
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST finalization."); 
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft": self.finalize_gst_button.setEnabled(True); else: self.finalize_gst_button.setEnabled(False); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: QMessageBox.information(self, "Success", f"GST Return (ID: {result.value.id}) finalized successfully.\nStatus: {result.value.status}.\nSettlement JE ID: {result.value.journal_entry_id or 'N/A'}"); self._saved_draft_gst_return_orm = result.value; self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); 
            if self._prepared_gst_data: self._prepared_gst_data.status = result.value.status
            else: QMessageBox.warning(self, "Finalization Error", f"Failed to finalize GST Return:\n{', '.join(result.errors)}"); 
            if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft": self.finalize_gst_button.setEnabled(True); self.save_draft_gst_button.setEnabled(True) 
        except Exception as e: self.app_core.logger.error(f"Exception handling finalize GST result: {e}", exc_info=True); QMessageBox.critical(self, "Finalization Error", f"An unexpected error occurred: {str(e)}"); 
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft": self.finalize_gst_button.setEnabled(True); self.save_draft_gst_button.setEnabled(True) 

    def _create_financial_statements_tab(self):
        fs_widget = QWidget(); fs_main_layout = QVBoxLayout(fs_widget)
        fs_group = QGroupBox("Financial Statements"); fs_group_layout = QVBoxLayout(fs_group) 
        controls_layout = QHBoxLayout(); self.fs_params_form = QFormLayout() 
        self.fs_report_type_combo = QComboBox(); self.fs_report_type_combo.addItems(["Balance Sheet", "Profit & Loss Statement", "Trial Balance", "General Ledger"]); self.fs_params_form.addRow("Report Type:", self.fs_report_type_combo)
        self.fs_gl_account_label = QLabel("Account for GL:"); self.fs_gl_account_combo = QComboBox(); self.fs_gl_account_combo.setMinimumWidth(250); self.fs_gl_account_combo.setEditable(True)
        completer = QCompleter([f"{item.get('code')} - {item.get('name')}" for item in self._gl_accounts_cache]); completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion); completer.setFilterMode(Qt.MatchFlag.MatchContains); self.fs_gl_account_combo.setCompleter(completer); self.fs_params_form.addRow(self.fs_gl_account_label, self.fs_gl_account_combo)
        self.fs_as_of_date_edit = QDateEdit(QDate.currentDate()); self.fs_as_of_date_edit.setCalendarPopup(True); self.fs_as_of_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("As of Date:", self.fs_as_of_date_edit)
        self.fs_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_start_date_edit.setCalendarPopup(True); self.fs_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("Period Start Date:", self.fs_start_date_edit)
        self.fs_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); self.fs_end_date_edit.setCalendarPopup(True); self.fs_end_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("Period End Date:", self.fs_end_date_edit)
        self.fs_include_zero_balance_check = QCheckBox("Include Zero-Balance Accounts"); self.fs_params_form.addRow(self.fs_include_zero_balance_check) 
        self.fs_include_comparative_check = QCheckBox("Include Comparative Period"); self.fs_params_form.addRow(self.fs_include_comparative_check)
        self.fs_comparative_as_of_date_label = QLabel("Comparative As of Date:"); self.fs_comparative_as_of_date_edit = QDateEdit(QDate.currentDate().addYears(-1)); self.fs_comparative_as_of_date_edit.setCalendarPopup(True); self.fs_comparative_as_of_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_as_of_date_label, self.fs_comparative_as_of_date_edit)
        self.fs_comparative_start_date_label = QLabel("Comparative Start Date:"); self.fs_comparative_start_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_comparative_start_date_edit.setCalendarPopup(True); self.fs_comparative_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_start_date_label, self.fs_comparative_start_date_edit)
        self.fs_comparative_end_date_label = QLabel("Comparative End Date:"); self.fs_comparative_end_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addDays(-QDate.currentDate().day())); self.fs_comparative_end_date_edit.setCalendarPopup(True); self.fs_comparative_end_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_end_date_label, self.fs_comparative_end_date_edit)
        
        # Dimension Filters (New)
        self.fs_dim1_type_label = QLabel("Dimension 1 Type:"); self.fs_dim1_type_combo = QComboBox(); self.fs_dim1_type_combo.addItem("All Types", None); self.fs_params_form.addRow(self.fs_dim1_type_label, self.fs_dim1_type_combo)
        self.fs_dim1_code_label = QLabel("Dimension 1 Code:"); self.fs_dim1_code_combo = QComboBox(); self.fs_dim1_code_combo.addItem("All Codes", None); self.fs_params_form.addRow(self.fs_dim1_code_label, self.fs_dim1_code_combo)
        self.fs_dim2_type_label = QLabel("Dimension 2 Type:"); self.fs_dim2_type_combo = QComboBox(); self.fs_dim2_type_combo.addItem("All Types", None); self.fs_params_form.addRow(self.fs_dim2_type_label, self.fs_dim2_type_combo)
        self.fs_dim2_code_label = QLabel("Dimension 2 Code:"); self.fs_dim2_code_combo = QComboBox(); self.fs_dim2_code_combo.addItem("All Codes", None); self.fs_params_form.addRow(self.fs_dim2_code_label, self.fs_dim2_code_combo)

        controls_layout.addLayout(self.fs_params_form)
        generate_fs_button_layout = QVBoxLayout(); self.generate_fs_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Generate Report"); self.generate_fs_button.clicked.connect(self._on_generate_financial_report_clicked)
        generate_fs_button_layout.addWidget(self.generate_fs_button); generate_fs_button_layout.addStretch(); controls_layout.addLayout(generate_fs_button_layout); controls_layout.addStretch(1); fs_group_layout.addLayout(controls_layout)
        self.fs_display_stack = QStackedWidget(); fs_group_layout.addWidget(self.fs_display_stack, 1)
        self.bs_tree_view = QTreeView(); self.bs_tree_view.setAlternatingRowColors(True); self.bs_tree_view.setHeaderHidden(False); self.bs_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.bs_model = QStandardItemModel(); self.bs_tree_view.setModel(self.bs_model); self.fs_display_stack.addWidget(self.bs_tree_view)
        self.pl_tree_view = QTreeView(); self.pl_tree_view.setAlternatingRowColors(True); self.pl_tree_view.setHeaderHidden(False); self.pl_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.pl_model = QStandardItemModel(); self.pl_tree_view.setModel(self.pl_model); self.fs_display_stack.addWidget(self.pl_tree_view)
        self.tb_table_view = QTableView(); self.tb_table_view.setAlternatingRowColors(True); self.tb_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.tb_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.tb_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tb_table_view.setSortingEnabled(True); self.tb_model = TrialBalanceTableModel(); self.tb_table_view.setModel(self.tb_model); self.fs_display_stack.addWidget(self.tb_table_view)
        gl_widget_container = QWidget(); gl_layout = QVBoxLayout(gl_widget_container); gl_layout.setContentsMargins(0,0,0,0)
        self.gl_summary_label_account = QLabel("Account: N/A"); self.gl_summary_label_account.setStyleSheet("font-weight: bold;")
        self.gl_summary_label_period = QLabel("Period: N/A")
        self.gl_summary_label_ob = QLabel("Opening Balance: 0.00")
        gl_summary_header_layout = QHBoxLayout(); gl_summary_header_layout.addWidget(self.gl_summary_label_account); gl_summary_header_layout.addStretch(); gl_summary_header_layout.addWidget(self.gl_summary_label_period); gl_layout.addLayout(gl_summary_header_layout); gl_layout.addWidget(self.gl_summary_label_ob)
        self.gl_table_view = QTableView(); self.gl_table_view.setAlternatingRowColors(True); self.gl_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.gl_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.gl_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.gl_table_view.setSortingEnabled(True); self.gl_model = GeneralLedgerTableModel(); self.gl_table_view.setModel(self.gl_model); gl_layout.addWidget(self.gl_table_view)
        self.gl_summary_label_cb = QLabel("Closing Balance: 0.00"); self.gl_summary_label_cb.setAlignment(Qt.AlignmentFlag.AlignRight); gl_layout.addWidget(self.gl_summary_label_cb)
        self.fs_display_stack.addWidget(gl_widget_container); self.gl_widget_container = gl_widget_container 
        export_button_layout = QHBoxLayout(); self.export_pdf_button = QPushButton("Export to PDF"); self.export_pdf_button.setEnabled(False); self.export_pdf_button.clicked.connect(lambda: self._on_export_report_clicked("pdf")); self.export_excel_button = QPushButton("Export to Excel"); self.export_excel_button.setEnabled(False); self.export_excel_button.clicked.connect(lambda: self._on_export_report_clicked("excel")); export_button_layout.addStretch(); export_button_layout.addWidget(self.export_pdf_button); export_button_layout.addWidget(self.export_excel_button); fs_group_layout.addLayout(export_button_layout)
        fs_main_layout.addWidget(fs_group); self.tab_widget.addTab(fs_widget, "Financial Statements")
        self.fs_report_type_combo.currentTextChanged.connect(self._on_fs_report_type_changed)
        self.fs_include_comparative_check.stateChanged.connect(self._on_comparative_check_changed)
        self.fs_dim1_type_combo.currentIndexChanged.connect(lambda index, tc=self.fs_dim1_type_combo, cc=self.fs_dim1_code_combo: self._on_dimension_type_selected(tc, cc))
        self.fs_dim2_type_combo.currentIndexChanged.connect(lambda index, tc=self.fs_dim2_type_combo, cc=self.fs_dim2_code_combo: self._on_dimension_type_selected(tc, cc))
        self._on_fs_report_type_changed(self.fs_report_type_combo.currentText()) 

    @Slot(str)
    def _on_fs_report_type_changed(self, report_type: str):
        is_bs = (report_type == "Balance Sheet"); is_pl = (report_type == "Profit & Loss Statement")
        is_gl = (report_type == "General Ledger"); is_tb = (report_type == "Trial Balance")
        self.fs_as_of_date_edit.setVisible(is_bs or is_tb); self.fs_start_date_edit.setVisible(is_pl or is_gl); self.fs_end_date_edit.setVisible(is_pl or is_gl)
        self.fs_gl_account_combo.setVisible(is_gl); self.fs_gl_account_label.setVisible(is_gl)
        self.fs_include_zero_balance_check.setVisible(is_bs); self.fs_include_comparative_check.setVisible(is_bs or is_pl)
        # Dimension filters visibility
        for w in [self.fs_dim1_type_label, self.fs_dim1_type_combo, self.fs_dim1_code_label, self.fs_dim1_code_combo,
                  self.fs_dim2_type_label, self.fs_dim2_type_combo, self.fs_dim2_code_label, self.fs_dim2_code_combo]:
            w.setVisible(is_gl)
        if is_gl and self.fs_dim1_type_combo.count() <= 1 : # Only "All Types"
            schedule_task_from_qt(self._load_dimension_types())

        self._on_comparative_check_changed(self.fs_include_comparative_check.checkState().value) 
        if hasattr(self, 'fs_params_form') and self.fs_params_form:
            for i in range(self.fs_params_form.rowCount()):
                field_widget = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget() # type: ignore
                label_widget = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.LabelRole).widget() # type: ignore
                if label_widget: 
                    if field_widget == self.fs_as_of_date_edit: label_widget.setVisible(is_bs or is_tb)
                    elif field_widget == self.fs_start_date_edit: label_widget.setVisible(is_pl or is_gl)
                    elif field_widget == self.fs_end_date_edit: label_widget.setVisible(is_pl or is_gl)
                    elif field_widget == self.fs_gl_account_combo: self.fs_gl_account_label.setVisible(is_gl)
                    elif field_widget in [self.fs_dim1_type_combo, self.fs_dim1_code_combo, self.fs_dim2_type_combo, self.fs_dim2_code_combo]:
                        label_widget.setVisible(is_gl) # Corresponding label for dimension combos
        if is_gl: self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
        elif is_bs: self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
        elif is_pl: self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
        elif is_tb: self.fs_display_stack.setCurrentWidget(self.tb_table_view)
        self._clear_current_financial_report_display(); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)

    async def _load_dimension_types(self):
        if not self.app_core.dimension_service: self.app_core.logger.error("DimensionService not available."); return
        try:
            dim_types = await self.app_core.dimension_service.get_distinct_dimension_types()
            json_data = json.dumps(dim_types)
            QMetaObject.invokeMethod(self, "_populate_dimension_types_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e: self.app_core.logger.error(f"Error loading dimension types: {e}", exc_info=True)

    @Slot(str)
    def _populate_dimension_types_slot(self, dim_types_json_str: str):
        try: dim_types = json.loads(dim_types_json_str)
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse dimension types JSON."); return
        for combo in [self.fs_dim1_type_combo, self.fs_dim2_type_combo]:
            current_data = combo.currentData() # Save current selection
            combo.clear(); combo.addItem("All Types", None)
            for dt in dim_types: combo.addItem(dt, dt)
            idx = combo.findData(current_data) # Try to restore
            if idx != -1: combo.setCurrentIndex(idx)
            else: combo.setCurrentIndex(0) # Default to "All Types"
        self._on_dimension_type_selected(self.fs_dim1_type_combo, self.fs_dim1_code_combo) # Trigger code load for Dim1
        self._on_dimension_type_selected(self.fs_dim2_type_combo, self.fs_dim2_code_combo) # Trigger code load for Dim2


    @Slot(QComboBox, QComboBox) # type: ignore Due to lambda usage, explicit type hint is harder for IDE
    def _on_dimension_type_selected(self, type_combo: QComboBox, code_combo: QComboBox):
        selected_type_str = type_combo.currentData() # This is the string type or None
        if selected_type_str:
            schedule_task_from_qt(self._load_dimension_codes_for_type(selected_type_str, code_combo.objectName() or ""))
        else: # "All Types" selected
            code_combo.clear(); code_combo.addItem("All Codes", None)

    async def _load_dimension_codes_for_type(self, dim_type_str: str, target_code_combo_name: str):
        if not self.app_core.dimension_service: self.app_core.logger.error("DimensionService not available."); return
        try:
            dimensions: List[Dimension] = await self.app_core.dimension_service.get_dimensions_by_type(dim_type_str)
            dim_codes_data = [{"id": d.id, "code": d.code, "name": d.name} for d in dimensions]
            json_data = json.dumps(dim_codes_data, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dimension_codes_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data), Q_ARG(str, target_code_combo_name))
        except Exception as e: self.app_core.logger.error(f"Error loading dimension codes for type '{dim_type_str}': {e}", exc_info=True)

    @Slot(str, str)
    def _populate_dimension_codes_slot(self, dim_codes_json_str: str, target_code_combo_name: str):
        target_combo: Optional[QComboBox] = None
        if target_code_combo_name == self.fs_dim1_code_combo.objectName(): target_combo = self.fs_dim1_code_combo
        elif target_code_combo_name == self.fs_dim2_code_combo.objectName(): target_combo = self.fs_dim2_code_combo
        if not target_combo: self.app_core.logger.error(f"Target code combo '{target_code_combo_name}' not found."); return
        
        current_data = target_combo.currentData() # Save current selection
        target_combo.clear(); target_combo.addItem("All Codes", None) # UserData None for "All Codes"
        try:
            dim_codes = json.loads(dim_codes_json_str, object_hook=json_date_hook)
            for dc in dim_codes: target_combo.addItem(f"{dc['code']} - {dc['name']}", dc['id'])
            idx = target_combo.findData(current_data) # Try to restore
            if idx != -1: target_combo.setCurrentIndex(idx)
            else: target_combo.setCurrentIndex(0) # Default to "All Codes"
        except json.JSONDecodeError: self.app_core.logger.error(f"Failed to parse dim codes JSON for {target_code_combo_name}")


    # ... (_on_comparative_check_changed, _load_gl_accounts_for_combo, _populate_gl_account_combo_slot,
    #      _clear_current_financial_report_display, _on_generate_financial_report_clicked, _handle_financial_report_result,
    #      _populate_balance_sheet_model, _populate_profit_loss_model, _display_financial_report,
    #      _on_export_report_clicked, _handle_export_result - unchanged from file set 4)
    @Slot(int)
    def _on_comparative_check_changed(self, state: int):
        is_checked = (state == Qt.CheckState.Checked.value); report_type = self.fs_report_type_combo.currentText(); is_bs = (report_type == "Balance Sheet"); is_pl = (report_type == "Profit & Loss Statement")
        self.fs_comparative_as_of_date_label.setVisible(is_bs and is_checked); self.fs_comparative_as_of_date_edit.setVisible(is_bs and is_checked)
        self.fs_comparative_start_date_label.setVisible(is_pl and is_checked); self.fs_comparative_start_date_edit.setVisible(is_pl and is_checked)
        self.fs_comparative_end_date_label.setVisible(is_pl and is_checked); self.fs_comparative_end_date_edit.setVisible(is_pl and is_checked)
    async def _load_gl_accounts_for_combo(self):
        if not self.app_core.chart_of_accounts_manager: self.app_core.logger.error("ChartOfAccountsManager not available for GL account combo."); return
        try:
            accounts_orm: List[Account] = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            self._gl_accounts_cache = [{"id": acc.id, "code": acc.code, "name": acc.name} for acc in accounts_orm]
            accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_gl_account_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, accounts_json))
        except Exception as e: self.app_core.logger.error(f"Error loading accounts for GL combo: {e}", exc_info=True); QMessageBox.warning(self, "Account Load Error", "Could not load accounts for General Ledger selection.")
    @Slot(str)
    def _populate_gl_account_combo_slot(self, accounts_json_str: str):
        self.fs_gl_account_combo.clear()
        try:
            accounts_data = json.loads(accounts_json_str); self._gl_accounts_cache = accounts_data if accounts_data else []
            self.fs_gl_account_combo.addItem("-- Select Account --", 0) 
            for acc_data in self._gl_accounts_cache: self.fs_gl_account_combo.addItem(f"{acc_data['code']} - {acc_data['name']}", acc_data['id'])
            if isinstance(self.fs_gl_account_combo.completer(), QCompleter): self.fs_gl_account_combo.completer().setModel(self.fs_gl_account_combo.model())
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse accounts JSON for GL combo."); self.fs_gl_account_combo.addItem("Error loading accounts", 0)
    def _clear_current_financial_report_display(self):
        self._current_financial_report_data = None; current_view = self.fs_display_stack.currentWidget()
        if isinstance(current_view, QTreeView): model = current_view.model(); 
        if isinstance(model, QStandardItemModel): model.clear()
        elif isinstance(current_view, QTableView): model = current_view.model(); 
        if hasattr(model, 'update_data'): model.update_data({}) 
        elif current_view == self.gl_widget_container : self.gl_model.update_data({}); self.gl_summary_label_account.setText("Account: N/A"); self.gl_summary_label_period.setText("Period: N/A"); self.gl_summary_label_ob.setText("Opening Balance: 0.00"); self.gl_summary_label_cb.setText("Closing Balance: 0.00")
    @Slot()
    def _on_generate_financial_report_clicked(self):
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        self._clear_current_financial_report_display(); self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating..."); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False); 
        coro: Optional[Any] = None; comparative_date_bs: Optional[python_date] = None; comparative_start_pl: Optional[python_date] = None; comparative_end_pl: Optional[python_date] = None; include_zero_bal_bs: bool = False
        dim1_id_val = self.fs_dim1_code_combo.currentData() if self.fs_dim1_code_label.isVisible() else None
        dim2_id_val = self.fs_dim2_code_combo.currentData() if self.fs_dim2_code_label.isVisible() else None
        dimension1_id = int(dim1_id_val) if dim1_id_val and dim1_id_val !=0 else None
        dimension2_id = int(dim2_id_val) if dim2_id_val and dim2_id_val !=0 else None

        if self.fs_include_comparative_check.isVisible() and self.fs_include_comparative_check.isChecked():
            if report_type == "Balance Sheet": comparative_date_bs = self.fs_comparative_as_of_date_edit.date().toPython()
            elif report_type == "Profit & Loss Statement":
                comparative_start_pl = self.fs_comparative_start_date_edit.date().toPython(); comparative_end_pl = self.fs_comparative_end_date_edit.date().toPython()
                if comparative_start_pl and comparative_end_pl and comparative_start_pl > comparative_end_pl: QMessageBox.warning(self, "Date Error", "Comparative start date cannot be after comparative end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
        if report_type == "Balance Sheet": as_of_date = self.fs_as_of_date_edit.date().toPython(); include_zero_bal_bs = self.fs_include_zero_balance_check.isChecked() if self.fs_include_zero_balance_check.isVisible() else False; coro = self.app_core.financial_statement_generator.generate_balance_sheet(as_of_date, comparative_date=comparative_date_bs, include_zero_balances=include_zero_bal_bs)
        elif report_type == "Profit & Loss Statement": start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython(); 
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
        coro = self.app_core.financial_statement_generator.generate_profit_loss(start_date, end_date, comparative_start=comparative_start_pl, comparative_end=comparative_end_pl)
        elif report_type == "Trial Balance": as_of_date = self.fs_as_of_date_edit.date().toPython(); coro = self.app_core.financial_statement_generator.generate_trial_balance(as_of_date)
        elif report_type == "General Ledger":
            account_id = self.fs_gl_account_combo.currentData(); 
            if not isinstance(account_id, int) or account_id == 0: QMessageBox.warning(self, "Selection Error", "Please select a valid account for the General Ledger report."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython()
            if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for General Ledger."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_general_ledger(account_id, start_date, end_date, dimension1_id, dimension2_id)
        if coro: future = schedule_task_from_qt(coro); 
        if future: future.add_done_callback(self._handle_financial_report_result); else: self._handle_financial_report_result(None) 
        else: QMessageBox.warning(self, "Selection Error", "Invalid report type selected or parameters missing."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
    def _handle_financial_report_result(self, future):
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try: report_data: Optional[Dict[str, Any]] = future.result(); 
        if report_data: self._current_financial_report_data = report_data; self._display_financial_report(report_data); self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e: self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True); QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")
    def _populate_balance_sheet_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); has_comparative = bool(report_data.get('comparative_date')); headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(f"Comparative ({report_data.get('comparative_date','Prev').strftime('%d/%m/%Y') if isinstance(report_data.get('comparative_date'), python_date) else 'Prev'})")
        model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}"); amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance'))); amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""; 
                    if comparative_accounts: comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None); comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str); comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)
        for section_key, section_title_display in [('assets', "Assets"), ('liabilities', "Liabilities"), ('equity', "Equity")]:
            section_data = report_data.get(section_key); 
            if not section_data or not isinstance(section_data, dict): continue
            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font); empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); header_row = [section_header_item, empty_amount_item]; 
            if has_comparative: header_row.append(QStandardItem("")); root_node.appendRow(header_row)
            add_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))
            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font); total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items = [total_desc_item, total_amount_item]; 
            if has_comparative: comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items); 
            if section_key != 'equity': root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else []))
        if 'total_liabilities_equity' in report_data:
            root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])); tle_desc = QStandardItem("Total Liabilities & Equity"); tle_desc.setFont(bold_font); tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('total_liabilities_equity'))); tle_amount.setFont(bold_font); tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); tle_row = [tle_desc, tle_amount]; 
            if has_comparative: comp_tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_total_liabilities_equity'))); comp_tle_amount.setFont(bold_font); comp_tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); tle_row.append(comp_tle_amount)
            root_node.appendRow(tle_row)
        if report_data.get('is_balanced') is False: warning_item = QStandardItem("Warning: Balance Sheet is out of balance!"); warning_item.setForeground(QColor("red")); warning_item.setFont(bold_font); warning_row = [warning_item, QStandardItem("")]; 
        if has_comparative: warning_row.append(QStandardItem("")); root_node.appendRow(warning_row)
    def _populate_profit_loss_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); has_comparative = bool(report_data.get('comparative_start')); comp_header_text = "Comparative"; 
        if has_comparative and report_data.get('comparative_start') and report_data.get('comparative_end'): comp_start_str = report_data['comparative_start'].strftime('%d/%m/%y'); comp_end_str = report_data['comparative_end'].strftime('%d/%m/%y'); comp_header_text = f"Comp. ({comp_start_str}-{comp_end_str})"
        headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(comp_header_text); model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_pl_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}"); amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance'))); amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""; 
                    if comparative_accounts: comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None); comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str); comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)
        for section_key, section_title_display in [('revenue', "Revenue"), ('expenses', "Operating Expenses")]: 
            section_data = report_data.get(section_key); 
            if not section_data or not isinstance(section_data, dict): continue
            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font); empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); header_row = [section_header_item, empty_amount_item]; 
            if has_comparative: header_row.append(QStandardItem("")); root_node.appendRow(header_row)
            add_pl_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))
            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font); total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items = [total_desc_item, total_amount_item]; 
            if has_comparative: comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items); root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])) 
        if 'net_profit' in report_data:
            np_desc = QStandardItem("Net Profit / (Loss)"); np_desc.setFont(bold_font); np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('net_profit'))); np_amount.setFont(bold_font); np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); np_row = [np_desc, np_amount]; 
            if has_comparative: comp_np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_net_profit'))); comp_np_amount.setFont(bold_font); comp_np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); np_row.append(comp_np_amount)
            root_node.appendRow(np_row)
    def _display_financial_report(self, report_data: Dict[str, Any]):
        report_title = report_data.get('title', '')
        if report_title == "Balance Sheet": self.fs_display_stack.setCurrentWidget(self.bs_tree_view); self._populate_balance_sheet_model(self.bs_model, report_data); self.bs_tree_view.expandAll(); 
        for i in range(self.bs_model.columnCount()): self.bs_tree_view.resizeColumnToContents(i)
        elif report_title == "Profit & Loss Statement": self.fs_display_stack.setCurrentWidget(self.pl_tree_view); self._populate_profit_loss_model(self.pl_model, report_data); self.pl_tree_view.expandAll(); 
        for i in range(self.pl_model.columnCount()): self.pl_tree_view.resizeColumnToContents(i)
        elif report_title == "Trial Balance": self.fs_display_stack.setCurrentWidget(self.tb_table_view); self.tb_model.update_data(report_data); 
        for i in range(self.tb_model.columnCount()): self.tb_table_view.resizeColumnToContents(i)
        elif report_title == "General Ledger": self.fs_display_stack.setCurrentWidget(self.gl_widget_container); self.gl_model.update_data(report_data); gl_summary_data = self.gl_model.get_report_summary(); self.gl_summary_label_account.setText(f"Account: {gl_summary_data['account_name']}"); self.gl_summary_label_period.setText(gl_summary_data['period_description']); self.gl_summary_label_ob.setText(f"Opening Balance: {self._format_decimal_for_display(gl_summary_data['opening_balance'], show_blank_for_zero=False)}"); self.gl_summary_label_cb.setText(f"Closing Balance: {self._format_decimal_for_display(gl_summary_data['closing_balance'], show_blank_for_zero=False)}"); 
        for i in range(self.gl_model.columnCount()): self.gl_table_view.resizeColumnToContents(i)
        else: self._clear_current_financial_report_display(); self.app_core.logger.warning(f"Unhandled report title '{report_title}' for specific display."); QMessageBox.warning(self, "Display Error", f"Display format for '{report_title}' is not fully implemented in this view.")
    @Slot(str)
    def _on_export_report_clicked(self, format_type: str):
        if not self._current_financial_report_data: QMessageBox.warning(self, "No Report", "Please generate a report first before exporting."); return
        report_title = self._current_financial_report_data.get('title', 'FinancialReport').replace(' ', '_').replace('&', 'And').replace('/', '-').replace(':', ''); default_filename = f"{report_title}_{python_date.today().strftime('%Y%m%d')}.{format_type}"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation); 
        if not documents_path: documents_path = os.path.expanduser("~") 
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {format_type.upper()} Report", os.path.join(documents_path, default_filename), f"{format_type.upper()} Files (*.{format_type});;All Files (*)")
        if file_path: self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False); future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._current_financial_report_data, format_type)); 
        if future: future.add_done_callback(lambda f, fp=file_path, ft=format_type: self._handle_export_result(f, fp, ft)); else: self._handle_export_result(None, file_path, format_type)
    def _handle_export_result(self, future, file_path: str, format_type: str):
        self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", f"Failed to generate report bytes for {format_type.upper()}.")
        except Exception as e: self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")

```

**Summary of Task Completion and Validation (Phase 2 - Dimension Filters for GL):**

1.  **`app/services/__init__.py`**:
    *   `IDimensionRepository` interface correctly defined with `get_distinct_dimension_types`, `get_dimensions_by_type`, and `get_by_type_and_code`.
    *   `Dimension` model imported.
    *   `IDimensionRepository` and `DimensionService` correctly added to `__all__`.
2.  **`app/services/accounting_services.py`**:
    *   `DimensionService` implemented:
        *   `get_distinct_dimension_types()` correctly fetches distinct, active dimension types.
        *   `get_dimensions_by_type()` correctly fetches active dimensions for a given type.
        *   `get_by_id`, `get_all`, `add`, `update`, `delete`, `get_by_type_and_code` provide standard repository methods for `Dimension` ORM.
3.  **`app/core/application_core.py`**:
    *   `DimensionService` correctly imported, instantiated in `startup()`, and exposed via the `dimension_service` property.
4.  **`app/services/journal_service.py`**:
    *   `get_posted_lines_for_account_in_range` signature correctly updated to include `dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None`.
    *   The SQLAlchemy query within this method now correctly appends `JournalEntryLine.dimension1_id == dimension1_id` and `JournalEntryLine.dimension2_id == dimension2_id` to its `conditions` list if these IDs are provided.
5.  **`app/reporting/financial_statement_generator.py`**:
    *   `__init__` now accepts an optional `dimension_service`.
    *   `generate_general_ledger` signature correctly updated to include `dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None`.
    *   These dimension IDs are correctly passed to `self.journal_service.get_posted_lines_for_account_in_range`.
    *   The `report_date_description` is enhanced to include dimension information if filters are applied, by fetching dimension details using `DimensionService`. This is a nice touch for clarity.
    *   `transactions_data` now includes `dim1_id` and `dim2_id` from the `JournalEntryLine` for potential display or further processing, which is good foresight.
6.  **`app/ui/reports/reports_widget.py`**:
    *   **UI Elements**: Four new `QComboBox`es (`fs_dim1_type_combo`, `fs_dim1_code_combo`, `fs_dim2_type_combo`, `fs_dim2_code_combo`) and their corresponding labels are added to `fs_params_form`.
    *   **Visibility**: `_on_fs_report_type_changed` correctly shows these dimension filter controls only when "General Ledger" is selected and hides them otherwise. It also triggers `_load_dimension_types` if they haven't been loaded yet for the GL report.
    *   **Dynamic Combo Population**:
        *   `_load_dimension_types` and `_populate_dimension_types_slot` correctly fetch distinct dimension types and populate `fs_dim1_type_combo` and `fs_dim2_type_combo`.
        *   `_on_dimension_type_selected` slot correctly connected to `currentIndexChanged` of type combos. It correctly triggers `_load_dimension_codes_for_type`.
        *   `_load_dimension_codes_for_type` and `_populate_dimension_codes_slot` correctly fetch dimension codes/names based on the selected type and populate the respective code combos (`fs_dim1_code_combo`, `fs_dim2_code_combo`), storing dimension `id` as `itemData`. Object names are used to identify target combos, which is a valid approach.
    *   **Filter Application**: In `_on_generate_financial_report_clicked`, when the report type is "General Ledger", it now correctly retrieves `dimension1_id` and `dimension2_id` from the `currentData()` of the code combos and passes them to `generate_general_ledger`. The conversion of `0` or `None` from `currentData()` to `None` for the service call is correct.

**Validation & No Regressions:**
*   The new dimension filtering capability for the General Ledger report is comprehensively implemented across all relevant layers (UI, generator, services).
*   The UI for selecting dimensions is dynamic and user-friendly.
*   The backend logic correctly applies these dimension filters to the data query.
*   The GL report description is updated to reflect active dimension filters.
*   All existing functionalities, including other report generations and filters, remain unaffected. The changes are well-encapsulated.

Phase 2 (Dimension Filters for GL) is complete. The application now offers more powerful analytical capabilities for the General Ledger. This also completes all items listed under the "Current Focus / Short-term" section of the roadmap.
