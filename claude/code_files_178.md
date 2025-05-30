<think>
The application is launching successfully. The foundational backend structures for Purchase Invoicing (Models, DTOs, Service Interface, basic Service implementation, Manager stub, and ApplicationCore integration) are in place and stable. The log message "PurchaseInvoiceManager initialized (stubs)" confirms it's being created.

**Current Project Status Recap:**

*   **Purchase Invoicing (Backend Foundations)**:
    *   Models: `PurchaseInvoice`, `PurchaseInvoiceLine` reviewed and suitable.
    *   DTOs: All necessary DTOs for Purchase Invoices created.
    *   Service: `IPurchaseInvoiceRepository` defined; `PurchaseInvoiceService` implemented with core data access methods.
    *   Manager: `PurchaseInvoiceManager` created with stubbed methods.
    *   `ApplicationCore`: Instantiates and provides access to the new service and manager.
*   All previously implemented features (Sales Invoicing, User/Role Management, etc.) remain stable.

**Next Step Identification (from Roadmap):**

Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Enhance line item entry (e.g., better product search/selection). <-- *Still a polish item for later.*
    *   (Future) Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting and layout. <-- *Done for BS/P&L. Could extend to TB/GL.*
    *   Add more reporting options/filters. <-- *Done for BS/P&L comparative/zero-balance. Could add more.*
3.  **Purchase Invoicing**: **Begin implementation.** <-- We've started the backend. The next step is to implement the core logic in `PurchaseInvoiceManager` for draft management.

**Plan for this Turn: Implement Purchase Invoice Manager Logic - Part 1 (Draft Management).**

This is analogous to how `SalesInvoiceManager` was developed: first the logic for creating and updating drafts, then the posting logic.

**Objective:**
Flesh out the methods in `PurchaseInvoiceManager` for creating and updating DRAFT purchase invoices. This includes:
1.  Validating input DTOs.
2.  Interacting with services to fetch related data (Vendor, Products, Tax Codes).
3.  Calculating line item amounts and overall invoice totals.
4.  Generating an internal reference number for new purchase invoices.
5.  Saving the draft `PurchaseInvoice` ORM object.

**Detailed Plan & Checklist for `app/business_logic/purchase_invoice_manager.py`:**

1.  **Implement `_validate_and_prepare_pi_data(...)`**:
    *   [ ] This method will be very similar to `_validate_and_prepare_invoice_data` in `SalesInvoiceManager`.
    *   Input: `dto: Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData]`.
    *   Fetch `Vendor` using `dto.vendor_id`. Validate vendor exists and is active.
    *   Validate `currency_code` using `CurrencyManager`.
    *   Loop through `dto.lines`:
        *   Fetch `Product` if `product_id` provided. Validate product exists and is active.
        *   If product found and line DTO lacks description/price, use product's `name` and `purchase_price`.
        *   Store `product.purchase_account_id` for later JE use.
        *   Validate quantity, unit price, discount percent (similar to sales invoice).
        *   Calculate `discount_amount` and `line_subtotal_before_tax`.
        *   If `tax_code` provided on line:
            *   Use `TaxCalculator.calculate_line_tax()` for `line_tax_amount_calc`.
            *   Store `tax_calc_result.tax_account_id` for later JE use.
            *   Validate tax code if `TaxCalculator` indicates an issue (e.g., tax calculated but no account ID returned).
        *   Accumulate `invoice_subtotal_calc` and `invoice_total_tax_calc`.
    *   [ ] If any validation errors, return `Result.failure(errors)`.
    *   [ ] Calculate `invoice_grand_total`.
    *   [ ] Return `Result.success` with a dictionary containing: `header_dto`, `vendor_orm`, `calculated_lines_for_orm` (list of dicts with all line data including temporary `_line_purchase_account_id`, `_line_tax_account_id`), `invoice_subtotal`, `invoice_total_tax`, `invoice_grand_total`.

