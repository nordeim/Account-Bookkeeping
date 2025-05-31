<think>
The application launched successfully after the changes to `JournalEntryManager` and the implementation of `PurchaseInvoiceManager.post_purchase_invoice()`. This indicates that the core logic for posting Purchase Invoices (financial JE part) is now in place and the system is stable.

**1. Identify the Next Roadmap Goal:**

From the generated `README.md`:
Roadmap - "Current Focus / Short-term":
1.  **Purchase Invoicing**:
    *   Implement posting logic (JE creation) for Purchase Invoices. <-- **DONE (Financial JE)**
2.  **Sales Invoicing & Purchase Invoicing**:
    *   Enhance line item entry (e.g., more advanced product search/selection in dialogs).
    *   Handle inventory updates upon posting (for 'Inventory' type products). <-- **THIS IS NEXT**
3.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting for Trial Balance and General Ledger.
    *   Add more filtering options to existing reports (e.g., dimensions, transaction status).

The next logical step, directly related to both Sales and Purchase Invoicing posting, is **"Handle inventory updates upon posting (for 'Inventory' type products)."**

**2. Task Intake & Diagnostic Process:**

*   **Requirements Clarification**:
    *   When a Sales Invoice or Purchase Invoice containing 'Inventory' type products is posted:
        *   In addition to the financial Journal Entry, an `InventoryMovement` record must be created for each 'Inventory' type line item.
        *   **For Sales Invoice (Inventory Sold):**
            *   `InventoryMovement.movement_type` should be 'Sale'.
            *   `InventoryMovement.quantity` should be *negative* the quantity sold (representing stock outflow).
            *   `InventoryMovement.unit_cost` should be the current cost of the item sold (this is the tricky part - Cost of Goods Sold valuation).
            *   `InventoryMovement.total_cost` = `quantity` * `unit_cost`.
            *   `InventoryMovement.reference_type` = 'SalesInvoiceLine', `reference_id` = `sales_invoice_line.id`.
            *   The financial JE for COGS should also be created:
                *   Debit: Cost of Goods Sold Account (`Product.purchase_account_id` often used for COGS, or a dedicated COGS account).
                *   Credit: Inventory Account (`Product.inventory_account_id`).
                *   The amount is `total_cost` calculated above.
        *   **For Purchase Invoice (Inventory Purchased):**
            *   `InventoryMovement.movement_type` should be 'Purchase'.
            *   `InventoryMovement.quantity` should be *positive* the quantity purchased.
            *   `InventoryMovement.unit_cost` should be the `unit_price` from the purchase invoice line (after discount, before tax).
            *   `InventoryMovement.total_cost` = `quantity` * `unit_cost`.
            *   `InventoryMovement.reference_type` = 'PurchaseInvoiceLine', `reference_id` = `purchase_invoice_line.id`.
            *   The financial JE for inventory purchase (debiting inventory account) is already handled by `PurchaseInvoiceManager.post_purchase_invoice`. No *additional* financial JE is needed here for inventory movement itself, but the cost information is critical.
    *   **Costing Method**: The requirement "unit_cost should be the current cost of the item sold" implies a costing method is needed. Common methods are FIFO, LIFO, Weighted Average, Standard Cost. The current database schema (`business.inventory_summary` view, `business.inventory_movements` table) hints at a system that tracks quantity and cost, but doesn't explicitly define the costing method.
        *   For simplicity in this iteration, **Weighted Average Cost (WAC)** is often a good starting point for SMB software if a specific method isn't mandated. It requires calculating a new WAC after each purchase. When a sale occurs, the current WAC is used for COGS.
        *   The `business.inventory_summary` view already calculates `average_cost`. This can be leveraged.
    *   **Acceptance Criteria**:
        *   Posting a Sales Invoice with inventory items creates correct `InventoryMovement` records and a COGS/Inventory JE using current WAC.
        *   Posting a Purchase Invoice with inventory items creates correct `InventoryMovement` records (updating quantity and cost, which in turn affects WAC for future sales).
        *   The `business.inventory_summary` view reflects updated quantities and average costs.

