<think>
The application is still launching and shutting down cleanly. This is excellent! It means the creation of `app/business_logic/__init__.py` and `app/business_logic/customer_manager.py`, along with the updated `app/services/__init__.py` and `app/services/business_services.py` (with `CustomerService`), did not introduce any import errors or other issues detectable at startup/shutdown.

**Current Step: Enhancement Execution Plan: Basic Customer Management Module - Phase A (Backend)**

We have completed:
*   A1. Create Pydantic DTOs for Customer (Done)
*   A2. Define `ICustomerRepository` Interface (Done)
*   A3. Implement `CustomerService` (Done)
*   A4. Create `CustomerManager` (Done)

The next and final step for Phase A is **A5: Integrate `CustomerService` and `CustomerManager` into `app/core/application_core.py`**.

**Plan for A5: Integrate into `app/core/application_core.py`**
   *   **Goal:** Make the new `CustomerService` and `CustomerManager` available through the `ApplicationCore` instance so other parts of the application (especially UI widgets) can access them.
   *   **File to Update:** `app/core/application_core.py`
   *   **Checklist & Tasks:**
        *   [ ] **Import**: Import `CustomerService` from `app.services.business_services` and `CustomerManager` from `app.business_logic.customer_manager`.
        *   [ ] **Instance Variables**: Add new private instance variable placeholders in `ApplicationCore.__init__`:
            *   `self._customer_service: Optional[CustomerService] = None`
            *   `self._customer_manager: Optional[CustomerManager] = None`
        *   [ ] **Instantiation in `startup()`**: In `ApplicationCore.startup()`, after other services are initialized (especially `AccountService` and `CurrencyService` which are dependencies for `CustomerManager`), instantiate `CustomerService` and then `CustomerManager`, injecting their dependencies.
            ```python
            # In ApplicationCore.startup()
            self._customer_service = CustomerService(self.db_manager, self)
            self._customer_manager = CustomerManager(
                customer_service=self.customer_service,
                account_service=self.account_service, # Assumes self.account_service is already initialized
                currency_service=self.currency_service, # Assumes self.currency_service (which is self.currency_repo_service) is initialized
                app_core=self
            )
            ```
        *   [ ] **Properties**: Expose `CustomerService` and `CustomerManager` via public properties:
            ```python
            @property
            def customer_service(self) -> CustomerService:
                if not self._customer_service: raise RuntimeError("CustomerService not initialized.")
                return self._customer_service

            @property
            def customer_manager(self) -> CustomerManager:
                if not self._customer_manager: raise RuntimeError("CustomerManager not initialized.")
                return self._customer_manager
            ```

This step is relatively straightforward and involves boilerplate for integrating new components into the existing `ApplicationCore` structure.
</think>

Fantastic! The application remains stable, indicating the backend components for Customer Management (`CustomerService` and `CustomerManager`) were correctly created without syntax or fundamental import errors.

Now, we'll proceed with the final step of **Phase A: Backend for Customer Management**, which is **A5: Integrate `CustomerService` and `CustomerManager` into `app/core/application_core.py`**. This will make these new components accessible throughout the application.

---
**1. Update `app/core/application_core.py`**

**Goal:** Instantiate and provide access to `CustomerService` and `CustomerManager`.

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

# Business Logic Managers (New Import)
from app.business_logic.customer_manager import CustomerManager 

# Services
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService, FiscalYearService
from app.services.business_services import CustomerService # New Import

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
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO) 

        if not hasattr(self.db_manager, 'logger') or self.db_manager.logger is None:
             self.db_manager.logger = self.logger


        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        # Accounting Services
        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        
        # Core Services
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None
        
        # Tax Services
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        
        # Business Services (New)
        self._customer_service_instance: Optional[CustomerService] = None
        # Add VendorService, ProductService placeholders later

        # Accounting Managers
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        
        # Tax Managers
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        
        # Reporting Managers
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None

        # Business Logic Managers (New)
        self._customer_manager_instance: Optional[CustomerManager] = None
        # Add VendorManager, ProductManager placeholders later


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
        
        # Initialize Tax Services
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        # Initialize Business Services (New)
        self._customer_service_instance = CustomerService(self.db_manager, self)

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
            self.account_type_service, 
            self.tax_code_service, self.company_settings_service
        )
        self._report_engine_instance = ReportEngine(self)

        # Initialize Business Logic Managers (New)
        self._customer_manager_instance = CustomerManager(
            customer_service=self.customer_service,
            account_service=self.account_service,
            currency_service=self.currency_service, # Property that points to currency_repo_service
            app_core=self
        )
        
        self.module_manager.load_all_modules() # Conceptual call
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self):
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # --- Service Properties ---
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
    def currency_repo_service(self) -> CurrencyRepoService: # Actual service instance for Currency CRUD
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def currency_service(self) -> CurrencyRepoService: # Alias for managers expecting 'currency_service'
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
    def customer_service(self) -> CustomerService: # New Property
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance

    # --- Manager Properties ---
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager:
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: # Facade for UI
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
    def customer_manager(self) -> CustomerManager: # New Property
        if not self._customer_manager_instance: raise RuntimeError("CustomerManager not initialized.")
        return self._customer_manager_instance

```
**Validation for `app/core/application_core.py`:**
*   **Imports**: Added `from app.services.business_services import CustomerService` and `from app.business_logic.customer_manager import CustomerManager`.
*   **Instance Variables**: Added `_customer_service_instance` and `_customer_manager_instance`.
*   **`startup()` Method**:
    *   `self._customer_service_instance` is instantiated.
    *   `self._customer_manager_instance` is instantiated, correctly injecting `self.customer_service`, `self.account_service`, and `self.currency_service` (which maps to `self.currency_repo_service`).
    *   The order of initialization is logical (services first, then managers that depend on them).
*   **Properties**: Added public properties `customer_service` and `customer_manager` for accessing the new instances, with standard initialization checks.
*   **`py_sequence_generator`**: Passed `app_core_ref=self` to `SequenceGenerator` constructor.

This completes Phase A for the Customer Management backend. The application should still launch cleanly as these are backend additions not yet called by any UI. The next phase (Phase B) would be to build the UI components for Customer Management.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing

