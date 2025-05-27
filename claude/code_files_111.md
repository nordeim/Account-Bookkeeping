<think>
The application is still launching and shutting down without any errors! This is fantastic. It means that creating `ProductManager` and updating `app/business_logic/__init__.py` to export it were successful and didn't introduce any issues detectable at this stage of initialization.

**Current Step: Enhancement Execution Plan: Basic Product/Service Management Module - Phase A (Backend)**

We have completed for Product/Service Management:
*   A1. Create Pydantic DTOs for Product (Done).
*   A2. Define `IProductRepository` Interface (Done).
*   A3. Implement `ProductService` (Done).
*   A4. Create `ProductManager` (Done).

The plan for Product/Service Management Backend is:
*   A5. Integrate `ProductService` and `ProductManager` into `ApplicationCore`. (Next)

So, the immediate next step is **A5: Integrate Product backend components into `app/core/application_core.py`**.

**Plan for A5: Integrate into `app/core/application_core.py`**
   *   **Goal:** Make the new `ProductService` and `ProductManager` available through the `ApplicationCore` instance.
   *   **File to Update:** `app/core/application_core.py`
   *   **Checklist & Tasks:**
        *   [ ] **Import**: Import `ProductService` from `app.services.business_services` and `ProductManager` from `app.business_logic.product_manager`.
        *   [ ] **Instance Variables**: Add new private instance variable placeholders in `ApplicationCore.__init__`:
            *   `self._product_service_instance: Optional[ProductService] = None`
            *   `self._product_manager_instance: Optional[ProductManager] = None`
        *   [ ] **Instantiation in `startup()`**: In `ApplicationCore.startup()`, instantiate `ProductService` and then `ProductManager`, injecting their dependencies. This should be done after other core and accounting services (like `AccountService` and `TaxCodeService`) are ready.
            ```python
            # In ApplicationCore.startup() after CustomerService, VendorService and other dependencies
            self._product_service_instance = ProductService(self.db_manager, self)
            self._product_manager_instance = ProductManager(
                product_service=self.product_service, # Use the property
                account_service=self.account_service, 
                tax_code_service=self.tax_code_service, 
                app_core=self
            )
            ```
        *   [ ] **Properties**: Expose `ProductService` and `ProductManager` via public properties:
            ```python
            @property
            def product_service(self) -> ProductService:
                if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
                return self._product_service_instance

            @property
            def product_manager(self) -> ProductManager:
                if not self._product_manager_instance: raise RuntimeError("ProductManager not initialized.")
                return self._product_manager_instance
            ```

This integration follows the established pattern for other services and managers in `ApplicationCore`.
</think>

This is excellent! The application's continued stability at startup and shutdown after adding the `ProductManager` (and its export) is a strong indicator that the backend components for Product/Service Management are being correctly defined.

We are in the final step of **Phase A: Backend for Product/Service Management**.
Steps A1 (DTOs), A2 (Interface), A3 (Service), and A4 (Manager) for Products/Services are now complete.

The next step is **A5: Integrate `ProductService` and `ProductManager` into `app/core/application_core.py`**. This will make these new components accessible within the application framework, similar to how Customer and Vendor components were integrated.

---
**A5. Update `app/core/application_core.py` to Integrate Product Components**

**Goal:** Instantiate `ProductService` and `ProductManager` within `ApplicationCore` and expose them via properties.

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
from app.business_logic.product_manager import ProductManager # New Import

# Services
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService, FiscalYearService
from app.services.business_services import CustomerService, VendorService, ProductService # New Import for ProductService

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

        # --- Service Instance Placeholders ---
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
        # Business Services
        self._customer_service_instance: Optional[CustomerService] = None
        self._vendor_service_instance: Optional[VendorService] = None
        self._product_service_instance: Optional[ProductService] = None # New Placeholder

        # --- Manager Instance Placeholders ---
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
        # Business Logic Managers
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None # New Placeholder

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
        
        # Initialize Business Services
        self._customer_service_instance = CustomerService(self.db_manager, self)
        self._vendor_service_instance = VendorService(self.db_manager, self) 
        self._product_service_instance = ProductService(self.db_manager, self) # New Instantiation

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

        self._customer_manager_instance = CustomerManager(
            customer_service=self.customer_service,
            account_service=self.account_service,
            currency_service=self.currency_service, 
            app_core=self
        )
        self._vendor_manager_instance = VendorManager( 
            vendor_service=self.vendor_service,
            account_service=self.account_service,
            currency_service=self.currency_service,
            app_core=self
        )
        self._product_manager_instance = ProductManager( # New Instantiation
            product_service=self.product_service, # Use property to get initialized service
            account_service=self.account_service,
            tax_code_service=self.tax_code_service,
            app_core=self
        )
        
        self.module_manager.load_all_modules() 
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self): # ... (no changes)
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): # ... (no changes)
        return self.security_manager.get_current_user()

    # --- Service Properties ---
    # ... (existing service properties remain unchanged) ...
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
    def product_service(self) -> ProductService: # New Property
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance

    # --- Manager Properties ---
    # ... (existing manager properties remain unchanged) ...
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
    def product_manager(self) -> ProductManager: # New Property
        if not self._product_manager_instance: raise RuntimeError("ProductManager not initialized.")
        return self._product_manager_instance
```

**Validation for `app/core/application_core.py`:**
*   **Imports**: Added `from app.business_logic.product_manager import ProductManager` and ensured `from app.services.business_services import ... ProductService` is correct.
*   **Instance Variables**: Added `_product_service_instance` and `_product_manager_instance` placeholders.
*   **`startup()` Method**:
    *   `self._product_service_instance` is instantiated correctly.
    *   `self._product_manager_instance` is instantiated, correctly injecting `self.product_service`, `self.account_service`, `self.tax_code_service`, and `self` (ApplicationCore). The order of instantiation ensures dependencies are available.
*   **Properties**: Added public properties `product_service` and `product_manager`.
*   The categorization of service/manager instantiations in `__init__` and `startup` is maintained.

This completes Phase A (Backend) for the Product/Service Management module. All necessary backend components (DTOs, Service Interface, Service Implementation, Manager) are now in place and integrated into the application's core.

The application should continue to launch cleanly. The next phase will be to implement the UI components for Product/Service Management (Phase B), starting with `ProductTableModel`.