*   **Systematic Diagnosis (Locate Relevant Code)**:
    *   `app/business_logic/sales_invoice_manager.py`: `post_invoice()` method needs to be extended.
    *   `app/business_logic/purchase_invoice_manager.py`: `post_purchase_invoice()` method needs to be extended.
    *   `app/models/business/inventory_movement.py`: `InventoryMovement` ORM model.
    *   `app/models/business/product.py`: `Product` model (for `inventory_account_id`, `purchase_account_id`).
    *   `app/services/business_services.py`: A new `InventoryMovementService` will be needed.
    *   `app/services/__init__.py`: Interface for `IInventoryMovementRepository`.
    *   `app/accounting/journal_entry_manager.py`: To create the COGS JE.
    *   Database: `business.inventory_summary` view logic might need checking or a function to get current WAC might be useful.

*   **Impact Assessment**:
    *   Modules requiring modification:
        *   `app/business_logic/sales_invoice_manager.py` (High)
        *   `app/business_logic/purchase_invoice_manager.py` (High)
        *   `app/services/business_services.py` (New service)
        *   `app/services/__init__.py` (New interface)
    *   Complexity: High. Implementing inventory costing correctly within transactions is complex.
    *   Testing: Crucial. Unit tests for WAC calculation, inventory movement creation, COGS JE. Integration tests for full invoice posting with inventory.

**3. Solution Architecture & Trade-Off Analysis (Focus on Costing & Integration):**

*   **Weighted Average Cost (WAC) Calculation**:
    *   WAC = Total Inventory Value / Total Inventory Quantity.
    *   **On Purchase**: New WAC = (Old Value + Purchase Value) / (Old Quantity + Purchase Quantity).
    *   **On Sale**: Use current WAC for COGS. Value of inventory decreases by (Quantity Sold * WAC). Quantity decreases. WAC itself *does not change* on a sale.
*   **Integration into Posting Methods**:
    *   The creation of `InventoryMovement` records and COGS JEs (for sales) should happen within the same database transaction as the main invoice posting and its financial JE.
    *   This means `SalesInvoiceManager.post_invoice` and `PurchaseInvoiceManager.post_purchase_invoice` will become more complex.
*   **`InventoryMovementService`**:
    *   A new service `InventoryMovementService` implementing `IInventoryMovementRepository` (basic CRUD for now) will be created to handle persistence of `InventoryMovement` records.
*   **Getting Current WAC for Sales**:
    *   **Option A**: Query the `business.inventory_summary` view for the product's `average_cost`.
        *   Pros: Uses existing view.
        *   Cons: View might not be transactionally consistent if it sums up movements that aren't yet committed within the *current* transaction. This is a significant risk.
    *   **Option B**: Calculate WAC on-the-fly by querying `Product.inventory_account_id` balance and summing `InventoryMovement.quantity` for that product up to the point of the current transaction *within the current session*. This is more complex.
    *   **Option C (Hybrid/Pragmatic for this iteration)**: Add `current_quantity_on_hand` and `current_total_value` (or `current_wac`) columns to the `business.products` table.
        *   These fields would be updated by triggers on `business.inventory_movements` or by the application after each inventory-affecting transaction.
        *   When selling, read `current_wac` from `business.products`.
        *   When purchasing, after saving the `InventoryMovement`, recalculate and update `current_wac` on `business.products`.
        *   Pros: Simplifies fetching WAC for sales.
        *   Cons: Denormalization; requires careful updates to maintain accuracy. Triggers are good for this. If done by application, needs strict transactional control.
        *   The `inventory_summary` view is already defined in `schema.sql` and calculates `current_quantity`, `average_cost`, `inventory_value`. Let's try to use this as the source of truth for WAC, acknowledging the transactional consistency challenge.
        *   **Re-evaluation for Option C/A**: The `inventory_summary` view computes these values. For a sale, we need the WAC *before* the current sale's movement.
            *   We can fetch the `average_cost` from `inventory_summary` for the product. This value represents the WAC based on all *committed* prior transactions. This is acceptable for WAC method.
