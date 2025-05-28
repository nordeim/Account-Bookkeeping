<think>
This is excellent! The application is launching and shutting down cleanly again. This confirms that the `NameError` in `SalesInvoiceManager` (due to missing `date` and `SalesInvoiceSummaryData` imports) and the other refinements in that file have been successfully resolved without introducing new startup issues.

**Current Step: Enhancement Execution Plan: Basic Sales Invoicing - Phase A (Backend)**

We have completed for Sales Invoice Backend:
*   A1. Create Pydantic DTOs for Sales Invoice (Done).
*   A2. Define `ISalesInvoiceRepository` Interface (Done).
*   A3. Implement `SalesInvoiceService` (Done).
*   A4. Create `SalesInvoiceManager` (Done, including import fixes).

The plan for Sales Invoice Backend was:
*   A5. Integrate `SalesInvoiceService` and `SalesInvoiceManager` into `ApplicationCore`. (Next)

So, the immediate next step is **A5: Integrate Sales Invoice backend components into `app/core/application_core.py`**.

**Plan for A5: Integrate into `app/core/application_core.py`**
   *   **Goal:** Make the new `SalesInvoiceService` and `SalesInvoiceManager` available through the `ApplicationCore` instance.
   *   **File to Update:** `app/core/application_core.py`
   *   **Checklist & Tasks:**
        *   [ ] **Import**: Import `SalesInvoiceService` from `app.services.business_services` and `SalesInvoiceManager` from `app.business_logic.sales_invoice_manager`.
        *   [ ] **Instance Variables**: Add new private instance variable placeholders in `ApplicationCore.__init__`:
            *   `self._sales_invoice_service_instance: Optional[SalesInvoiceService] = None`
            *   `self._sales_invoice_manager_instance: Optional[SalesInvoiceManager] = None`
        *   [ ] **Instantiation in `startup()`**: In `ApplicationCore.startup()`, instantiate `SalesInvoiceService` and then `SalesInvoiceManager`, injecting their dependencies. This should be done after other core and business services (like `CustomerService`, `ProductService`, `TaxCodeService`, `SequenceService`, `TaxCalculator`) are ready.
            ```python
            # In ApplicationCore.startup()
            self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self)
            self._sales_invoice_manager_instance = SalesInvoiceManager(
                sales_invoice_service=self.sales_invoice_service, # Use property
                customer_service=self.customer_service,
                product_service=self.product_service,
                tax_code_service=self.tax_code_service,
                tax_calculator=self.tax_calculator, # Assumes self.tax_calculator is initialized
                sequence_service=self.sequence_service, # Assumes self.sequence_service is initialized
                app_core=self
            )
            ```
        *   [ ] **Properties**: Expose `SalesInvoiceService` and `SalesInvoiceManager` via public properties:
            ```python
            @property
            def sales_invoice_service(self) -> SalesInvoiceService:
                if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
                return self._sales_invoice_service_instance

            @property
            def sales_invoice_manager(self) -> SalesInvoiceManager:
                if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
                return self._sales_invoice_manager_instance
            ```

This integration follows the established pattern for other services and managers in `ApplicationCore`.
</think>

This is wonderful news! The application's continued stability after each incremental backend addition is a strong sign of the architecture's soundness and the careful implementation.

We are in the final step of **Phase A: Backend for Basic Sales Invoicing**.
Steps A1 (DTOs), A2 (Interface), A3 (Service), and A4 (Manager) for Sales Invoices are now complete.

The next and final step for this backend phase is **A5: Integrate `SalesInvoiceService` and `SalesInvoiceManager` into `app/core/application_core.py`**. This will make these new components available globally within the application framework.

---
**A5. Update `app/core/application_core.py` to Integrate Sales Invoice Components**

**Goal:** Instantiate `SalesInvoiceService` and `SalesInvoiceManager` within `ApplicationCore` and expose them via properties.

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
from app.business_logic.sales_invoice_manager import SalesInvoiceManager # New Import

# Services
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService, FiscalYearService
from app.services.business_services import CustomerService, VendorService, ProductService, SalesInvoiceService # New Import for SalesInvoiceService