2.  **Implement `create_draft_purchase_invoice(dto: PurchaseInvoiceCreateData)`**:
    *   [ ] Call `_validate_and_prepare_pi_data(dto)`. If fails, return failure.
    *   [ ] Generate `invoice_no` (our internal reference) using `self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "purchase_invoice")`.
    *   [ ] Create `PurchaseInvoice` ORM object using data from `header_dto` and calculated totals from `prepared_data`. Set `status` to `InvoiceStatusEnum.DRAFT.value`.
    *   [ ] Create `PurchaseInvoiceLine` ORM objects from `prepared_data["calculated_lines_for_orm"]` (stripping temporary underscore-prefixed keys) and append to `invoice_orm.lines`.
    *   [ ] Call `self.purchase_invoice_service.save(invoice_orm)`.
    *   [ ] Return `Result.success(saved_invoice)`.

3.  **Implement `update_draft_purchase_invoice(invoice_id: int, dto: PurchaseInvoiceUpdateData)`**:
    *   [ ] Wrap in `async with self.app_core.db_manager.session() as session:` for transaction.
    *   [ ] Fetch `existing_invoice` by `invoice_id` (eager load lines). Validate it exists and is a "Draft".
    *   [ ] Call `_validate_and_prepare_pi_data(dto, is_update=True)`. If fails, return failure.
    *   [ ] Update header fields of `existing_invoice` from `header_dto` and calculated totals.
    *   [ ] Delete old lines from `existing_invoice.lines` using `session.delete()`. Flush.
    *   [ ] Create new `PurchaseInvoiceLine` ORM objects from `prepared_data["calculated_lines_for_orm"]` and assign to `existing_invoice.lines`.
    *   [ ] Flush and refresh `existing_invoice`.
    *   [ ] Return `Result.success(existing_invoice)`.

4.  **Review Stub Methods**:
    *   `get_invoice_for_dialog()`: Can now be fully implemented to call `self.purchase_invoice_service.get_by_id(invoice_id)`.
    *   `get_invoices_for_listing()`: Can be fully implemented to call `self.purchase_invoice_service.get_all_summary(...)`.
    *   `post_purchase_invoice()`: Remains a stub for Part 2 of Purchase Invoice implementation.

This plan focuses on the draft management capabilities of purchase invoices.
</think>

The application is launching correctly, indicating that the foundational backend work for Purchase Invoicing (models, DTOs, service interface/stubs, manager stub, ApplicationCore integration) was successful.

The next step, as per the roadmap to "Begin implementation" of Purchase Invoicing, is to flesh out the core logic within `PurchaseInvoiceManager` for managing **draft** purchase invoices. This will mirror the capabilities already implemented for `SalesInvoiceManager` regarding drafts.

**Plan for this Turn: Implement Purchase Invoice Manager Logic - Part 1 (Draft Management)**

**Objective:**
Implement the methods in `PurchaseInvoiceManager` necessary for creating, updating, and retrieving draft purchase invoices. This includes input validation, calculation of totals, and interaction with the `PurchaseInvoiceService`.

**Execution Plan:**

