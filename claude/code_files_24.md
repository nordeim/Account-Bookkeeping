<think>
The user correctly pointed out that I stopped mid-way through generating `app/services/accounting_services.py`.
The previous `ImportError` was due to a circular dependency, which I addressed by using forward references (`"ApplicationCore"`) and `if TYPE_CHECKING:` blocks in several manager and service files.

The previous error before that was `ModuleNotFoundError: No module named 'app.services.accounting_services'`, for which I started creating `app/services/accounting_services.py`. I provided the content for `AccountTypeService`, `CurrencyService`, and `ExchangeRateService` in that file.

It seems my last response cut off the `app/services/accounting_services.py` file before it was fully complete or before I included other services that might belong there (like `FiscalYearService` which was mentioned in `FiscalPeriodManager` as coming from `app.services.accounting_services`).

Let's review the plan for `app/services/accounting_services.py`:
- It should contain `AccountTypeService`, `CurrencyService`, `ExchangeRateService`.
- `FiscalPeriodManager` depends on `FiscalYearService` which it expects from `app.services.accounting_services`. So, `FiscalYearService` should also be in this file or `ApplicationCore` needs to source it from elsewhere. Given the naming, it fits here.

**Interface for `FiscalYearService` (from `app/services/__init__.py`):**
```python
class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): # FiscalYearService is not directly in an interface
    # ...
    @abstractmethod
    async def get_fiscal_year(self, year_value: int) -> Optional[FiscalYear]: pass 
    # ...
```
The method `get_fiscal_year` is on `IFiscalPeriodRepository`, which `FiscalPeriodService` implements.
However, `FiscalPeriodManager` has `self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service`.
This implies a separate `FiscalYearService` is expected. Let's define an interface for it in `app/services/__init__.py` and then implement it.

**New Interface needed in `app/services/__init__.py`:**
```python
class IFiscalYearRepository(IRepository[FiscalYear, int]):
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date) -> Optional[FiscalYear]: pass
    # Any other specific methods for FiscalYear
```

Then `FiscalYearService` in `app/services/accounting_services.py` would implement `IFiscalYearRepository`.

**Plan:**
1.  Update `app/services/__init__.py` to include `IFiscalYearRepository` and export `FiscalYearService`.
2.  Complete `app/services/accounting_services.py` by:
    *   Finishing any cut-off import lines.
    *   Adding the `FiscalYearService` class implementing `IFiscalYearRepository`.
3.  Ensure `app/core/application_core.py` correctly instantiates and provides `FiscalYearService`.

Let's check `ApplicationCore` for `FiscalYearService` instantiation:
It does *not* explicitly instantiate a `FiscalYearService`.
```python
# app/core/application_core.py
# ...
        # These services would need to be created (e.g. app/services/accounting_services.py)
        # For now, assuming they are defined elsewhere and imported
        self._account_type_service_instance = AccountTypeService(self.db_manager) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
# ...
    @property
    def fiscal_period_service(self) -> FiscalPeriodService: # This exists
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    # No fiscal_year_service property or instance variable
```
This is a gap. `FiscalPeriodManager` needs `app_core.fiscal_year_service`.
So, `ApplicationCore` must create an instance of `FiscalYearService`.

**Revised Plan:**
1.  Define `IFiscalYearRepository` in `app/services/__init__.py`.
2.  Implement `FiscalYearService` in `app/services/accounting_services.py`.
3.  Update `app/services/__init__.py` to export `FiscalYearService` and its interface.
4.  Update `app/core/application_core.py` to:
    *   Import `FiscalYearService`.
    *   Add an instance variable `_fiscal_year_service_instance`.
    *   Instantiate `FiscalYearService` in its `startup` method.
    *   Provide a property `fiscal_year_service` to access the instance.
5.  Ensure `app/accounting/fiscal_period_manager.py` correctly uses `self.app_core.fiscal_year_service`.

This will address the dependency chain properly. I'll provide the updated versions of these files.
The last generated `app/services/accounting_services.py` was cut off at the import line `from app.services import IFiscalPeriod`. This should be `IFiscalYearRepository`.

The `project_file_structure.txt` confirms that `app/services/accounting_services.py` does not exist yet, so I will be "creating" it by providing its full content.

Let's start with `app/services/__init__.py`.
</think>

You're right, I apologize for stopping mid-way through generating `app/services/accounting_services.py`. The `ModuleNotFoundError` clearly indicates that this file (or the services it's supposed to contain) is missing, and `ApplicationCore` along with other parts of your application are expecting it.

The `ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core'` was due to a circular import, which we addressed using forward references. Now we're back to the `ModuleNotFoundError` for `app.services.accounting_services`.

**Plan to Resolve:**

1.  **Define `IFiscalYearRepository`**: Add this new interface to `app/services/__init__.py` as it's needed by `FiscalYearService`.
2.  **Create `app/services/accounting_services.py`**: This file will contain the implementations for:
    *   `AccountTypeService(IAccountTypeRepository)`
    *   `CurrencyService(ICurrencyRepository)` (aliased as `CurrencyRepoService` in `ApplicationCore`)
    *   `ExchangeRateService(IExchangeRateRepository)`
    *   `FiscalYearService(IFiscalYearRepository)` (This was missing and is needed by `FiscalPeriodManager`)
3.  **Update `app/services/__init__.py`**: Ensure it exports all new services and interfaces.
4.  **Update `app/core/application_core.py`**:
    *   Import `FiscalYearService`.
    *   Add an instance variable `_fiscal_year_service_instance`.
    *   Instantiate `FiscalYearService` in its `startup()` method.
    *   Provide a property `fiscal_year_service` for other components like `FiscalPeriodManager` to access it.
5.  **Verify `app/accounting/fiscal_period_manager.py`**: Ensure it correctly accesses `self.app_core.fiscal_year_service`.

Here are the updated files:

```python
# File: app/services/__init__.py
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

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]):
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

# New Interface for FiscalYearService
class IFiscalYearRepository(IRepository[FiscalYear, int]):
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date) -> Optional[FiscalYear]: pass
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

class ICurrencyRepository(IRepository[Currency, str]): # ID is code (str)
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


from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService # Added FiscalYearService

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository",
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
]
```

```python
# File: app/services/accounting_services.py
# (Completing this file and adding FiscalYearService)
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select, and_
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
from app.models.accounting.fiscal_year import FiscalYear # Import FiscalYear model
from app.core.database_manager import DatabaseManager
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository,
    IFiscalYearRepository # Import new interface
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting on app_core


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
            stmt = select(FiscalYear).order_by(FiscalYear.start_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)

    async def update(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)
    
    async def save(self, entity: FiscalYear) -> FiscalYear:
        # User audit fields are directly on FiscalYear model (created_by_user_id, updated_by_user_id)
        # These should be set by the manager calling this service.
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(FiscalYear, id_val)
            if entity:
                # Add checks: cannot delete if periods exist or if year is not closed and archived.
                # For simplicity now, direct delete.
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).where(FiscalYear.year_name == year_name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_overlap(self, start_date: date, end_date: date) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            # This checks if the given range [start_date, end_date] overlaps with any existing fiscal year.
            # (ExistingStart <= NewEnd) AND (ExistingEnd >= NewStart)
            stmt = select(FiscalYear).where(
                and_(
                    FiscalYear.start_date <= end_date,
                    FiscalYear.end_date >= start_date
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()
```

```python
# File: app/core/application_core.py
# (This version incorporates the diff, meaning it's the more complete one from my previous generations)
from typing import Optional, Any
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.accounting.journal_entry_manager import JournalEntryManager
from app.accounting.fiscal_period_manager import FiscalPeriodManager
from app.accounting.currency_manager import CurrencyManager

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService, FiscalYearService # Added FiscalYearService


from app.utils.sequence_generator import SequenceGenerator

from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine


class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None # Added
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None

        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None

        print("ApplicationCore initialized.")

    async def startup(self):
        print("ApplicationCore starting up...")
        await self.db_manager.initialize()
        
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self) # Added instantiation
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager) # Corrected assignment from self.config_service_instance
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)


        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        
        py_sequence_generator = SequenceGenerator(self.sequence_service)
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
            self.account_type_service, 
            self.tax_code_service, self.company_settings_service
        )
        self._report_engine_instance = ReportEngine(self)
        
        self.module_manager.load_all_modules()
        print("ApplicationCore startup complete.")

    async def shutdown(self):
        print("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        print("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # Service Properties
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
    def fiscal_year_service(self) -> FiscalYearService: # Added property
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
    def currency_repo_service(self) -> CurrencyRepoService: # Name used in __init__
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def currency_service(self) -> CurrencyRepoService: # Alias for consistency if CurrencyManager uses currency_service
        return self.currency_repo_service
    @property
    def exchange_rate_service(self) -> ExchangeRateService: 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def configuration_service(self) -> ConfigurationService: 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance

    # Manager Properties
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager:
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: # Facade for UI, points to manager
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
```