*   **Default COGS Account**: `Product.purchase_account_id` is often used for COGS for simplicity. A dedicated COGS account could be configured on the Product or globally. For now, will use `Product.purchase_account_id` as COGS if `Product.inventory_account_id` is the inventory asset. If `purchase_account_id` is not set on product, use a system default COGS account (e.g. `SysAcc_DefaultCOGS` from `core.configuration`).

**Chosen Approach for WAC and JE:**

1.  **Purchases**:
    *   When a `PurchaseInvoiceLine` for an 'Inventory' item is processed during `PurchaseInvoiceManager.post_purchase_invoice`:
        *   Create an `InventoryMovement` record:
            *   `movement_type = 'Purchase'`
            *   `quantity = line.quantity`
            *   `unit_cost = line.line_subtotal / line.quantity` (cost after discount, before tax)
            *   `total_cost = line.line_subtotal`
        *   The existing financial JE (Debit Inventory Asset, Debit GST Input, Credit AP) is already correct for perpetual inventory.
2.  **Sales**:
    *   When a `SalesInvoiceLine` for an 'Inventory' item is processed during `SalesInvoiceManager.post_invoice`:
        *   **Fetch Current WAC**: Before creating the `InventoryMovement` for the sale, query `business.inventory_summary.average_cost` for the product. If the product is new and has no prior movements/summary, WAC might be based on its `purchase_price` or default to zero (handle this).
        *   Create an `InventoryMovement` record:
            *   `movement_type = 'Sale'`
            *   `quantity = -line.quantity` (negative)
            *   `unit_cost = current_wac_fetched`
            *   `total_cost = abs(quantity) * current_wac_fetched`
        *   **Create COGS Journal Entry**:
            *   Debit: COGS Account (use `line.product.purchase_account_id` or default `SysAcc_DefaultCOGS`).
            *   Credit: Inventory Account (`line.product.inventory_account_id`).
            *   Amount: `total_cost` calculated above.
            *   This JE must be part of the same transaction as the main Sales Invoice financial JE.

**4. Implementation Planning & Execution:**

**4.1 New Service: `app/services/business_services.py` - `InventoryMovementService`**
*   **Plan**:
    1.  Define `IInventoryMovementRepository` in `app/services/__init__.py`.
    2.  Implement `InventoryMovementService(IInventoryMovementRepository)`:
        *   `__init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None)`.
        *   `async def save(self, movement: InventoryMovement, session: Optional[AsyncSession] = None) -> InventoryMovement`: Persists an `InventoryMovement` object, using provided session or creating one.
*   **Checklist**:
    *   [ ] Define `IInventoryMovementRepository` interface in `app/services/__init__.py`.
    *   [ ] Implement `InventoryMovementService` class.
    *   [ ] Implement `save` method, handling optional session.
    *   [ ] Add `InventoryMovementService` and its interface to `app/services/__init__.py` `__all__`.
    *   [ ] Instantiate `InventoryMovementService` in `ApplicationCore.startup()` and add property.

**4.2 Modify `app/business_logic/purchase_invoice_manager.py` - `post_purchase_invoice`**
*   **Plan**:
    1.  Inject `InventoryMovementService` into `__init__`.
    2.  Inside the `async with session:` block in `post_purchase_invoice`:
        *   After successfully creating and posting the financial JE and before updating the PI status:
        *   Iterate through `invoice_to_post.lines`.
        *   If `line.product` exists and `ProductTypeEnum(line.product.product_type) == ProductTypeEnum.INVENTORY`:
            *   Create an `InventoryMovement` ORM instance:
                *   `product_id = line.product_id`
                *   `movement_date = invoice_to_post.invoice_date`
                *   `movement_type = InventoryMovementTypeEnum.PURCHASE.value`
                *   `quantity = line.quantity`
                *   `unit_cost = line.line_subtotal / line.quantity` (ensure quantity is not zero; already validated in `_validate_and_prepare_pi_data`)
                *   `total_cost = line.line_subtotal`
                *   `reference_type = 'PurchaseInvoiceLine'`
                *   `reference_id = line.id` (Ensure `line.id` is available after initial PI save/flush, which it should be if posting happens after initial save or lines are flushed with PI).
                *   `created_by_user_id = user_id`
            *   Call `await self.inventory_movement_service.save(inv_movement_orm, session=session)`.