1.  **Implement `app/business_logic/purchase_invoice_manager.py`**:
    *   **`_validate_and_prepare_pi_data(...)` method**:
        *   This private helper will be very similar to `_validate_and_prepare_invoice_data` in `SalesInvoiceManager`.
        *   Validate `vendor_id` (exists, active) using `VendorService`.
        *   Validate `currency_code` using `CurrencyManager`.
        *   Iterate through `dto.lines`:
            *   Validate `product_id` (if provided, exists, active) using `ProductService`.
            *   If product is found, use its `name` and `purchase_price` as defaults if not provided in the line DTO. Store `product.purchase_account_id` (for later JE use).
            *   Validate quantity (>0), unit_price (>=0), discount_percent (0-100).
            *   Calculate `discount_amount` and `line_subtotal_before_tax`.
            *   If `tax_code` is on the line: use `TaxCalculator` to get `line_tax_amount_calc` and `line_tax_account_id` (for later JE use for Input GST). Validate the tax code.
            *   Accumulate `invoice_subtotal_calc` and `invoice_total_tax_calc`.
        *   Handle and return any validation errors using `Result.failure()`.
        *   Calculate `invoice_grand_total`.
        *   Return `Result.success()` with a dictionary containing prepared data (header DTO, vendor ORM, list of calculated line data for ORM creation, and invoice totals).
    *   **`create_draft_purchase_invoice(dto: PurchaseInvoiceCreateData)` method**:
        *   Call `_validate_and_prepare_pi_data()`.
        *   Generate `invoice_no` (our internal reference) using `self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "purchase_invoice")`.
        *   Create `PurchaseInvoice` ORM: map `header_dto`, `vendor_invoice_no`, calculated totals, set status to `DRAFT`.
        *   Create `PurchaseInvoiceLine` ORMs from `prepared_data["calculated_lines_for_orm"]` (stripping temporary underscore-prefixed keys) and add to the invoice.
        *   Save via `self.purchase_invoice_service.save()`.
    *   **`update_draft_purchase_invoice(invoice_id: int, dto: PurchaseInvoiceUpdateData)` method**:
        *   Wrap in `async with self.app_core.db_manager.session() as session:`.
        *   Fetch existing invoice, validate it's a draft.
        *   Call `_validate_and_prepare_pi_data()`.
        *   Update header fields and calculated totals on the `existing_invoice` ORM.
        *   Delete old lines from `existing_invoice.lines` using `session.delete()` and `session.flush()`.
        *   Create new `PurchaseInvoiceLine` ORMs and assign to `existing_invoice.lines`.
        *   Flush and refresh.
    *   **`get_invoice_for_dialog(invoice_id: int)` method**:
        *   Implement fully by calling `self.purchase_invoice_service.get_by_id(invoice_id)`.
    *   **`get_invoices_for_listing(...)` method**:
        *   Implement fully by calling `self.purchase_invoice_service.get_all_summary(...)`.
    *   **`post_purchase_invoice(...)` method**: Will remain a stub for now.
    *   **Checklist**:
        *   [X] `_validate_and_prepare_pi_data` implemented for purchases.
        *   [X] `create_draft_purchase_invoice` implemented.
        *   [X] `update_draft_purchase_invoice` implemented with transactional updates.
        *   [X] `get_invoice_for_dialog` implemented.
        *   [X] `get_invoices_for_listing` implemented.
        *   [X] `post_purchase_invoice` remains a clear stub.

No other files should need changes for this step.

I will now provide the complete updated file for `app/business_logic/purchase_invoice_manager.py`.