# Utilities
from app.utils.sequence_generator import SequenceGenerator # Still used by JE Manager

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
        # ... (other existing service placeholders)
        self._customer_service_instance: Optional[CustomerService] = None
        self._vendor_service_instance: Optional[VendorService] = None
        self._product_service_instance: Optional[ProductService] = None
        self._sales_invoice_service_instance: Optional[SalesInvoiceService] = None # New Placeholder

        # --- Manager Instance Placeholders ---
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        # ... (other existing manager placeholders)
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None
        self._sales_invoice_manager_instance: Optional[SalesInvoiceManager] = None # New Placeholder

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
        self._product_service_instance = ProductService(self.db_manager, self)
        self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self) # New Instantiation

        # Initialize Managers (dependencies should be initialized services)
        # SequenceGenerator is used by JournalEntryManager.
        # SalesInvoiceManager will use SequenceService directly for DB function call.
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) 

        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        self._je_manager_instance = JournalEntryManager(
            self.journal_service, self.account_service, 
            self.fiscal_period_service, py_sequence_generator, self # py_sequence_generator used here
        )
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 
        self._tax_calculator_instance = TaxCalculator(self.tax_code_service) # TaxCalculator needs TaxCodeService
        self._gst_manager_instance = GSTManager(
            self.tax_code_service, self.journal_service, self.company_settings_service,
            self.gst_return_service, self.account_service, self.fiscal_period_service,
            py_sequence_generator, self # py_sequence_generator if GST settlement JE needs it
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
        self._sales_invoice_manager_instance = SalesInvoiceManager( # New Instantiation
            sales_invoice_service=self.sales_invoice_service,
            customer_service=self.customer_service,
            product_service=self.product_service,
            tax_code_service=self.tax_code_service,
            tax_calculator=self.tax_calculator, # Pass initialized TaxCalculator
            sequence_service=self.sequence_service, # Pass initialized SequenceService
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
    # ... (other existing service properties) ...
    @property
    def account_service(self) -> AccountService: # ...
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> JournalService: # ...
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance
    @property
    def fiscal_period_service(self) -> FiscalPeriodService: # ...
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def fiscal_year_service(self) -> FiscalYearService: # ...
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
    @property
    def sequence_service(self) -> SequenceService: # ...
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> CompanySettingsService: # ...
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def tax_code_service(self) -> TaxCodeService: # ...
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> GSTReturnService: # ...
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> AccountTypeService:  # ...
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> CurrencyRepoService: # ...
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def currency_service(self) -> CurrencyRepoService: # ...
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyService (CurrencyRepoService) not initialized.")
        return self._currency_repo_service_instance
    @property
    def exchange_rate_service(self) -> ExchangeRateService: # ...
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def configuration_service(self) -> ConfigurationService: # ...
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance
    @property
    def customer_service(self) -> CustomerService: # ...
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance
    @property
    def vendor_service(self) -> VendorService: # ...
        if not self._vendor_service_instance: raise RuntimeError("VendorService not initialized.")
        return self._vendor_service_instance
    @property
    def product_service(self) -> ProductService: # ...
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance
    @property
    def sales_invoice_service(self) -> SalesInvoiceService: # New Property
        if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
        return self._sales_invoice_service_instance

    # --- Manager Properties ---
    # ... (other existing manager properties) ...
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager: # ...
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: # ...
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> JournalEntryManager: # ...
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance
    @property
    def fiscal_period_manager(self) -> FiscalPeriodManager: # ...
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance
    @property
    def currency_manager(self) -> CurrencyManager: # ...
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance
    @property
    def gst_manager(self) -> GSTManager: # ...
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance
    @property
    def tax_calculator(self) -> TaxCalculator: # ...
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance
    @property
    def financial_statement_generator(self) -> FinancialStatementGenerator: # ...
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance
    @property
    def report_engine(self) -> ReportEngine: # ...
        if not self._report_engine_instance: raise RuntimeError("ReportEngine not initialized.")
        return self._report_engine_instance
    @property
    def customer_manager(self) -> CustomerManager: # ...
        if not self._customer_manager_instance: raise RuntimeError("CustomerManager not initialized.")
        return self._customer_manager_instance
    @property
    def vendor_manager(self) -> VendorManager: # ...
        if not self._vendor_manager_instance: raise RuntimeError("VendorManager not initialized.")
        return self._vendor_manager_instance
    @property
    def product_manager(self) -> ProductManager: # ...
        if not self._product_manager_instance: raise RuntimeError("ProductManager not initialized.")
        return self._product_manager_instance
    @property
    def sales_invoice_manager(self) -> SalesInvoiceManager: # New Property
        if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
        return self._sales_invoice_manager_instance

```

**Validation for `app/core/application_core.py`:**
*   **Imports**: Added `from app.business_logic.sales_invoice_manager import SalesInvoiceManager` and `from app.services.business_services import ... SalesInvoiceService`.
*   **Instance Variables**: Added `_sales_invoice_service_instance` and `_sales_invoice_manager_instance` placeholders.
*   **`startup()` Method**:
    *   `self._sales_invoice_service_instance` is instantiated correctly.
    *   `self._sales_invoice_manager_instance` is instantiated. Dependencies for `SalesInvoiceManager` were: `sales_invoice_service`, `customer_service`, `product_service`, `tax_code_service`, `tax_calculator`, and `sequence_service`. All these services are initialized before `SalesInvoiceManager` and passed correctly using their respective properties.
*   **Properties**: Added public properties `sales_invoice_service` and `sales_invoice_manager`.
*   The overall structure and order of instantiations have been maintained.

This completes Phase A (Backend) for the Basic Sales Invoicing module. All necessary backend components are now in place and integrated into `ApplicationCore`. The application should continue to launch cleanly.

The next phase will be **Phase B: Frontend UI for Sales Invoicing**, starting with creating the `SalesInvoiceTableModel` and `SalesInvoiceDialog`.