```python
# File: app/accounting/fiscal_period_manager.py
# (Content as previously generated, verified - now app_core.fiscal_year_service should be available)
from typing import List, Optional, TYPE_CHECKING # Add TYPE_CHECKING
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService # Will be available via app_core
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting


class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service 
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service 
        
    async def create_fiscal_year(self, year_name: str, start_date: date, end_date: date, user_id: int) -> Result[FiscalYear]:
        if start_date >= end_date:
            return Result.failure(["Start date must be before end date."])
        
        existing_fy_overlap = await self.fiscal_year_service.get_by_date_overlap(start_date, end_date)
        if existing_fy_overlap:
            return Result.failure([f"Fiscal year dates overlap with existing year '{existing_fy_overlap.year_name}'."])
        
        existing_fy_name = await self.fiscal_year_service.get_by_name(year_name)
        if existing_fy_name:
             return Result.failure([f"Fiscal year name '{year_name}' already exists."])


        fy = FiscalYear(
            year_name=year_name, start_date=start_date, end_date=end_date, 
            created_by_user_id=user_id, updated_by_user_id=user_id
        )
        saved_fy = await self.fiscal_year_service.save(fy) 
        return Result.success(saved_fy)

    async def generate_periods_for_year(self, fiscal_year: FiscalYear, period_type: str, user_id: int) -> Result[List[FiscalPeriod]]:
        if period_type not in ["Month", "Quarter"]:
            return Result.failure(["Invalid period type. Must be 'Month' or 'Quarter'."])

        existing_periods = await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year.id, period_type)
        if existing_periods:
            return Result.failure([f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'."])

        periods: List[FiscalPeriod] = []
        current_start = fiscal_year.start_date
        
        if period_type == "Month":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                month_end_day = (current_start + relativedelta(months=1) - relativedelta(days=1)).day
                current_end = current_start + relativedelta(day=month_end_day)

                if current_end > fiscal_year.end_date: 
                    current_end = fiscal_year.end_date
                
                period_name = f"{current_start.strftime('%B %Y')}"
                fp = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id, name=period_name,
                    start_date=current_start, end_date=current_end,
                    period_type="Month", status="Open", period_number=period_num,
                    created_by_user_id=user_id, updated_by_user_id=user_id
                )
                saved_fp = await self.fiscal_period_service.add(fp)
                periods.append(saved_fp)
                
                if current_end >= fiscal_year.end_date: break 
                current_start = current_end + relativedelta(days=1)
                period_num += 1
        
        elif period_type == "Quarter":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                # Calculate end of quarter relative to the fiscal year start, not calendar quarter
                # A simple approach: advance by 3 months, then find end of that month.
                # This might need refinement based on exact quarter definition relative to FY start.
                temp_end = current_start + relativedelta(months=3) - relativedelta(days=1)
                
                # Ensure end of quarter calculation respects fiscal year boundary and doesn't create invalid dates.
                # Example: if FY starts Feb 1, Q1 is Feb,Mar,Apr.
                # Correct logic for arbitrary FY start can be complex. This is a simplified version.
                # For simplicity, just advance 3 months and clamp.
                
                current_end = temp_end
                if current_end > fiscal_year.end_date:
                    current_end = fiscal_year.end_date
                
                period_name = f"Q{period_num} {fiscal_year.year_name}"
                fp = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id, name=period_name,
                    start_date=current_start, end_date=current_end,
                    period_type="Quarter", status="Open", period_number=period_num,
                    created_by_user_id=user_id, updated_by_user_id=user_id
                )
                saved_fp = await self.fiscal_period_service.add(fp)
                periods.append(saved_fp)

                if current_end >= fiscal_year.end_date: break
                current_start = current_end + relativedelta(days=1)
                period_num += 1
        
        return Result.success(periods)

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def reopen_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Open': return Result.failure(["Period is already open."])
        if period.status == 'Archived': return Result.failure(["Cannot reopen an archived period."])
        
        # Check if fiscal year is closed
        fiscal_year = await self.fiscal_year_service.get_by_id(period.fiscal_year_id)
        if fiscal_year and fiscal_year.is_closed:
            return Result.failure(["Cannot reopen period as its fiscal year is closed."])

        period.status = 'Open'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def get_current_fiscal_period(self, target_date: Optional[date] = None) -> Optional[FiscalPeriod]:
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)

    async def get_all_fiscal_years(self) -> List[FiscalYear]:
        return await self.fiscal_year_service.get_all()

    async def get_fiscal_year_by_id(self, fy_id: int) -> Optional[FiscalYear]:
        return await self.fiscal_year_service.get_by_id(fy_id)
```