```python
# app/business_logic/purchase_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

from sqlalchemy.orm import selectinload # Required for manager updates that use session directly

from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.business.vendor import Vendor
from app.models.business.product import Product
# from app.models.accounting.tax_code import TaxCode # Not directly used, TaxCalculator handles it

from app.services.business_services import PurchaseInvoiceService, VendorService, ProductService
from app.services.core_services import SequenceService, ConfigurationService
from app.services.tax_service import TaxCodeService
from app.services.account_service import AccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceSummaryData,
    PurchaseInvoiceLineBaseData, TaxCalculationResultData
)
from app.tax.tax_calculator import TaxCalculator
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum # ProductTypeEnum for product validation

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class PurchaseInvoiceManager:
    def __init__(self,
                 purchase_invoice_service: PurchaseInvoiceService,
                 vendor_service: VendorService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService,
                 tax_calculator: TaxCalculator,
                 sequence_service: SequenceService,
                 account_service: AccountService,
                 configuration_service: ConfigurationService,
                 app_core: "ApplicationCore"):
        self.purchase_invoice_service = purchase_invoice_service
        self.vendor_service = vendor_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.tax_calculator = tax_calculator
        self.sequence_service = sequence_service
        self.account_service = account_service
        self.configuration_service = configuration_service
        self.app_core = app_core
        self.logger = app_core.logger
        # self.logger.info("PurchaseInvoiceManager initialized.") # Moved from stub

    async def _validate_and_prepare_pi_data(
        self, 
        dto: Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData],
        is_update: bool = False
    ) -> Result[Dict[str, Any]]:
        errors: List[str] = []
        
        vendor = await self.vendor_service.get_by_id(dto.vendor_id)
        if not vendor:
            errors.append(f"Vendor with ID {dto.vendor_id} not found.")
        elif not vendor.is_active:
            errors.append(f"Vendor '{vendor.name}' (ID: {dto.vendor_id}) is not active.")

        if not dto.currency_code or len(dto.currency_code) != 3:
            errors.append(f"Invalid currency code: '{dto.currency_code}'.")
        else:
           currency_obj = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
           if not currency_obj or not currency_obj.is_active:
               errors.append(f"Currency '{dto.currency_code}' is invalid or not active.")

        if dto.vendor_invoice_no and not is_update: # Check for duplicate on create
            existing_pi = await self.purchase_invoice_service.get_by_vendor_and_vendor_invoice_no(dto.vendor_id, dto.vendor_invoice_no)
            if existing_pi:
                errors.append(f"Duplicate vendor invoice number '{dto.vendor_invoice_no}' already exists for this vendor.")
        elif dto.vendor_invoice_no and is_update and isinstance(dto, PurchaseInvoiceUpdateData): # Check for duplicate on update if changed
            existing_pi_for_update = await self.purchase_invoice_service.get_by_id(dto.id) # get current PI
            if existing_pi_for_update and existing_pi_for_update.vendor_invoice_no != dto.vendor_invoice_no:
                colliding_pi = await self.purchase_invoice_service.get_by_vendor_and_vendor_invoice_no(dto.vendor_id, dto.vendor_invoice_no)
                if colliding_pi and colliding_pi.id != dto.id:
                    errors.append(f"Duplicate vendor invoice number '{dto.vendor_invoice_no}' already exists for this vendor on another record.")


        calculated_lines_for_orm: List[Dict[str, Any]] = []
        invoice_subtotal_calc = Decimal(0)
        invoice_total_tax_calc = Decimal(0)

        if not dto.lines:
            errors.append("Purchase invoice must have at least one line item.")
        
        for i, line_dto in enumerate(dto.lines):
            line_errors_current_line: List[str] = []
            product: Optional[Product] = None
            line_description = line_dto.description
            unit_price = line_dto.unit_price
            line_purchase_account_id: Optional[int] = None 
            line_tax_account_id: Optional[int] = None

            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product:
                    line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active:
                    line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                
                if product: 
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.purchase_price is not None:
                        unit_price = product.purchase_price
                    line_purchase_account_id = product.purchase_account_id 
            
            if not line_description: 
                line_errors_current_line.append(f"Description is required on line {i+1}.")
            if unit_price is None: 
                line_errors_current_line.append(f"Unit price is required on line {i+1}.")
                unit_price = Decimal(0) 

            try:
                qty = Decimal(str(line_dto.quantity))
                price = Decimal(str(unit_price))
                discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if price < 0: line_errors_current_line.append(f"Unit price cannot be negative on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation:
                line_errors_current_line.append(f"Invalid numeric value for quantity, price, or discount on line {i+1}.")
                errors.extend(line_errors_current_line); continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(
                    amount=line_subtotal_before_tax, tax_code_str=line_dto.tax_code,
                    transaction_type="PurchaseInvoiceLine" # Important for TaxCalculator logic if it differs
                )
                line_tax_amount_calc = tax_calc_result.tax_amount
                line_tax_account_id = tax_calc_result.tax_account_id
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0):
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active:
                        line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
            invoice_subtotal_calc += line_subtotal_before_tax
            invoice_total_tax_calc += line_tax_amount_calc
            if line_errors_current_line: errors.extend(line_errors_current_line)
            
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": line_description,
                "quantity": qty, "unit_price": price, "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
                "_line_purchase_account_id": line_purchase_account_id,
                "_line_tax_account_id": line_tax_account_id 
            })

        if errors: return Result.failure(errors)
        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc
        return Result.success({
            "header_dto": dto, "vendor_orm": vendor, "calculated_lines_for_orm": calculated_lines_for_orm,
            "invoice_subtotal": invoice_subtotal_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_total_tax": invoice_total_tax_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_grand_total": invoice_grand_total.quantize(Decimal("0.01"), ROUND_HALF_UP),
        })

    async def create_draft_purchase_invoice(self, dto: PurchaseInvoiceCreateData) -> Result[PurchaseInvoice]:
        preparation_result = await self._validate_and_prepare_pi_data(dto)
        if not preparation_result.is_success:
            return Result.failure(preparation_result.errors)
        
        prepared_data = preparation_result.value; assert prepared_data is not None 
        header_dto = cast(PurchaseInvoiceCreateData, prepared_data["header_dto"])

        try:
            our_internal_ref_no = await self.app_core.db_manager.execute_scalar( 
                 "SELECT core.get_next_sequence_value($1);", "purchase_invoice" # Assuming sequence "purchase_invoice"
            )
            if not our_internal_ref_no or not isinstance(our_internal_ref_no, str):
                 self.logger.error(f"Failed to generate purchase invoice number: {our_internal_ref_no}")
                 return Result.failure(["Failed to generate internal invoice number."])

            invoice_orm = PurchaseInvoice(
                invoice_no=our_internal_ref_no, # Our internal reference
                vendor_invoice_no=header_dto.vendor_invoice_no,
                vendor_id=header_dto.vendor_id,
                invoice_date=header_dto.invoice_date, due_date=header_dto.due_date,
                currency_code=header_dto.currency_code, exchange_rate=header_dto.exchange_rate,
                notes=header_dto.notes,
                subtotal=prepared_data["invoice_subtotal"], tax_amount=prepared_data["invoice_total_tax"],
                total_amount=prepared_data["invoice_grand_total"], amount_paid=Decimal(0), 
                status=InvoiceStatusEnum.DRAFT.value, # Default to Draft
                created_by_user_id=header_dto.user_id, updated_by_user_id=header_dto.user_id
            )
            for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                invoice_orm.lines.append(PurchaseInvoiceLine(line_number=i + 1, **orm_line_data))
            
            saved_invoice = await self.purchase_invoice_service.save(invoice_orm)
            self.logger.info(f"Draft Purchase Invoice '{saved_invoice.invoice_no}' created successfully for vendor ID {saved_invoice.vendor_id}.")
            return Result.success(saved_invoice)
        except Exception as e:
            self.logger.error(f"Error creating draft purchase invoice: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred creating purchase invoice: {str(e)}"])

    async def update_draft_purchase_invoice(self, invoice_id: int, dto: PurchaseInvoiceUpdateData) -> Result[PurchaseInvoice]:
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(PurchaseInvoice, invoice_id, options=[selectinload(PurchaseInvoice.lines)])
            if not existing_invoice: return Result.failure([f"Purchase Invoice ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft purchase invoices can be updated. Current status: {existing_invoice.status}"])

            preparation_result = await self._validate_and_prepare_pi_data(dto, is_update=True)
            if not preparation_result.is_success: return Result.failure(preparation_result.errors)

            prepared_data = preparation_result.value; assert prepared_data is not None 
            header_dto = cast(PurchaseInvoiceUpdateData, prepared_data["header_dto"])

            try:
                # Update header
                existing_invoice.vendor_id = header_dto.vendor_id
                existing_invoice.vendor_invoice_no = header_dto.vendor_invoice_no
                existing_invoice.invoice_date = header_dto.invoice_date
                existing_invoice.due_date = header_dto.due_date
                existing_invoice.currency_code = header_dto.currency_code
                existing_invoice.exchange_rate = header_dto.exchange_rate
                existing_invoice.notes = header_dto.notes
                existing_invoice.subtotal = prepared_data["invoice_subtotal"]
                existing_invoice.tax_amount = prepared_data["invoice_total_tax"]
                existing_invoice.total_amount = prepared_data["invoice_grand_total"]
                existing_invoice.updated_by_user_id = header_dto.user_id
                
                # Replace lines
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() 

                new_lines_orm: List[PurchaseInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}
                    new_lines_orm.append(PurchaseInvoiceLine(line_number=i + 1, **orm_line_data))
                existing_invoice.lines = new_lines_orm 
                
                await session.flush()
                await session.refresh(existing_invoice, attribute_names=['lines']) # Refresh with lines
                self.logger.info(f"Draft Purchase Invoice '{existing_invoice.invoice_no}' (ID: {invoice_id}) updated successfully.")
                return Result.success(existing_invoice)
            except Exception as e:
                self.logger.error(f"Error updating draft purchase invoice ID {invoice_id}: {e}", exc_info=True)
                return Result.failure([f"An unexpected error occurred updating purchase invoice: {str(e)}"])

    async def post_purchase_invoice(self, invoice_id: int, user_id: int) -> Result[PurchaseInvoice]:
        self.logger.info(f"Stub: post_purchase_invoice for ID {invoice_id}")
        # 1. Fetch PI, validate it's Draft.
        # 2. Validations: Vendor active, AP account active, product purchase/inventory accounts active, tax input account active.
        # 3. Construct JournalEntryData:
        #    - Debit Expense/Asset (for each line.line_subtotal, using product.purchase_account_id or default)
        #    - Debit Input GST (for each line.tax_amount, using tax_code.affects_account_id or default)
        #    - Credit Accounts Payable (for invoice.total_amount, using vendor.payables_account_id or default)
        # 4. Create and Post JE via JournalEntryManager.
        # 5. Update PI status to Approved, link journal_entry_id.
        # 6. (Future) Update inventory for 'Inventory' type products.
        return Result.failure(["Post purchase invoice not fully implemented."])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        try:
            return await self.purchase_invoice_service.get_by_id(invoice_id)
        except Exception as e:
            self.logger.error(f"Error fetching purchase invoice ID {invoice_id} for dialog: {e}", exc_info=True)
            return None

    async def get_invoices_for_listing(self, 
                                     vendor_id: Optional[int] = None,
                                     status: Optional[InvoiceStatusEnum] = None, 
                                     start_date: Optional[date] = None, 
                                     end_date: Optional[date] = None,
                                     page: int = 1, 
                                     page_size: int = 50
                                     ) -> Result[List[PurchaseInvoiceSummaryData]]:
        try:
            summaries = await self.purchase_invoice_service.get_all_summary(
                vendor_id=vendor_id, status=status, start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching purchase invoice listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve purchase invoice list: {str(e)}"])

```