*   **Checklist**:
    *   [ ] Inject `InventoryMovementService`.
    *   [ ] In `post_purchase_invoice`, iterate through lines *after* financial JE is confirmed but *within* the same transaction.
    *   [ ] Check if product is of 'Inventory' type.
    *   [ ] Create `InventoryMovement` ORM object with correct values.
    *   [ ] Call `InventoryMovementService.save` with the session.
    *   [ ] Ensure `line.id` for `reference_id` is correctly populated/available. (The invoice and its lines are flushed before JE creation in `post_purchase_invoice` for `SalesInvoiceManager`, a similar pattern might be needed or ensure lines are flushed when invoice is saved, even if as draft, to get IDs).
        *   *Correction*: `post_purchase_invoice` first fetches the `invoice_to_post` which implies it was already saved as draft, so `line.id` should be available.

**4.3 Modify `app/business_logic/sales_invoice_manager.py` - `post_invoice`**
*   **Plan**:
    1.  Inject `InventoryMovementService` and `ConfigurationService` into `__init__`.
    2.  Inside the `async with session:` block in `post_invoice`:
        *   After successfully creating and posting the main financial JE for Sales (AR, Revenue, GST Output) and before updating the SI status:
        *   Iterate through `invoice_to_post.lines`.
        *   If `line.product` exists and `ProductTypeEnum(line.product.product_type) == ProductTypeEnum.INVENTORY`:
            *   **Fetch Current WAC**:
                *   Query `business.inventory_summary` view: `SELECT average_cost FROM business.inventory_summary WHERE product_id = :pid`. Use `session.execute(text(...))` for this.
                *   If no summary or `average_cost` is null, use `line.product.purchase_price` (last purchase price) as a fallback WAC, or `Decimal(0)` if that's also null. Log this fallback.
            *   `cogs_amount_for_line = line.quantity * current_wac_fetched`.
            *   Create `InventoryMovement` ORM instance:
                *   `product_id = line.product_id`
                *   `movement_date = invoice_to_post.invoice_date`
                *   `movement_type = InventoryMovementTypeEnum.SALE.value`
                *   `quantity = -line.quantity` (negative)
                *   `unit_cost = current_wac_fetched`
                *   `total_cost = cogs_amount_for_line` (store as positive, represents value decrease)
                *   `reference_type = 'SalesInvoiceLine'`
                *   `reference_id = line.id`
                *   `created_by_user_id = user_id`
            *   Call `await self.inventory_movement_service.save(inv_movement_orm, session=session)`.
            *   **Create COGS Journal Entry**:
                *   Determine COGS account: `line.product.purchase_account_id` (common practice) or fallback to default 'SysAcc_DefaultCOGS' from `ConfigurationService`. Validate active.
                *   Determine Inventory Asset account: `line.product.inventory_account_id`. Validate active.
                *   Create `JournalEntryLineData` for Debit COGS, Credit Inventory Asset, amount = `cogs_amount_for_line`.
                *   Construct `JournalEntryData` DTO for this COGS JE (description like "COGS for Inv X, Product Y"). `source_type = 'SalesInvoiceCOGS'`, `source_id = invoice_to_post.id`.
                *   Call `self.app_core.journal_entry_manager.create_journal_entry(cogs_je_dto, session=session)`.
                *   Call `self.app_core.journal_entry_manager.post_journal_entry(created_cogs_je.id, user_id, session=session)`.
*   **Checklist**:
    *   [ ] Inject `InventoryMovementService` and `ConfigurationService`.
    *   [ ] In `post_invoice`, iterate through lines *after* main financial JE, *within* same transaction.
    *   [ ] Check if product is 'Inventory' type.
    *   [ ] Fetch current WAC from `inventory_summary` view or product's last purchase price.
    *   [ ] Create `InventoryMovement` ORM object with correct values (negative quantity).
    *   [ ] Call `InventoryMovementService.save`.
    *   [ ] Determine and validate COGS and Inventory Asset accounts.
    *   [ ] Create and Post COGS Journal Entry using `JournalEntryManager` (pass session).