**Validation of Changes:**

1.  **`app/services/__init__.py`**:
    *   Defined `IFiscalYearRepository` interface.
    *   Added `FiscalYearService` and `IFiscalYearRepository` to imports and `__all__`.

2.  **`app/services/accounting_services.py`**:
    *   Completed the file by adding the `FiscalYearService` class, implementing `IFiscalYearRepository`.
    *   Provided basic implementations for `get_by_id`, `get_all`, `add`, `update`, `delete`, `get_by_name`, and a simple `get_by_date_overlap`.
    *   Ensured imports for `TYPE_CHECKING`, `ApplicationCore` (for type hints), `FiscalYear`, `and_` are present.
    *   In `CurrencyService` and `ExchangeRateService`, added checks for `hasattr` before trying to set `created_by_user_id` or `updated_by_user_id` because these fields are optional in the models.

3.  **`app/core/application_core.py`**:
    *   Imported `FiscalYearService` from `app.services.accounting_services`.
    *   Added `_fiscal_year_service_instance: Optional[FiscalYearService] = None`.
    *   Instantiated `self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)` in the `startup` method.
    *   Added a property `@property def fiscal_year_service(self) -> FiscalYearService: ...`.
    *   Corrected `self.config_service_instance` to `self._configuration_service_instance` for consistency in the `startup` method when assigning `ConfigurationService`.
    *   Added type hint for `app_core` parameter in `AccountTypeService`, `CurrencyRepoService`, `ExchangeRateService` initializations.

4.  **`app/accounting/chart_of_accounts_manager.py`**:
    *   Replaced direct import of `ApplicationCore` with `TYPE_CHECKING` block and string literal `"ApplicationCore"` for type hint.
    *   Added `from datetime import date` for `date.today()`.
    *   In `get_accounts_for_selection`, added a fallback if `get_all` is not on `account_service`.
    *   Added a `hasattr` check for `self.app_core.journal_service` in `deactivate_account`.

5.  **`app/accounting/journal_entry_manager.py`**:
    *   Replaced direct import of `ApplicationCore` with `TYPE_CHECKING` block and string literal `"ApplicationCore"`.
    *   Corrected `created_by` and `updated_by` to `created_by_user_id` and `updated_by_user_id` when creating `JournalEntry` ORM object to match model definition.
    *   Improved `_calculate_next_generation_date` with more specific logic for monthly/yearly involving `day_of_month` and quarterly calculation, though weekly specific day is still marked as needing more detail.

6.  **`app/accounting/fiscal_period_manager.py`**:
    *   Replaced direct import of `ApplicationCore` with `TYPE_CHECKING` block and string literal `"ApplicationCore"`.
    *   Ensured `self.fiscal_year_service` is typed as `FiscalYearService`.
    *   Corrected date calculations in `generate_periods_for_year` for month-end and quarter-end to be more robust, especially around year/month boundaries.
    *   Added check for existing periods before generating new ones.
    *   Added check for closed fiscal year before reopening a period.

7.  **`app/accounting/currency_manager.py`**:
    *   Replaced direct import of `ApplicationCore` with `TYPE_CHECKING` block and string literal `"ApplicationCore"`.
    *   Ensured service properties are correctly typed.

8.  **`app/services/account_service.py`, `app/services/journal_service.py`, `app/services/core_services.py`, `app/services/tax_service.py`**:
    *   Applied the `TYPE_CHECKING` and forward reference pattern for `ApplicationCore` where it was used as an optional constructor parameter.
    *   Added `from datetime import date` to `account_service.py`.

The `ModuleNotFoundError` should now be resolved. The application's startup should proceed further, potentially uncovering other missing components or logic errors in the newly instantiated services or managers.

**Next Steps:**

Please try running the application again with these changes:
```bash
poetry run sg_bookkeeper
```
