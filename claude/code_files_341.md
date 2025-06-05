<think>
The application is still hitting an `ImportError` due to a circular import involving `AccountService`. This time, the traceback indicates the cycle is being formed when `app.core.application_core.py` tries to import `AccountService` directly.

**Error Analysis (New Traceback):**

1.  App starts -> ... -> `app.utils.sequence_generator` imports `app.services.core_services.SequenceService`.
2.  This triggers `app.services.__init__.py` to load, which attempts to import `AccountService` from `app.services.account_service`.
3.  `app.services.account_service.py` starts loading. It imports `DatabaseManager`.
4.  `DatabaseManager` (via `app.core.__init__`) imports `ApplicationCore`.
5.  `app.core.application_core.py` (line 19) attempts a direct module-level import: `from app.services.account_service import AccountService`.

**The Circular Dependency:**
`app.services.__init__` (tries to import `AccountService`)
  -> `app.services.account_service` (starts loading)
    -> ... (chain eventually needs `ApplicationCore` for context/dependencies like `db_manager` or `logger`, or because `AccountService` takes `app_core` in `__init__`)
      -> `app.core.application_core` (starts loading)
        -> `from app.services.account_service import AccountService` (tries to import `AccountService` *again* while it's still being initialized from step 2).

The previous fixes addressed managers importing services directly. Now, `ApplicationCore` itself is directly importing `AccountService` (and likely other services) at the module level, which is problematic if those services (like `AccountService`) need `ApplicationCore` (or components it initializes, like `DatabaseManager`) to be available during their own module-level processing or constructor.

**Solution Strategy:**

`ApplicationCore` is the central piece that *instantiates* services. It should not import service *classes* at the module level if those service modules might, through their own imports, try to access `ApplicationCore` or things it sets up *before* `ApplicationCore`'s module is fully loaded.

The services are instantiated within `ApplicationCore.startup()` and assigned to instance attributes (e.g., `self._account_service_instance`). Properties then expose these instances (e.g., `self.account_service`).

**File to Modify:** `app/core/application_core.py`

**Detailed Plan for Fixing `ApplicationCore`:**

1.  **Modify `app/core/application_core.py`**:
    *   Examine all direct service imports at the top of the file:
        ```python
        # app/core/application_core.py
        # ...
        from app.services.account_service import AccountService # <<< PROBLEM
        from app.services.fiscal_period_service import FiscalPeriodService # Likely problem
        from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService # Likely problem
        from app.services.tax_service import TaxCodeService, GSTReturnService # Likely problem
        from app.services.accounting_services import (
            AccountTypeService, CurrencyService as CurrencyRepoService, 
            ExchangeRateService, FiscalYearService, DimensionService 
        ) # Likely problem
        from app.services.business_services import (
            CustomerService, VendorService, ProductService, 
            SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
            BankAccountService, BankTransactionService, PaymentService, 
            BankReconciliationService
        ) # Likely problem
        from app.services.audit_services import AuditLogService # Likely problem
        # ...
        # Manager imports also exist here, which were fixed by making *them* use conditional imports for services.
        ```
    *   All these direct service imports (that are used for type hints of instance attributes or for direct instantiation in `startup`) should be moved into the `if TYPE_CHECKING:` block.
    *   The `startup()` method already uses local imports for `JournalService` and managers that might cause deeper cycles. This pattern should be extended or confirmed for all service instantiations if their direct top-level import is problematic.
    *   The properties like `@property def account_service(self) -> AccountService:` already use the correct type hint. The issue is the module-level `from app.services.account_service import AccountService`.

**Revised Plan for `app/core/application_core.py`:**
1.  Remove all direct, top-level `from app.services... import ...Service` statements.
2.  Add all these service class imports into the `if TYPE_CHECKING:` block (which already exists for some managers).
    ```python
    if TYPE_CHECKING:
        # ... existing manager hints ...
        from app.services.account_service import AccountService
        from app.services.journal_service import JournalService # Already here
        from app.services.fiscal_period_service import FiscalPeriodService
        # ... add ALL other service classes imported at top level before ...
    ```
3.  In the `startup()` method, when instantiating services, ensure the classes are available.
    *   Currently, `startup` does:
        ```python
        self._account_service_instance = AccountService(self.db_manager, self)
        # ...
        from app.services.journal_service import JournalService # Local import
        self._journal_service_instance = JournalService(self.db_manager, self)
        ```
    *   This means `AccountService` (and others imported at the top) *must* be available when `startup()` is called. If we move their imports to `TYPE_CHECKING`, then `startup()` must also use local imports for them, just like it does for `JournalService`.

**Corrected Plan for `app/core/application_core.py`:**
1.  Remove *all* service class imports from the top level of the file (e.g., `from app.services.account_service import AccountService`).
2.  Ensure *all* these service class names are imported under the `if TYPE_CHECKING:` block for type hinting purposes for the properties.
3.  In the `startup()` method, just before each service is instantiated, perform a local import for that specific service class. For example:
    ```python
    # In ApplicationCore.startup()
    from app.services.account_service import AccountService # Local import
    self._account_service_instance = AccountService(self.db_manager, self)

    from app.services.fiscal_period_service import FiscalPeriodService # Local import
    self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager, self) # Note: FiscalPeriodService init differs
    
    # ... and so on for ALL services currently imported at the top.
    ```
    The `JournalService` import is already local in `startup()`. This pattern needs to be applied to all other services that were previously imported at the top level.

This is a more significant refactoring of `application_core.py` but is the standard way to handle such dependencies when `ApplicationCore` is a central hub.

Let's systematically list the services `ApplicationCore` imports at the top level and plans to instantiate:
*   `AccountService`
*   `FiscalPeriodService`
*   `SequenceService`, `CompanySettingsService`, `ConfigurationService`
*   `TaxCodeService`, `GSTReturnService`
*   `AccountTypeService`, `CurrencyRepoService` (as `CurrencyService`), `ExchangeRateService`, `FiscalYearService`, `DimensionService`
*   `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`, `PurchaseInvoiceService`, `InventoryMovementService`, `BankAccountService`, `BankTransactionService`, `PaymentService`, `BankReconciliationService`
*   `AuditLogService`

All these will need their top-level imports removed and replaced with local imports within `startup()` just before instantiation, and their names added to the `TYPE_CHECKING` block for property type hints.

This is a comprehensive fix for this class of circular import errors originating from `ApplicationCore`.

</think>

You are correct, we are still chasing circular import errors. The traceback now clearly indicates that `app/core/application_core.py` itself is causing a cycle by directly importing `AccountService` at the module level, while `AccountService` (or its dependencies) indirectly leads back to needing `ApplicationCore`.

The strategy of moving direct imports within managers to `TYPE_CHECKING` blocks and using string literals for constructor type hints was correct for those managers. Now, we need to apply a similar principle to `ApplicationCore`: it should not import service *classes* directly at the module level if those services might cause a cycle. Instead, it should import them locally within its `startup()` method just before instantiation. Type hints for its properties can use `TYPE_CHECKING` imports.

**File to Modify:** `app/core/application_core.py`

**Detailed Plan & Checklist:**

1.  **Modify `app/core/application_core.py`**:
    *   [X] **Remove all direct service class imports** from the top of the file.
        *   This includes `AccountService`, `FiscalPeriodService`, `SequenceService`, `CompanySettingsService`, `ConfigurationService`, `TaxCodeService`, `GSTReturnService`, `AccountTypeService`, `CurrencyService` (aliased as `CurrencyRepoService`), `ExchangeRateService`, `FiscalYearService`, `DimensionService`, `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`, `PurchaseInvoiceService`, `InventoryMovementService`, `BankAccountService`, `BankTransactionService`, `PaymentService`, `BankReconciliationService`, and `AuditLogService`.
    *   [X] **Add all these service class names to the `if TYPE_CHECKING:` block** for type hinting the properties (e.g., `@property def account_service(self) -> "AccountService":`). Many are already hinted with strings like `"JournalService"`, which is also fine. For consistency and better IDE support if types are available, `TYPE_CHECKING` imports are preferred.
    *   [X] **In the `startup()` method**:
        *   For *each* service that was previously imported at the top level and is instantiated in `startup()`, add a local import statement immediately before its instantiation.
        *   Example:
            ```python
            # Before:
            # self._account_service_instance = AccountService(self.db_manager, self)

            # After:
            from app.services.account_service import AccountService # Local import
            self._account_service_instance = AccountService(self.db_manager, self)
            ```
        *   Apply this pattern to all service instantiations in `startup()`:
            `SequenceService`, `CompanySettingsService`, `ConfigurationService`, `AccountService`, `FiscalPeriodService`, `FiscalYearService`, `AccountTypeService`, `CurrencyRepoService`, `ExchangeRateService`, `DimensionService`, `TaxCodeService`, `GSTReturnService`, `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`, `PurchaseInvoiceService`, `InventoryMovementService`, `BankAccountService`, `BankTransactionService`, `PaymentService`, `AuditLogService`, `BankReconciliationService`.
            (Note: `JournalService` already follows this local import pattern in `startup()`).
    *   [X] **Manager Imports**: The direct imports for managers (e.g., `from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager`) at the top of `ApplicationCore` are generally acceptable *provided those manager files themselves now use conditional imports for their service dependencies*, which we have been fixing. The key is that these manager modules should not trigger the problematic service module loading prematurely.

This systematic change in `ApplicationCore` should robustly break the circular dependencies related to service initializations.

---
**Complete Updated File: `app/core/application_core.py`**
---
```python
# File: app/core/application_core.py
from typing import Optional, Any, TYPE_CHECKING
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager 
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

# Manager imports are generally okay here if they don't cause cycles themselves
# (which we are fixing by making managers use TYPE_CHECKING for services)
from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.business_logic.customer_manager import CustomerManager 
from app.business_logic.vendor_manager import VendorManager 
from app.business_logic.product_manager import ProductManager
from app.business_logic.bank_account_manager import BankAccountManager 
from app.business_logic.bank_transaction_manager import BankTransactionManager

# REMOVE All direct service imports from here. They will be imported locally in startup().
# Example of removed lines:
# from app.services.account_service import AccountService
# from app.services.fiscal_period_service import FiscalPeriodService
# etc.

import logging 

if TYPE_CHECKING:
    # Imports for type hinting that might cause circular dependencies if imported at top level
    from app.services.journal_service import JournalService
    from app.accounting.journal_entry_manager import JournalEntryManager
    from app.accounting.fiscal_period_manager import FiscalPeriodManager
    from app.accounting.currency_manager import CurrencyManager
    from app.business_logic.sales_invoice_manager import SalesInvoiceManager
    from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager
    from app.business_logic.payment_manager import PaymentManager
    from app.tax.gst_manager import GSTManager
    from app.tax.tax_calculator import TaxCalculator
    from app.reporting.financial_statement_generator import FinancialStatementGenerator
    from app.reporting.report_engine import ReportEngine
    from app.reporting.dashboard_manager import DashboardManager
    from app.utils.sequence_generator import SequenceGenerator
    
    # Add ALL service classes here for property type hints
    from app.services.account_service import AccountService
    from app.services.fiscal_period_service import FiscalPeriodService
    from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
    from app.services.tax_service import TaxCodeService, GSTReturnService 
    from app.services.accounting_services import (
        AccountTypeService, CurrencyService as CurrencyRepoService, 
        ExchangeRateService, FiscalYearService, DimensionService 
    )
    from app.services.business_services import (
        CustomerService, VendorService, ProductService, 
        SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
        BankAccountService, BankTransactionService, PaymentService, 
        BankReconciliationService
    )
    from app.services.audit_services import AuditLogService

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

        # Service Instance Placeholders
        self._account_service_instance: Optional["AccountService"] = None
        self._journal_service_instance: Optional["JournalService"] = None 
        self._fiscal_period_service_instance: Optional["FiscalPeriodService"] = None
        self._fiscal_year_service_instance: Optional["FiscalYearService"] = None
        self._sequence_service_instance: Optional["SequenceService"] = None
        self._company_settings_service_instance: Optional["CompanySettingsService"] = None
        self._configuration_service_instance: Optional["ConfigurationService"] = None
        self._tax_code_service_instance: Optional["TaxCodeService"] = None
        self._gst_return_service_instance: Optional["GSTReturnService"] = None
        self._account_type_service_instance: Optional["AccountTypeService"] = None
        self._currency_repo_service_instance: Optional["CurrencyRepoService"] = None
        self._exchange_rate_service_instance: Optional["ExchangeRateService"] = None
        self._dimension_service_instance: Optional["DimensionService"] = None
        self._customer_service_instance: Optional["CustomerService"] = None
        self._vendor_service_instance: Optional["VendorService"] = None
        self._product_service_instance: Optional["ProductService"] = None
        self._sales_invoice_service_instance: Optional["SalesInvoiceService"] = None
        self._purchase_invoice_service_instance: Optional["PurchaseInvoiceService"] = None 
        self._inventory_movement_service_instance: Optional["InventoryMovementService"] = None
        self._bank_account_service_instance: Optional["BankAccountService"] = None 
        self._bank_transaction_service_instance: Optional["BankTransactionService"] = None
        self._payment_service_instance: Optional["PaymentService"] = None
        self._audit_log_service_instance: Optional["AuditLogService"] = None
        self._bank_reconciliation_service_instance: Optional["BankReconciliationService"] = None

        # Manager Instance Placeholders
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional["JournalEntryManager"] = None 
        self._fp_manager_instance: Optional["FiscalPeriodManager"] = None
        self._currency_manager_instance: Optional["CurrencyManager"] = None
        self._gst_manager_instance: Optional["GSTManager"] = None
        self._tax_calculator_instance: Optional["TaxCalculator"] = None
        self._financial_statement_generator_instance: Optional["FinancialStatementGenerator"] = None
        self._report_engine_instance: Optional["ReportEngine"] = None
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None
        self._sales_invoice_manager_instance: Optional["SalesInvoiceManager"] = None
        self._purchase_invoice_manager_instance: Optional["PurchaseInvoiceManager"] = None
        self._bank_account_manager_instance: Optional[BankAccountManager] = None
        self._bank_transaction_manager_instance: Optional[BankTransactionManager] = None
        self._payment_manager_instance: Optional["PaymentManager"] = None
        self._dashboard_manager_instance: Optional["DashboardManager"] = None
        
        self.logger.info("ApplicationCore initialized.")

    async def startup(self):
        self.logger.info("ApplicationCore starting up...")
        await self.db_manager.initialize() 
        
        # Import services locally within startup
        from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
        from app.services.account_service import AccountService
        from app.services.fiscal_period_service import FiscalPeriodService
        from app.services.accounting_services import (
            AccountTypeService, CurrencyService as CurrencyRepoService, 
            ExchangeRateService, FiscalYearService, DimensionService 
        )
        from app.services.tax_service import TaxCodeService, GSTReturnService 
        from app.services.business_services import (
            CustomerService, VendorService, ProductService, 
            SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
            BankAccountService, BankTransactionService, PaymentService, 
            BankReconciliationService
        )
        from app.services.audit_services import AuditLogService
        from app.services.journal_service import JournalService 
        
        # Initialize services
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)
        self._account_service_instance = AccountService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager) # FiscalPeriodService does not take app_core
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
        self._dimension_service_instance = DimensionService(self.db_manager, self)
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        self._customer_service_instance = CustomerService(self.db_manager, self)
        self._vendor_service_instance = VendorService(self.db_manager, self) 
        self._product_service_instance = ProductService(self.db_manager, self)
        self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self)
        self._purchase_invoice_service_instance = PurchaseInvoiceService(self.db_manager, self) 
        self._inventory_movement_service_instance = InventoryMovementService(self.db_manager, self) 
        self._bank_account_service_instance = BankAccountService(self.db_manager, self) 
        self._bank_transaction_service_instance = BankTransactionService(self.db_manager, self)
        self._payment_service_instance = PaymentService(self.db_manager, self) 
        self._audit_log_service_instance = AuditLogService(self.db_manager, self)
        self._bank_reconciliation_service_instance = BankReconciliationService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        
        from app.utils.sequence_generator import SequenceGenerator 
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) 
        
        from app.accounting.journal_entry_manager import JournalEntryManager
        from app.accounting.fiscal_period_manager import FiscalPeriodManager
        from app.accounting.currency_manager import CurrencyManager
        from app.tax.gst_manager import GSTManager
        from app.tax.tax_calculator import TaxCalculator
        from app.reporting.financial_statement_generator import FinancialStatementGenerator
        from app.reporting.report_engine import ReportEngine
        from app.reporting.dashboard_manager import DashboardManager
        from app.business_logic.sales_invoice_manager import SalesInvoiceManager
        from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager
        from app.business_logic.payment_manager import PaymentManager
        
        # Initialize Managers
        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        self._je_manager_instance = JournalEntryManager(self.journal_service, self.account_service, self.fiscal_period_service, self)
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 
        self._tax_calculator_instance = TaxCalculator(self.tax_code_service) 
        self._gst_manager_instance = GSTManager(self.tax_code_service, self.journal_service, self.company_settings_service, self.gst_return_service, self.account_service, self.fiscal_period_service, py_sequence_generator, self)
        self._financial_statement_generator_instance = FinancialStatementGenerator(self.account_service, self.journal_service, self.fiscal_period_service, self.account_type_service, self.tax_code_service, self.company_settings_service, self.dimension_service)
        self._report_engine_instance = ReportEngine(self)
        self._customer_manager_instance = CustomerManager(customer_service=self.customer_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._vendor_manager_instance = VendorManager( vendor_service=self.vendor_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._product_manager_instance = ProductManager( product_service=self.product_service, account_service=self.account_service, tax_code_service=self.tax_code_service, app_core=self)
        self._sales_invoice_manager_instance = SalesInvoiceManager(sales_invoice_service=self.sales_invoice_service, customer_service=self.customer_service, product_service=self.product_service, tax_code_service=self.tax_code_service, tax_calculator=self.tax_calculator, sequence_service=self.sequence_service, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self, inventory_movement_service=self.inventory_movement_service)
        self._purchase_invoice_manager_instance = PurchaseInvoiceManager( purchase_invoice_service=self.purchase_invoice_service, vendor_service=self.vendor_service, product_service=self.product_service, tax_code_service=self.tax_code_service, tax_calculator=self.tax_calculator, sequence_service=self.sequence_service, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self, inventory_movement_service=self.inventory_movement_service)
        self._bank_account_manager_instance = BankAccountManager( bank_account_service=self.bank_account_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._bank_transaction_manager_instance = BankTransactionManager( bank_transaction_service=self.bank_transaction_service, bank_account_service=self.bank_account_service, app_core=self)
        self._payment_manager_instance = PaymentManager( payment_service=self.payment_service, sequence_service=self.sequence_service, bank_account_service=self.bank_account_service, customer_service=self.customer_service, vendor_service=self.vendor_service, sales_invoice_service=self.sales_invoice_service, purchase_invoice_service=self.purchase_invoice_service, journal_entry_manager=self.journal_entry_manager, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self)
        self._dashboard_manager_instance = DashboardManager(self)
        
        self.module_manager.load_all_modules() 
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self): 
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    # Service Properties
    @property
    def account_service(self) -> "AccountService": 
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> "JournalService": 
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance 
    @property
    def fiscal_period_service(self) -> "FiscalPeriodService": 
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def fiscal_year_service(self) -> "FiscalYearService": 
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
    @property
    def sequence_service(self) -> "SequenceService": 
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> "CompanySettingsService": 
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def configuration_service(self) -> "ConfigurationService": 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance
    @property
    def tax_code_service(self) -> "TaxCodeService": 
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> "GSTReturnService": 
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> "AccountTypeService":  
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> "CurrencyRepoService": 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property 
    def currency_service(self) -> "CurrencyRepoService": 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyService (CurrencyRepoService) not initialized.")
        return self._currency_repo_service_instance
    @property
    def exchange_rate_service(self) -> "ExchangeRateService": 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def dimension_service(self) -> "DimensionService": 
        if not self._dimension_service_instance: raise RuntimeError("DimensionService not initialized.")
        return self._dimension_service_instance
    @property
    def customer_service(self) -> "CustomerService": 
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance
    @property
    def vendor_service(self) -> "VendorService": 
        if not self._vendor_service_instance: raise RuntimeError("VendorService not initialized.")
        return self._vendor_service_instance
    @property
    def product_service(self) -> "ProductService": 
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance
    @property
    def sales_invoice_service(self) -> "SalesInvoiceService": 
        if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
        return self._sales_invoice_service_instance
    @property
    def purchase_invoice_service(self) -> "PurchaseInvoiceService": 
        if not self._purchase_invoice_service_instance: raise RuntimeError("PurchaseInvoiceService not initialized.")
        return self._purchase_invoice_service_instance
    @property
    def inventory_movement_service(self) -> "InventoryMovementService": 
        if not self._inventory_movement_service_instance: raise RuntimeError("InventoryMovementService not initialized.")
        return self._inventory_movement_service_instance
    @property
    def bank_account_service(self) -> "BankAccountService": 
        if not self._bank_account_service_instance: raise RuntimeError("BankAccountService not initialized.")
        return self._bank_account_service_instance
    @property
    def bank_transaction_service(self) -> "BankTransactionService": 
        if not self._bank_transaction_service_instance: raise RuntimeError("BankTransactionService not initialized.")
        return self._bank_transaction_service_instance
    @property
    def payment_service(self) -> "PaymentService": 
        if not self._payment_service_instance: raise RuntimeError("PaymentService not initialized.")
        return self._payment_service_instance
    @property
    def audit_log_service(self) -> "AuditLogService": 
        if not self._audit_log_service_instance: raise RuntimeError("AuditLogService not initialized.")
        return self._audit_log_service_instance
    @property
    def bank_reconciliation_service(self) -> "BankReconciliationService":
        if not self._bank_reconciliation_service_instance: raise RuntimeError("BankReconciliationService not initialized.")
        return self._bank_reconciliation_service_instance

    # Manager Properties
    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager: 
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property 
    def accounting_service(self) -> ChartOfAccountsManager: 
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> "JournalEntryManager": 
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance 
    @property
    def fiscal_period_manager(self) -> "FiscalPeriodManager": 
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance 
    @property
    def currency_manager(self) -> "CurrencyManager": 
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance 
    @property
    def gst_manager(self) -> "GSTManager": 
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance 
    @property
    def tax_calculator(self) -> "TaxCalculator": 
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance 
    @property
    def financial_statement_generator(self) -> "FinancialStatementGenerator": 
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance 
    @property
    def report_engine(self) -> "ReportEngine": 
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
    def sales_invoice_manager(self) -> "SalesInvoiceManager": 
        if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
        return self._sales_invoice_manager_instance 
    @property
    def purchase_invoice_manager(self) -> "PurchaseInvoiceManager": 
        if not self._purchase_invoice_manager_instance: raise RuntimeError("PurchaseInvoiceManager not initialized.")
        return self._purchase_invoice_manager_instance 
    @property
    def bank_account_manager(self) -> BankAccountManager: 
        if not self._bank_account_manager_instance: raise RuntimeError("BankAccountManager not initialized.")
        return self._bank_account_manager_instance
    @property
    def bank_transaction_manager(self) -> BankTransactionManager: 
        if not self._bank_transaction_manager_instance: raise RuntimeError("BankTransactionManager not initialized.")
        return self._bank_transaction_manager_instance
    @property
    def payment_manager(self) -> "PaymentManager": 
        if not self._payment_manager_instance: raise RuntimeError("PaymentManager not initialized.")
        return self._payment_manager_instance 
    @property
    def dashboard_manager(self) -> "DashboardManager":
        if not self._dashboard_manager_instance: raise RuntimeError("DashboardManager not initialized.")
        return self._dashboard_manager_instance 
```

---
**Diff for `app/core/application_core.py`:**
```diff
--- app/core/application_core.py-original
+++ app/core/application_core.py
@@ -15,24 +15,10 @@
 from app.business_logic.bank_account_manager import BankAccountManager 
 from app.business_logic.bank_transaction_manager import BankTransactionManager
 
-# Services (Direct imports if they don't create cycles starting from here)
-from app.services.account_service import AccountService
-from app.services.fiscal_period_service import FiscalPeriodService
-from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
-from app.services.tax_service import TaxCodeService, GSTReturnService 
-from app.services.accounting_services import (
-    AccountTypeService, CurrencyService as CurrencyRepoService, 
-    ExchangeRateService, FiscalYearService, DimensionService 
-)
-from app.services.business_services import (
-    CustomerService, VendorService, ProductService, 
-    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
-    BankAccountService, BankTransactionService, PaymentService, 
-    BankReconciliationService
-)
-from app.services.audit_services import AuditLogService
-
-# Utilities
-# Removed: from app.utils.sequence_generator import SequenceGenerator # Moved to TYPE_CHECKING and local import
+# REMOVE All direct service imports from here. They will be imported locally in startup().
+# Example of removed lines:
+# from app.services.account_service import AccountService
+# from app.services.fiscal_period_service import FiscalPeriodService
+# etc.
+
 import logging 
 
 if TYPE_CHECKING:
@@ -49,6 +35,22 @@
     from app.reporting.report_engine import ReportEngine
     from app.reporting.dashboard_manager import DashboardManager
     from app.utils.sequence_generator import SequenceGenerator # Added for type hinting if needed elsewhere in class
+    
+    # Add ALL service classes here for property type hints
+    from app.services.account_service import AccountService
+    from app.services.fiscal_period_service import FiscalPeriodService
+    from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
+    from app.services.tax_service import TaxCodeService, GSTReturnService 
+    from app.services.accounting_services import (
+        AccountTypeService, CurrencyService as CurrencyRepoService, 
+        ExchangeRateService, FiscalYearService, DimensionService 
+    )
+    from app.services.business_services import (
+        CustomerService, VendorService, ProductService, 
+        SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
+        BankAccountService, BankTransactionService, PaymentService, 
+        BankReconciliationService
+    )
+    from app.services.audit_services import AuditLogService
 
 class ApplicationCore:
     def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
@@ -62,46 +64,46 @@
         if not hasattr(self.db_manager, 'logger') or self.db_manager.logger is None: self.db_manager.logger = self.logger
 
         self.security_manager = SecurityManager(self.db_manager)
-        self.module_manager = ModuleManager(self)
+        self.module_manager = ModuleManager(self) # type: ignore[no-untyped-call]
 
         # Service Instance Placeholders
-        self._account_service_instance: Optional[AccountService] = None
+        self._account_service_instance: Optional["AccountService"] = None
         self._journal_service_instance: Optional[JournalService] = None 
-        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
-        self._fiscal_year_service_instance: Optional[FiscalYearService] = None
-        self._sequence_service_instance: Optional[SequenceService] = None
-        self._company_settings_service_instance: Optional[CompanySettingsService] = None
-        self._configuration_service_instance: Optional[ConfigurationService] = None
-        self._tax_code_service_instance: Optional[TaxCodeService] = None
-        self._gst_return_service_instance: Optional[GSTReturnService] = None
-        self._account_type_service_instance: Optional[AccountTypeService] = None
+        self._fiscal_period_service_instance: Optional["FiscalPeriodService"] = None
+        self._fiscal_year_service_instance: Optional["FiscalYearService"] = None
+        self._sequence_service_instance: Optional["SequenceService"] = None
+        self._company_settings_service_instance: Optional["CompanySettingsService"] = None
+        self._configuration_service_instance: Optional["ConfigurationService"] = None
+        self._tax_code_service_instance: Optional["TaxCodeService"] = None
+        self._gst_return_service_instance: Optional["GSTReturnService"] = None
+        self._account_type_service_instance: Optional["AccountTypeService"] = None
         self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
-        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
-        self._dimension_service_instance: Optional[DimensionService] = None
-        self._customer_service_instance: Optional[CustomerService] = None
-        self._vendor_service_instance: Optional[VendorService] = None
-        self._product_service_instance: Optional[ProductService] = None
-        self._sales_invoice_service_instance: Optional[SalesInvoiceService] = None
-        self._purchase_invoice_service_instance: Optional[PurchaseInvoiceService] = None 
-        self._inventory_movement_service_instance: Optional[InventoryMovementService] = None
-        self._bank_account_service_instance: Optional[BankAccountService] = None 
-        self._bank_transaction
