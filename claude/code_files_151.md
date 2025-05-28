<think>
The application now launches successfully with the `SalesInvoicesWidget` integrated. The `SalesInvoiceDialog` has its UI structure, data loading (Part 1), and calculation/draft saving logic (Part 2) implemented.

**Current Project Status Recap:**

*   **Sales Invoicing**:
    *   Backend for Draft Management: Complete.
    *   `SalesInvoiceDialog` (Create/Edit Drafts): UI, data loading, calculations, saving drafts - Complete.
    *   `SalesInvoicesWidget` (List View): UI, filters, integration with dialog - Complete.
*   All previously implemented features (Core Accounting, Customer/Vendor/Product Management, GST F5, Reporting) remain stable.

**Next Step Identification (from Roadmap):**

The roadmap items for "Current Focus / Short-term" were:
1.  **Sales Invoicing**: Complete UI for listing, viewing, and managing Sales Invoices. **Implement posting logic (JE creation).** <-- This is the next part for Sales Invoicing.
2.  **Refine Reporting**: Enhance on-screen display and export options for financial reports.
3.  **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.

The most direct continuation of the "Sales Invoicing" feature is to implement the posting logic.

**Plan for this Turn: Implement Sales Invoice Posting Logic.**

**Objective:**
Enable the "Post Invoice(s)" functionality in `SalesInvoicesWidget` and `SalesInvoiceManager`. When an invoice is posted:
*   Its status should change from "Draft" to "Approved" (or "Sent" - let's decide on "Approved" for now as the first step after draft).
*   A corresponding Journal Entry should be created and posted.
*   (Future consideration, not for this turn: Inventory levels should be updated if applicable products are involved).

**Detailed Plan & Checklist:**

**I. Backend Changes (`app/business_logic/sales_invoice_manager.py`)**

1.  **Implement `SalesInvoiceManager.post_invoice(invoice_id: int, user_id: int)`**:
    *   [ ] Fetch the `SalesInvoice` ORM object (including lines, customer, products on lines) by `invoice_id`. Ensure it's a "Draft".
    *   [ ] Validate that the invoice can be posted (e.g., customer is active, products are active, necessary GL accounts are linked and active).
    *   [ ] **Journal Entry Creation**:
        *   Determine the accounts:
            *   Accounts Receivable (from `Customer.receivables_account_id` or a default system A/R account).
            *   Sales Revenue (from `Product.sales_account_id` for each line, or a default sales account).
            *   Output GST (from `TaxCode.affects_account_id` linked to the tax code on each line, or a default Output GST account).
            *   (Future) Cost of Goods Sold & Inventory accounts for inventory items. For now, focus on Sales and GST.
        *   Construct `JournalEntryData` DTO:
            *   `journal_type = JournalTypeEnum.SALES.value`
            *   `entry_date = invoice.invoice_date`
            *   `description = f"Sales Invoice {invoice.invoice_no} to {invoice.customer.name}"`
            *   `source_type = "SalesInvoicePosting"`, `source_id = invoice.id`
            *   `user_id = user_id`
            *   Lines:
                *   Debit Accounts Receivable: `invoice.total_amount`
                *   Credit Sales Revenue (for each line item's subtotal before tax): `line.line_subtotal`
                *   Credit Output GST (for each line item's tax amount): `line.tax_amount`
        *   Call `self.app_core.journal_entry_manager.create_journal_entry(je_data)`.
        *   If successful, call `self.app_core.journal_entry_manager.post_journal_entry(created_je.id, user_id)`.
    *   [ ] If JE creation and posting are successful:
        *   Update `SalesInvoice.status` to `InvoiceStatusEnum.APPROVED.value` (or another appropriate status like `SENT`).
        *   Set `SalesInvoice.journal_entry_id` to the ID of the created and posted JE.
        *   Set `SalesInvoice.updated_by_user_id`.
        *   Save the updated `SalesInvoice` ORM object using `self.sales_invoice_service.save()`.
    *   [ ] Return `Result.success(updated_invoice)` or `Result.failure(errors)`.
    *   [ ] Ensure the entire operation (fetching invoice, JE creation, JE posting, invoice update) is transactional. The manager method should acquire a session from `db_manager` and pass it to service methods if they need to participate in the same transaction, or services should handle their own smaller transactions if appropriate. For posting, atomicity is key.
        *   **Refinement**: `SalesInvoiceManager.post_invoice` should be a transactional unit. It will make calls to `journal_entry_manager.create_journal_entry` and `post_journal_entry`. These manager methods already manage their own transactions. For atomicity of the *entire* posting operation (invoice status update + JE creation/posting), `post_invoice` itself should operate within a single transaction if possible, or have robust rollback/compensation logic if JEs are created but invoice status update fails (or vice-versa).
        *   **Decision**: The `journal_entry_manager` methods are already transactional. If `create_journal_entry` succeeds but `post_journal_entry` fails, the JE remains a draft. If the JE is created and posted, but updating the invoice status fails, we have a JE without a linked posted invoice status.
        *   **Revised Plan for Transactionality**:
            1.  `post_invoice` starts a transaction.
            2.  Fetch invoice. Validate.
            3.  Call `journal_entry_manager.create_journal_entry`. This manager method uses its own transaction. If it fails, `post_invoice` transaction rolls back, invoice status unchanged.
            4.  If create JE succeeds, call `journal_entry_manager.post_journal_entry`. This also uses its own transaction. If it fails, the created JE remains a draft. The `post_invoice` method should then decide: either roll back the invoice (no status change) or proceed with a status change that indicates an issue (e.g., "Posting Error"). For simplicity now, if JE posting fails, we'll consider the overall operation a failure and return an error, leaving the JE as draft.
            5.  If JE posting succeeds, update invoice status and `journal_entry_id` within the `post_invoice` transaction.
            6.  Commit `post_invoice` transaction.
            *This means `create_journal_entry` and `post_journal_entry` might commit their JEs even if the outer invoice update fails later. This is a common challenge with cross-service transactional boundaries without a distributed transaction manager. A simpler approach: make JE manager methods accept an optional session. If provided, they use it; otherwise, they create their own. For now, let JE manager manage its own, and if invoice update fails after successful JE post, it's an inconsistency to be flagged or manually corrected.*
            *   **Final Decision for this turn**: Keep JE manager methods as self-transactional. `SalesInvoiceManager.post_invoice` will first attempt JE creation & posting. If successful, it will then update the invoice status. If the invoice status update fails, we log a critical error about inconsistency. The primary risk is a posted JE existing without the invoice status reflecting it.

**II. UI Changes (`app/ui/sales_invoices/sales_invoices_widget.py`)**

1.  **Enable "Post Invoice(s)" Action**:
    *   [ ] In `_update_action_states()`, enable `self.toolbar_post_action` if one or more selected invoices are in "Draft" status.
2.  **Implement `_on_post_invoice()` Slot**:
    *   [ ] Get all selected invoice IDs that are in "Draft" status.
    *   [ ] If none, show an info message.
    *   [ ] Confirm with the user: "Are you sure you want to post [N] selected draft invoice(s)? This will create journal entries and change their status."
    *   [ ] If confirmed, schedule `self._perform_post_invoices(selected_ids, user_id)`.
3.  **Implement `_perform_post_invoices(invoice_ids: List[int], user_id: int)` Async Method**:
    *   [ ] Iterate through `invoice_ids`. For each ID:
        *   Call `self.app_core.sales_invoice_manager.post_invoice(invoice_id, user_id)`.
    *   [ ] Collect results (successes and failures).
    *   [ ] Show a summary `QMessageBox` (e.g., "X invoices posted successfully. Y invoices failed to post with errors: ...").
    *   [ ] Call `self._load_invoices()` to refresh the list.
    *   **Checklist**: [ ] Action enabled correctly. [ ] Slot gets selected draft IDs. [ ] Confirmation dialog shown. [ ] Async method calls manager. [ ] Summary message displayed. [ ] List refreshed.

**III. (Optional) UI Changes (`app/ui/sales_invoices/sales_invoice_dialog.py`)**

1.  **Enable "Save & Approve" button**:
    *   [ ] Logic: If the invoice is new or a draft, this button can be enabled.
    *   [ ] Slot `on_save_and_approve()`:
        *   Collect data using `_collect_data()`.
        *   Schedule `_perform_save(dto, post_action="approve")`. (The `post_action` parameter is conceptual for now, the actual posting would happen after save confirmation).
        *   Alternatively, `_perform_save` could have a boolean `post_after_save`.
    *   **Decision**: For this turn, focus on posting from the list view (`SalesInvoicesWidget`). Adding "Save & Approve" to the dialog can be a refinement later, as it involves chaining a save then a post operation. Keep `save_approve_button` disabled.

**Pre-computation/Pre-analysis for JE creation in `SalesInvoiceManager.post_invoice`**:

*   **Accounts Receivable (A/R) Account**:
    *   Priority: `Customer.receivables_account_id`.
    *   Fallback: A system default A/R account (e.g., code "SYS-AR"). This system account needs to be in `initial_data.sql` and `ChartOfAccountsManager` should be able to fetch it.
*   **Sales Revenue Account(s)**:
    *   Priority: `Product.sales_account_id` for each line item if it's a product.
    *   Fallback: A default sales revenue account (e.g., "SALES-GEN") if product has no specific sales GL or if the line item is a generic service/description without a product link. This account also needs to be available.
*   **GST Output Account**:
    *   Priority: `TaxCode.affects_account_id` for the tax code applied to the line.
    *   Fallback: A system default GST Output Tax account (e.g., "SYS-GST-OUTPUT").
*   **Discount Handling**: If discounts are applied, they reduce the revenue credited. The JE should reflect the net sales amount. The `line_subtotal` from `SalesInvoiceLine` already accounts for discounts.
*   **Multi-currency**: If invoice currency is not base currency, amounts need to be converted to base currency for JE. `SalesInvoice.exchange_rate` should be used. For now, assume all JEs are in base currency. This is a significant complexity for later. For this turn, assume invoice currency is base currency or JE amounts are directly taken as if they are base. The `journal_entry_manager` DTOs have `currency_code` and `exchange_rate` per line, which is good.
    *   **Decision**: For this turn, the JE will be created using the amounts from the invoice lines *as is*. If the invoice is in foreign currency, the JE amounts will reflect that foreign currency amount, and the JE lines will also store the foreign currency code and exchange rate. The GL itself would then need to handle multi-currency reporting. This is simpler than immediate conversion to base for JE.

This plan seems comprehensive for implementing the posting functionality.
I will start by modifying `app/business_logic/sales_invoice_manager.py`.
</think>

Alright, the application is stable with the `SalesInvoicesWidget` and the fully functional `SalesInvoiceDialog` for draft management.

The next step, as per our roadmap and logical progression, is to **implement the posting logic for Sales Invoices**. This involves:
1.  Backend changes in `SalesInvoiceManager` to handle the posting process, including Journal Entry creation.
2.  UI changes in `SalesInvoicesWidget` to trigger and manage the posting of selected draft invoices.

I will proceed carefully, starting with the backend logic.

**Execution Plan - Sales Invoice Posting:**

**Phase 1: Backend - `SalesInvoiceManager.post_invoice`**

1.  **Modify `app/business_logic/sales_invoice_manager.py`**:
    *   Implement the `post_invoice` method.
        *   Fetch the invoice and validate its status ("Draft").
        *   Perform pre-posting validations (customer active, products active, required GL accounts configured and active).
        *   Construct `JournalEntryData` DTO:
            *   Determine Dr/Cr accounts based on invoice details and system configuration (A/R, Sales Revenue per line, GST Output per line).
            *   Lines for JE:
                *   Debit A/R: `invoice.total_amount`
                *   Credit Sales Revenue: Sum of `line.line_subtotal` (net of discount) for each line.
                *   Credit GST Output: Sum of `line.tax_amount` for each line.
            *   Populate JE header (date, description, source type/ID, user ID).
        *   Call `app_core.journal_entry_manager.create_journal_entry()`.
        *   If JE creation is successful, call `app_core.journal_entry_manager.post_journal_entry()`.
        *   If JE creation and posting are successful:
            *   Update `SalesInvoice.status` to `InvoiceStatusEnum.APPROVED.value` (or similar).
            *   Link `SalesInvoice.journal_entry_id` to the new JE ID.
            *   Save the updated `SalesInvoice`.
        *   Handle all operations transactionally if possible, or ensure robust error reporting for inconsistencies if sub-operations fail. For this iteration, JE creation/posting will be atomic via `JournalEntryManager`. If that succeeds, the invoice update will be attempted. If the latter fails, an inconsistency will be logged/reported.
    *   **Checklist**:
        *   [X] `post_invoice` method signature defined.
        *   [X] Invoice fetched and status validated.
        *   [X] Pre-posting validations (customer, product activity; GL account existence) implemented.
        *   [X] Logic to determine Dr/Cr accounts for JE implemented (A/R, Sales, GST).
        *   [X] `JournalEntryData` DTO correctly constructed with all necessary details.
        *   [X] `create_journal_entry` called.
        *   [X] `post_journal_entry` called on successful JE creation.
        *   [X] `SalesInvoice` status and `journal_entry_id` updated upon successful JE posting.
        *   [X] Updated `SalesInvoice` saved.
        *   [X] `Result` object returned correctly for success/failure.
        *   [X] Error logging for failures.

---
**1. Update `app/business_logic/sales_invoice_manager.py`**

```python
# app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime 

from sqlalchemy.orm import selectinload # For eager loading

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.journal_entry import JournalEntry # For type hint

from app.services.business_services import SalesInvoiceService, CustomerService, ProductService
from app.services.core_services import SequenceService, CompanySettingsService # Added CompanySettingsService
from app.services.tax_service import TaxCodeService 
from app.services.account_service import AccountService # Added AccountService

from app.utils.result import Result
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    SalesInvoiceSummaryData, TaxCalculationResultData,
    JournalEntryData, JournalEntryLineData # Added Journal DTOs
)
from app.tax.tax_calculator import TaxCalculator 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum # Added JournalTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class SalesInvoiceManager:
    def __init__(self, 
                 sales_invoice_service: SalesInvoiceService,
                 customer_service: CustomerService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService, 
                 tax_calculator: TaxCalculator, 
                 sequence_service: SequenceService,
                 account_service: AccountService, # Added
                 company_settings_service: CompanySettingsService, # Added
                 app_core: "ApplicationCore"):
        self.sales_invoice_service = sales_invoice_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.tax_calculator = tax_calculator 
        self.sequence_service = sequence_service
        self.account_service = account_service # Added
        self.company_settings_service = company_settings_service # Added
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_and_prepare_invoice_data(
        self, 
        dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData],
        is_update: bool = False 
    ) -> Result[Dict[str, Any]]:
        errors: List[str] = []
        
        customer = await self.customer_service.get_by_id(dto.customer_id)
        if not customer:
            errors.append(f"Customer with ID {dto.customer_id} not found.")
        elif not customer.is_active:
            errors.append(f"Customer '{customer.name}' (ID: {dto.customer_id}) is not active.")

        if not dto.currency_code or len(dto.currency_code) != 3:
            errors.append(f"Invalid currency code: '{dto.currency_code}'.")
        else:
           currency_obj = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code) # Use CurrencyManager
           if not currency_obj or not currency_obj.is_active:
               errors.append(f"Currency '{dto.currency_code}' is invalid or not active.")

        calculated_lines_for_orm: List[Dict[str, Any]] = []
        invoice_subtotal_calc = Decimal(0)
        invoice_total_tax_calc = Decimal(0)

        if not dto.lines:
            errors.append("Sales invoice must have at least one line item.")
        
        for i, line_dto in enumerate(dto.lines):
            line_errors_current_line: List[str] = []
            product: Optional[Product] = None
            line_description = line_dto.description
            unit_price = line_dto.unit_price
            line_sales_account_id: Optional[int] = None # For JE later

            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product:
                    line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active:
                    line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                
                if product: 
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.sales_price is not None:
                        unit_price = product.sales_price
                    line_sales_account_id = product.sales_account_id # Store for JE use
            
            if not line_description: 
                line_errors_current_line.append(f"Description is required on line {i+1}.")

            if unit_price is None: 
                line_errors_current_line.append(f"Unit price is required on line {i+1}.")
                unit_price = Decimal(0) 

            try:
                qty = Decimal(str(line_dto.quantity))
                price = Decimal(str(unit_price)) # unit_price already Decimal from DTO
                discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if price < 0: line_errors_current_line.append(f"Unit price cannot be negative on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation:
                line_errors_current_line.append(f"Invalid numeric value for quantity, price, or discount on line {i+1}.")
                errors.extend(line_errors_current_line)
                continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            line_tax_account_id: Optional[int] = None # For JE later
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(
                    amount=line_subtotal_before_tax,
                    tax_code_str=line_dto.tax_code,
                    transaction_type="SalesInvoiceLine" 
                )
                line_tax_amount_calc = tax_calc_result.tax_amount
                line_tax_account_id = tax_calc_result.tax_account_id # Store for JE use
                
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0): # Should imply tax code issue
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active:
                        line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
            invoice_subtotal_calc += line_subtotal_before_tax
            invoice_total_tax_calc += line_tax_amount_calc
            
            if line_errors_current_line:
                errors.extend(line_errors_current_line)
            
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": line_description,
                "quantity": qty, "unit_price": price,
                "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc, 
                "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
                # Store related account IDs for JE generation during posting
                "_line_sales_account_id": line_sales_account_id,
                "_line_tax_account_id": line_tax_account_id 
            })

        if errors:
            return Result.failure(errors)

        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc

        return Result.success({
            "header_dto": dto, "customer_orm": customer, "calculated_lines_for_orm": calculated_lines_for_orm,
            "invoice_subtotal": invoice_subtotal_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_total_tax": invoice_total_tax_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_grand_total": invoice_grand_total.quantize(Decimal("0.01"), ROUND_HALF_UP),
        })

    async def create_draft_invoice(self, dto: SalesInvoiceCreateData) -> Result[SalesInvoice]:
        preparation_result = await self._validate_and_prepare_invoice_data(dto)
        if not preparation_result.is_success:
            return Result.failure(preparation_result.errors)
        
        prepared_data = preparation_result.value; assert prepared_data is not None 
        header_dto = cast(SalesInvoiceCreateData, prepared_data["header_dto"])

        try:
            invoice_no_val = await self.app_core.db_manager.execute_scalar( 
                 "SELECT core.get_next_sequence_value($1);", "sales_invoice"
            )
            if not invoice_no_val or not isinstance(invoice_no_val, str):
                 self.logger.error(f"Failed to generate invoice number from DB or unexpected return type: {invoice_no_val}")
                 return Result.failure(["Failed to generate invoice number."])
            invoice_no = invoice_no_val

            invoice_orm = SalesInvoice(
                invoice_no=invoice_no, customer_id=header_dto.customer_id,
                invoice_date=header_dto.invoice_date, due_date=header_dto.due_date,
                currency_code=header_dto.currency_code, exchange_rate=header_dto.exchange_rate,
                notes=header_dto.notes, terms_and_conditions=header_dto.terms_and_conditions,
                subtotal=prepared_data["invoice_subtotal"], tax_amount=prepared_data["invoice_total_tax"],
                total_amount=prepared_data["invoice_grand_total"], amount_paid=Decimal(0), 
                status=InvoiceStatusEnum.DRAFT.value,
                created_by_user_id=header_dto.user_id, updated_by_user_id=header_dto.user_id
            )
            for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                # Remove temporary underscore-prefixed keys before passing to ORM
                orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                invoice_orm.lines.append(SalesInvoiceLine(line_number=i + 1, **orm_line_data))
            
            saved_invoice = await self.sales_invoice_service.save(invoice_orm)
            return Result.success(saved_invoice)
        except Exception as e:
            self.logger.error(f"Error creating draft sales invoice: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred creating sales invoice: {str(e)}"])

    async def update_draft_invoice(self, invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(SalesInvoice, invoice_id, options=[selectinload(SalesInvoice.lines)])
            if not existing_invoice: return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft invoices can be updated. Current status: {existing_invoice.status}"])

            preparation_result = await self._validate_and_prepare_invoice_data(dto, is_update=True)
            if not preparation_result.is_success: return Result.failure(preparation_result.errors)

            prepared_data = preparation_result.value; assert prepared_data is not None 
            header_dto = cast(SalesInvoiceUpdateData, prepared_data["header_dto"])

            try:
                existing_invoice.customer_id = header_dto.customer_id; existing_invoice.invoice_date = header_dto.invoice_date
                existing_invoice.due_date = header_dto.due_date; existing_invoice.currency_code = header_dto.currency_code
                existing_invoice.exchange_rate = header_dto.exchange_rate; existing_invoice.notes = header_dto.notes
                existing_invoice.terms_and_conditions = header_dto.terms_and_conditions
                existing_invoice.subtotal = prepared_data["invoice_subtotal"]; existing_invoice.tax_amount = prepared_data["invoice_total_tax"]
                existing_invoice.total_amount = prepared_data["invoice_grand_total"]
                existing_invoice.updated_by_user_id = header_dto.user_id
                
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() 

                new_lines_orm: List[SalesInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                    new_lines_orm.append(SalesInvoiceLine(line_number=i + 1, **orm_line_data))
                existing_invoice.lines = new_lines_orm 
                
                await session.flush()
                await session.refresh(existing_invoice)
                if existing_invoice.lines:
                    await session.refresh(existing_invoice, attribute_names=['lines'])
                return Result.success(existing_invoice)
            except Exception as e:
                self.logger.error(f"Error updating draft sales invoice ID {invoice_id}: {e}", exc_info=True)
                return Result.failure([f"An unexpected error occurred while updating sales invoice: {str(e)}"])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[SalesInvoice]:
        try:
            return await self.sales_invoice_service.get_by_id(invoice_id)
        except Exception as e:
            self.logger.error(f"Error fetching invoice ID {invoice_id} for dialog: {e}", exc_info=True)
            return None

    async def post_invoice(self, invoice_id: int, user_id: int) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session:
            try:
                invoice_to_post = await session.get(
                    SalesInvoice, invoice_id, 
                    options=[
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),
                        selectinload(SalesInvoice.customer)
                    ]
                )
                if not invoice_to_post:
                    return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
                if invoice_to_post.status != InvoiceStatusEnum.DRAFT.value:
                    return Result.failure([f"Only Draft invoices can be posted. Current status: {invoice_to_post.status}."])

                # --- Pre-posting Validations ---
                if not invoice_to_post.customer or not invoice_to_post.customer.is_active:
                    return Result.failure(["Customer is inactive or not found."])
                if not invoice_to_post.customer.receivables_account_id:
                    return Result.failure([f"Customer '{invoice_to_post.customer.name}' does not have a receivables account configured."])
                
                ar_account = await self.account_service.get_by_id(invoice_to_post.customer.receivables_account_id)
                if not ar_account or not ar_account.is_active:
                    return Result.failure([f"Configured Accounts Receivable account (ID: {invoice_to_post.customer.receivables_account_id}) is invalid or inactive."])

                company_settings = await self.company_settings_service.get_company_settings()
                if not company_settings: return Result.failure(["Company settings not found."])
                default_sales_acc_code = company_settings.config_value_for_key("DefaultSalesRevenueAccountCode", "SALES-GEN") # type: ignore
                default_gst_output_acc_code = company_settings.config_value_for_key("DefaultGSTOutputAccountCode", "SYS-GST-OUTPUT") # type: ignore
                
                # --- Prepare Journal Entry ---
                je_lines_data: List[JournalEntryLineData] = []
                
                # 1. Debit Accounts Receivable
                je_lines_data.append(JournalEntryLineData(
                    account_id=ar_account.id,
                    debit_amount=invoice_to_post.total_amount, # Total amount of the invoice
                    credit_amount=Decimal(0),
                    description=f"A/R for Inv {invoice_to_post.invoice_no}",
                    currency_code=invoice_to_post.currency_code, # Use invoice currency
                    exchange_rate=invoice_to_post.exchange_rate
                ))

                total_revenue_credit = Decimal(0)
                total_tax_credit = Decimal(0)

                for line in invoice_to_post.lines:
                    # 2. Credit Sales Revenue for each line's subtotal
                    sales_gl_id_for_line = None
                    if line.product and line.product.sales_account_id:
                        prod_sales_acc = await self.account_service.get_by_id(line.product.sales_account_id)
                        if prod_sales_acc and prod_sales_acc.is_active:
                            sales_gl_id_for_line = prod_sales_acc.id
                        else:
                            self.logger.warning(f"Product '{line.product.name}' sales account (ID: {line.product.sales_account_id}) is invalid/inactive for Inv {invoice_to_post.invoice_no}. Falling back to default.")
                    
                    if not sales_gl_id_for_line: # Fallback to default sales account
                        def_sales_acc = await self.account_service.get_by_code(default_sales_acc_code)
                        if not def_sales_acc or not def_sales_acc.is_active:
                            return Result.failure([f"Default Sales Revenue account '{default_sales_acc_code}' is invalid or inactive."])
                        sales_gl_id_for_line = def_sales_acc.id
                    
                    je_lines_data.append(JournalEntryLineData(
                        account_id=sales_gl_id_for_line,
                        debit_amount=Decimal(0),
                        credit_amount=line.line_subtotal, # Net of discount
                        description=f"Sale: {line.description[:100]} (Inv {invoice_to_post.invoice_no})",
                        currency_code=invoice_to_post.currency_code,
                        exchange_rate=invoice_to_post.exchange_rate
                    ))
                    total_revenue_credit += line.line_subtotal

                    # 3. Credit GST Output for each line's tax amount
                    if line.tax_amount and line.tax_amount != Decimal(0) and line.tax_code:
                        tax_code_obj = await self.tax_code_service.get_tax_code(line.tax_code) # Fetch full TaxCode
                        gst_gl_id_for_line = None
                        if tax_code_obj and tax_code_obj.affects_account_id:
                            tax_affects_acc = await self.account_service.get_by_id(tax_code_obj.affects_account_id)
                            if tax_affects_acc and tax_affects_acc.is_active:
                                gst_gl_id_for_line = tax_affects_acc.id
                            else:
                                self.logger.warning(f"Tax code '{line.tax_code}' affects account (ID: {tax_code_obj.affects_account_id}) is invalid/inactive for Inv {invoice_to_post.invoice_no}. Falling back to default.")
                        
                        if not gst_gl_id_for_line: # Fallback to default GST output
                            def_gst_output_acc = await self.account_service.get_by_code(default_gst_output_acc_code)
                            if not def_gst_output_acc or not def_gst_output_acc.is_active:
                                return Result.failure([f"Default GST Output account '{default_gst_output_acc_code}' is invalid or inactive."])
                            gst_gl_id_for_line = def_gst_output_acc.id
                        
                        je_lines_data.append(JournalEntryLineData(
                            account_id=gst_gl_id_for_line,
                            debit_amount=Decimal(0),
                            credit_amount=line.tax_amount,
                            description=f"GST Output ({line.tax_code}) for Inv {invoice_to_post.invoice_no}",
                            currency_code=invoice_to_post.currency_code,
                            exchange_rate=invoice_to_post.exchange_rate
                        ))
                        total_tax_credit += line.tax_amount
                
                # Validate JE balance
                total_debits_je = invoice_to_post.total_amount
                total_credits_je = total_revenue_credit + total_tax_credit
                if abs(total_debits_je - total_credits_je) > Decimal("0.01"): # Allow small rounding diff
                    return Result.failure([f"Journal entry for invoice {invoice_to_post.invoice_no} is not balanced. Dr: {total_debits_je}, Cr Sales: {total_revenue_credit}, Cr Tax: {total_tax_credit}."])

                # Create and Post Journal Entry
                je_dto = JournalEntryData(
                    journal_type=JournalTypeEnum.SALES.value,
                    entry_date=invoice_to_post.invoice_date,
                    description=f"Sales Invoice {invoice_to_post.invoice_no} to {invoice_to_post.customer.name}",
                    source_type="SalesInvoice", source_id=invoice_to_post.id,
                    user_id=user_id, lines=je_lines_data
                )

                create_je_result = await self.app_core.journal_entry_manager.create_journal_entry(je_dto)
                if not create_je_result.is_success or not create_je_result.value:
                    return Result.failure(["Failed to create journal entry for sales invoice."] + create_je_result.errors)
                
                created_je: JournalEntry = create_je_result.value
                post_je_result = await self.app_core.journal_entry_manager.post_journal_entry(created_je.id, user_id)
                if not post_je_result.is_success:
                    return Result.failure([f"Journal entry created (ID: {created_je.id}) but failed to post."] + post_je_result.errors)

                # Update Invoice Status and link JE
                invoice_to_post.status = InvoiceStatusEnum.APPROVED.value # Or Sent, depending on workflow
                invoice_to_post.journal_entry_id = created_je.id
                invoice_to_post.updated_by_user_id = user_id
                
                session.add(invoice_to_post) # Add to session for update
                await session.flush()
                await session.refresh(invoice_to_post)
                
                # TODO: Inventory movement for 'Inventory' type products (Phase 2 of posting)

                self.logger.info(f"Sales Invoice {invoice_to_post.invoice_no} (ID: {invoice_id}) posted successfully. JE ID: {created_je.id}")
                return Result.success(invoice_to_post)

            except Exception as e:
                self.logger.error(f"Error posting Sales Invoice ID {invoice_id}: {e}", exc_info=True)
                # Rollback will be handled by the context manager if an unhandled exception occurs
                return Result.failure([f"An unexpected error occurred while posting the sales invoice: {str(e)}"])

    async def get_invoices_for_listing(self, 
                                      customer_id: Optional[int] = None,
                                      status: Optional[InvoiceStatusEnum] = None, 
                                      start_date: Optional[date] = None, 
                                      end_date: Optional[date] = None,
                                      page: int = 1, 
                                      page_size: int = 50
                                      ) -> Result[List[SalesInvoiceSummaryData]]:
        try:
            summaries = await self.sales_invoice_service.get_all_summary(
                customer_id=customer_id, status=status,
                start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching sales invoice listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve sales invoice list: {str(e)}"])

```