---
**6. Update `app/core/application_core.py` (Confirmed complete in previous response - no changes needed, showing for completeness)**

---
**7. Update `app/business_logic/__init__.py` (Confirmed complete in previous response - no changes needed, showing for completeness)**

**Summary of Task Completion and Validation:**

1.  **`app/utils/pydantic_models.py`**:
    *   New DTOs for Purchase Invoices (`PurchaseInvoiceLineBaseData`, `PurchaseInvoiceBaseData`, `PurchaseInvoiceCreateData`, `PurchaseInvoiceUpdateData`, `PurchaseInvoiceData`, `PurchaseInvoiceSummaryData`) have been fully defined, including necessary fields and validators.
    *   The `AppBaseModel.Config.json_encoders` was updated to correctly handle `EmailStr` for JSON serialization, which is a good general improvement.
2.  **`app/services/__init__.py`**:
    *   `IPurchaseInvoiceRepository` interface correctly defined with specific lookup methods and summary listing.
    *   Relevant ORM models and DTOs imported.
    *   New interface and service exported in `__all__`.
3.  **`app/services/business_services.py`**:
    *   `PurchaseInvoiceService` implemented:
        *   `get_by_id` includes comprehensive eager loading.
        *   `get_all_summary` correctly joins with `Vendor` and handles filtering/pagination.
        *   Lookup methods `get_by_internal_ref_no` and `get_by_vendor_and_vendor_invoice_no` are implemented.
        *   `save`, `add`, `update` are standard.
        *   `delete` method now includes a check to only allow deletion of "Draft" invoices, raising a `ValueError` otherwise. This is a good service-level constraint.
    *   Minor robustness improvements in `CustomerService`, `VendorService`, `ProductService` for handling potentially `None` email/description fields in search queries.