**4.4 Update `ApplicationCore` (`app/core/application_core.py`)**
*   **Plan**:
    1.  Add import for `InventoryMovementService`.
    2.  Instantiate `InventoryMovementService` in `startup()`.
    3.  Add a property `inventory_movement_service` to access it.
*   **Checklist**:
    *   [ ] Import `InventoryMovementService`.
    *   [ ] Instantiate in `startup()`.
    *   [ ] Add property.

This plan addresses the inventory update requirements for both sales and purchases, focusing on using the Weighted Average Cost method by leveraging the `inventory_summary` view.
I will now proceed with generating the modified files.
</think>

Excellent! The application is stable and the previous step (Purchase Invoice Posting - Financial JE) was successful. We will now proceed with the next critical roadmap item: **Handling inventory updates upon posting for 'Inventory' type products.**

This involves:
1.  Creating a new `InventoryMovementService`.
2.  Modifying `PurchaseInvoiceManager.post_purchase_invoice` to record inventory inflows.
3.  Modifying `SalesInvoiceManager.post_invoice` to record inventory outflows and generate the corresponding Cost of Goods Sold (COGS) journal entry. We'll use the Weighted Average Cost (WAC) method, primarily deriving the cost from the `business.inventory_summary` view.

**Execution Plan: Implement Inventory Updates on Invoice Posting**

**I. Create/Update `app/services/__init__.py` (Define `IInventoryMovementRepository`)**
**II. Create `app/services/business_services.py` (Implement `InventoryMovementService`)**
**III. Update `app/core/application_core.py` (Instantiate and provide `InventoryMovementService`)**
**IV. Modify `app/business_logic/purchase_invoice_manager.py` (Add inventory movement on post)**
**V. Modify `app/business_logic/sales_invoice_manager.py` (Add inventory movement and COGS JE on post)**

Let's proceed with the file modifications.

---
**I. Update `app/services/__init__.py`**
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
from app.models.business.inventory_movement import InventoryMovement # New Import

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

# --- New Interface for Inventory Movement ---
class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement) -> InventoryMovement: pass
    # Add other specific methods if needed, e.g., get_movements_for_product, etc.

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService # Added InventoryMovementService
)

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "IInventoryMovementRepository", # New export
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
    "InventoryMovementService", # New export
]

```

---
**II. Update `app/services/business_services.py`**
```python
# app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession # Added for type hint in InventoryMovementService
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine 
from app.models.business.inventory_movement import InventoryMovement # New Import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository # Added IInventoryMovementRepository
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData 
)
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum 
from datetime import date 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

# ... (CustomerService, VendorService, ProductService, SalesInvoiceService, PurchaseInvoiceService remain unchanged from file set 5)
class CustomerService(ICustomerRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(selectinload(Customer.currency),selectinload(Customer.receivables_account),selectinload(Customer.created_by_user),selectinload(Customer.updated_by_user)).where(Customer.id == customer_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Customer.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Customer.customer_code.ilike(search_pattern), Customer.name.ilike(search_pattern), Customer.email.ilike(search_pattern) if Customer.email else False )) 
            stmt = select(Customer.id, Customer.customer_code, Customer.name, Customer.email, Customer.phone, Customer.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Customer.name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer); await session.flush(); await session.refresh(customer); return customer
    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        log_msg = f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")

class VendorService(IVendorRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(selectinload(Vendor.currency), selectinload(Vendor.payables_account),selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)).where(Vendor.id == vendor_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern) if Vendor.email else False))
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, vendor: Vendor) -> Vendor:
        async with self.db_manager.session() as session:
            session.add(vendor); await session.flush(); await session.refresh(vendor); return vendor
    async def add(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def update(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def delete(self, vendor_id: int) -> bool:
        log_msg = f"Hard delete attempted for Vendor ID {vendor_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")

class ProductService(IProductRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(selectinload(Product.sales_account),selectinload(Product.purchase_account),selectinload(Product.inventory_account),selectinload(Product.tax_code_obj),selectinload(Product.created_by_user),selectinload(Product.updated_by_user)).where(Product.id == product_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,product_type_filter: Optional[ProductTypeEnum] = None,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Product.is_active == True)
            if product_type_filter: conditions.append(Product.product_type == product_type_filter.value)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Product.product_code.ilike(search_pattern), Product.name.ilike(search_pattern), Product.description.ilike(search_pattern) if Product.description else False ))
            stmt = select(Product.id, Product.product_code, Product.name, Product.product_type, Product.sales_price, Product.purchase_price, Product.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Product.product_type, Product.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, product: Product) -> Product:
        async with self.db_manager.session() as session:
            session.add(product); await session.flush(); await session.refresh(product); return product
    async def add(self, entity: Product) -> Product: return await self.save(entity)
    async def update(self, entity: Product) -> Product: return await self.save(entity)
    async def delete(self, product_id: int) -> bool:
        log_msg = f"Hard delete attempted for Product/Service ID {product_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")