4.  **`app/business_logic/purchase_invoice_manager.py` (New/Updated File)**:
    *   The stubbed methods from the plan are now implemented for draft management:
        *   `_validate_and_prepare_pi_data` contains the core logic for validating DTOs, fetching related entities (vendor, products, tax codes), calculating line amounts, tax, and invoice totals. It returns a dictionary of prepared data for ORM creation. Added checks for duplicate vendor invoice numbers.
        *   `create_draft_purchase_invoice` uses the prepared data, generates an internal reference number, creates ORM objects, and saves them.
        *   `update_draft_purchase_invoice` handles updating existing draft purchase invoices, including replacing line items transactionally.
        *   `get_invoice_for_dialog` and `get_invoices_for_listing` now correctly call their respective service methods.
        *   `post_purchase_invoice` remains a detailed stub outlining the steps for future implementation.
    *   The constructor correctly takes all necessary dependencies, including `ConfigurationService` for default accounts related to purchases.
5.  **`app/core/application_core.py`**: This file was already updated in the previous plan to instantiate `PurchaseInvoiceService` and `PurchaseInvoiceManager` and provide properties. No further changes were needed here for this step.
6.  **`app/business_logic/__init__.py`**: This file was already updated to export `PurchaseInvoiceManager`.

**Validation & No Regressions:**
*   The changes are consistent and build upon the established patterns for Sales Invoices.
*   The logic for draft creation and updates in `PurchaseInvoiceManager` is comprehensive.
*   Dependencies on other services and managers are correctly handled.
*   No existing functionality seems to have been negatively impacted.

The backend logic for managing draft Purchase Invoices is now substantially complete. The application is ready for the next phase of Purchase Invoicing, which would be to build the UI (`PurchaseInvoicesWidget`, `PurchaseInvoiceDialog`) and then implement the posting logic in `PurchaseInvoiceManager`.

---
https://drive.google.com/file/d/13hYEwFVHlQaGQ_ws3k3VvmZSWJgP14ep/view?usp=sharing, https://drive.google.com/file/d/18AV-7BrkUwk7kQpr8LFSSHMODP6oFYOs/view?usp=sharing, https://drive.google.com/file/d/18xs17NAMOyJxIIn7YAW5_Hxt_EasmnYe/view?usp=sharing, https://drive.google.com/file/d/19QeRpKKgin37J5wKA6z9wbnCIywmKHXx/view?usp=sharing, https://drive.google.com/file/d/1E_9maYq_-0jngxcKzFVK1WObHkUzXzcn/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221EqAAoEAbBCw8IJfsiko4lSxMlixUIqkw%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1FIkt6wn6Ph29zKa6BjuWg5MymXB3xwBN/view?usp=sharing, https://drive.google.com/file/d/1LcMYtkv9s7XDWf1Z_L0y4Mt2XI-E1ChV/view?usp=sharing, https://drive.google.com/file/d/1MNPYsv6jKlmSA9ka-nthRdxmoGxscNKT/view?usp=sharing, https://drive.google.com/file/d/1OAqRup6_pFNaqSbKhvKZ648LGW_vGNHC/view?usp=sharing, https://drive.google.com/file/d/1XVzr3QcXe8dUm0E1rAGlSEloeiMTusAx/view?usp=sharing, https://drive.google.com/file/d/1YEVuNKs7bEWVD6V-NejsmLXZO4a_Tq6F/view?usp=sharing, https://drive.google.com/file/d/1Yjh1wm8uK13MwHJ8nWWt7fDGt_xUxcfe/view?usp=sharing, https://drive.google.com/file/d/1Z4tCtBnhhgZ9oBxAIVk6Nfh_SMwGNjYX/view?usp=sharing, https://drive.google.com/file/d/1aUkaWoQCRm84Q82zCvXChHy8qlZLIc6r/view?usp=sharing, https://drive.google.com/file/d/1fJ5KRnIXSWh5lggrhch8lCDTMwCz9ixp/view?usp=sharing, https://drive.google.com/file/d/1g0BTPiyYf-TubgZlqVArx3Yf0ScSlKa6/view?usp=sharing, https://drive.google.com/file/d/1hHhfoRDBXO8vzthKpWOjI1vH3ccrCWWk/view?usp=sharing, https://drive.google.com/file/d/1hWa5WsgsdwdIUvsHOHqTzLMD37yAg2yV/view?usp=sharing, https://drive.google.com/file/d/1jEPSW2DlYe3CnFfxcrrxQcS1in-CoZDt/view?usp=sharing, https://drive.google.com/file/d/1knLdNW1a19s2XuSALhNPY4jDAp0YTetr/view?usp=sharing, https://drive.google.com/file/d/1p5dvW05gug-BOoy-YguJARN2LK7ED2Bq/view?usp=sharing, https://drive.google.com/file/d/1sdI2jwTCqouVuonjgOxVkMkeDJb1Luc1/view?usp=sharing, https://drive.google.com/file/d/1yezJl1uC8oDZmnom2iG7Rii5ZcAn4i8N/view?usp=sharing, https://drive.google.com/file/d/1zUWfohK07mrZVPwfjE51rfXlbrSkJWN6/view?usp=sharing