class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),
                selectinload(SalesInvoice.customer), selectinload(SalesInvoice.currency),
                selectinload(SalesInvoice.journal_entry), 
                selectinload(SalesInvoice.created_by_user), selectinload(SalesInvoice.updated_by_user)
            ).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None: conditions.append(SalesInvoice.customer_id == customer_id)
            if status: conditions.append(SalesInvoice.status == status.value)
            if start_date: conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date: conditions.append(SalesInvoice.invoice_date <= end_date)
            stmt = select( SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date,
                Customer.name.label("customer_name"), SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status
            ).join(Customer, SalesInvoice.customer_id == Customer.id) 
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [SalesInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines)).where(SalesInvoice.invoice_no == invoice_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def save(self, invoice: SalesInvoice) -> SalesInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: 
                await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def update(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        log_msg = f"Hard delete attempted for Sales Invoice ID {invoice_id}. Not implemented; use voiding/cancellation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")

class PurchaseInvoiceService(IPurchaseInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(
                selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product),
                selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj),
                selectinload(PurchaseInvoice.vendor), selectinload(PurchaseInvoice.currency),
                selectinload(PurchaseInvoice.journal_entry),
                selectinload(PurchaseInvoice.created_by_user), selectinload(PurchaseInvoice.updated_by_user)
            ).where(PurchaseInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, vendor_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50) -> List[PurchaseInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if vendor_id is not None: conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            if status: conditions.append(PurchaseInvoice.status == status.value)
            if start_date: conditions.append(PurchaseInvoice.invoice_date >= start_date)
            if end_date: conditions.append(PurchaseInvoice.invoice_date <= end_date)
            stmt = select( PurchaseInvoice.id, PurchaseInvoice.invoice_no, PurchaseInvoice.vendor_invoice_no, 
                PurchaseInvoice.invoice_date, Vendor.name.label("vendor_name"), 
                PurchaseInvoice.total_amount, PurchaseInvoice.status
            ).join(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PurchaseInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.invoice_no == internal_ref_no) 
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.vendor_id == vendor_id, PurchaseInvoice.vendor_invoice_no == vendor_invoice_no)
            result = await session.execute(stmt); return result.scalars().first() 
    async def save(self, invoice: PurchaseInvoice) -> PurchaseInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def update(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        async with self.db_manager.session() as session:
            pi = await session.get(PurchaseInvoice, invoice_id)
            if pi and pi.status == InvoiceStatusEnum.DRAFT.value: 
                await session.delete(pi); return True
            elif pi: self.logger.warning(f"Attempt to delete non-draft PI ID {invoice_id} with status {pi.status}. Denied."); raise ValueError(f"Cannot delete PI {pi.invoice_no} as its status is '{pi.status}'. Only Draft invoices can be deleted.")
        return False


# --- New Service for Inventory Movement ---
class InventoryMovementService(IInventoryMovementRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[InventoryMovement]:
        async with self.db_manager.session() as session:
            return await session.get(InventoryMovement, id_val)

    async def get_all(self) -> List[InventoryMovement]:
        async with self.db_manager.session() as session:
            stmt = select(InventoryMovement).order_by(InventoryMovement.movement_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession] = None) -> InventoryMovement:
        """Saves an InventoryMovement, optionally using a provided session."""
        if session:
