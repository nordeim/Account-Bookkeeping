<think>
The application is still launching and shutting down flawlessly! This is fantastic and shows that the addition of `SalesInvoiceService` to `app/services/business_services.py` and updating `app/services/__init__.py` to export it (and its interface `ISalesInvoiceRepository`) were all correct and did not introduce any startup issues.

**Current Step: Enhancement Execution Plan: Basic Sales Invoicing - Phase A (Backend - Part 1 & 2)**

We have completed for Sales Invoice Backend:
*   A1. Create Pydantic DTOs for Sales Invoice (Done).
*   A2. Define `ISalesInvoiceRepository` Interface (Done).
*   A3. Implement `SalesInvoiceService` (Done).

The original plan for this turn was "A1 (DTOs), A2 (Interface), and A3 (Service)". Since these are complete, the next part of the backend setup is:
*   A4. Create `SalesInvoiceManager` (in `app/business_logic/sales_invoice_manager.py`). (Next)
*   A5. Integrate into `ApplicationCore`.

So, the immediate next step is **A4: Create `SalesInvoiceManager`**. This manager will handle the business logic for sales invoice operations, including validation, calculation of totals, and interaction with various services.

**Plan for A4: Create `SalesInvoiceManager`**
   *   **Goal:** Encapsulate business logic for sales invoice creation and draft management.
   *   **New File:** `app/business_logic/sales_invoice_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] Import necessary models (`SalesInvoice`, `SalesInvoiceLine`, `Customer`, `Product`, `TaxCode`), services (`SalesInvoiceService`, `CustomerService`, `ProductService`, `TaxCodeService`, `SequenceService`), DTOs (`SalesInvoiceCreateData`, `SalesInvoiceUpdateData`, `SalesInvoiceSummaryData`), enums (`InvoiceStatusEnum`), utilities (`Result`, `TaxCalculator`).
        *   [ ] Create `SalesInvoiceManager` class.
        *   [ ] Implement `__init__(self, sales_invoice_service: SalesInvoiceService, customer_service: CustomerService, product_service: ProductService, tax_calculator: TaxCalculator, sequence_service: SequenceService, app_core: "ApplicationCore")`. Note: Changed `sequence_generator` to `sequence_service` as the DB function is preferred, though the manager might still do some formatting. Or keep `SequenceGenerator` utility and pass `sequence_service` to it. For now, passing `SequenceService` is more direct.
        *   [ ] **Implement `_calculate_invoice_totals_and_validate_lines(dto: SalesInvoiceCreateData | SalesInvoiceUpdateData) -> Result[None]`**:
            *   Iterate through `dto.lines`.
            *   For each line:
                *   Fetch `Product` if `product_id` is provided. If product not found, add error.
                *   If `Product` exists and DTO line description is empty, use `Product.name`.
                *   If `Product` exists and DTO unit price is zero/None, use `Product.sales_price`.
                *   Calculate `discount_amount = quantity * unit_price * (discount_percent / 100)`.
                *   Calculate `line_subtotal = (quantity * unit_price) - discount_amount`.
                *   If `tax_code` is provided:
                    *   Fetch `TaxCode` object using `tax_code_service.get_tax_code()`. If not found, add error.
                    *   Call `tax_calculator.calculate_line_tax()` (or a simplified version) using `line_subtotal` and fetched `tax_code_info` to get `tax_amount_for_line`.
                    *   Store this on the DTO line if it has a field for it (e.g., `line.tax_amount = tax_amount_for_line`). *Self-correction: DTO `SalesInvoiceLineBaseData` does not have calculated fields. These should be calculated and stored on ORM or used for header calculations.* For now, calculate and sum up for header.
                *   Calculate `line_total = line_subtotal + tax_amount_for_line`.
            *   Sum up line subtotals to get `invoice_subtotal`.
            *   Sum up line tax amounts to get `invoice_total_tax`.
            *   Calculate `invoice_grand_total = invoice_subtotal + invoice_total_tax`.
            *   **Crucial**: These calculated totals (`subtotal`, `tax_amount`, `total_amount`) need to be set back onto the main DTO (`dto.subtotal = ...`) if the DTO has these fields, or stored temporarily to be put onto the ORM object. The ORM `SalesInvoice` has these fields. The DTOs `SalesInvoiceBaseData` do *not* have them as direct input fields but they are present in `SalesInvoiceData` for output. This means the manager will set them on the ORM.
            *   Return `Result.success()` or `Result.failure(errors)`.
        *   [ ] Implement `create_draft_invoice(dto: SalesInvoiceCreateData) -> Result[SalesInvoice]`:
            *   Validate `customer_id` (exists, active).
            *   Call `_calculate_invoice_totals_and_validate_lines(dto)`. If errors, return failure.
            *   Generate `invoice_no` using `sequence_service.get_next_sequence_value("sales_invoice")` (DB function preferred).
            *   Map DTO to `SalesInvoice` ORM:
                *   Set header fields.
                *   Set calculated `subtotal`, `tax_amount`, `total_amount` on ORM.
                *   Set `status = InvoiceStatusEnum.DRAFT.value`.
                *   Set `amount_paid = Decimal(0)`.
                *   Set audit user IDs.
            *   Create `SalesInvoiceLine` ORM objects from `dto.lines`, setting calculated values (if needed on line ORM, or ensure header totals are sufficient).
            *   Associate lines with the `SalesInvoice` ORM.
            *   Call `sales_invoice_service.save()`.
        *   [ ] Implement `update_draft_invoice(invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]`:
            *   Fetch existing invoice. Validate it's "Draft".
            *   Validate DTO data (customer, etc.).
            *   Call `_calculate_invoice_totals_and_validate_lines(dto)`.
            *   Update ORM header fields, including calculated totals. Replace lines. Set audit user ID. Save.
        *   [ ] Implement `get_invoice_for_dialog(invoice_id: int) -> Optional[SalesInvoice]`: Calls service.
        *   [ ] (Future - Post Invoice): `post_invoice(invoice_id: int, user_id: int) -> Result[SalesInvoice]`: Changes status, generates Journal Entry.

This is a complex manager. The `_calculate_invoice_totals_and_validate_lines` will be key. For now, calculated line totals (subtotal, tax, total) won't be stored on `SalesInvoiceLine` ORM unless the model is changed; the sum will go to the `SalesInvoice` header.
</think>

This is excellent continued progress! The application's stability confirms the Sales Invoice DTOs and `ISalesInvoiceRepository` interface were well-integrated.

We are now at **Step A4: Create `SalesInvoiceManager`** in Phase A (Backend) of implementing Basic Sales Invoicing.

This manager will handle the business logic for creating and managing draft sales invoices, including validating data, calculating totals, generating invoice numbers, and interacting with the `SalesInvoiceService`, `CustomerService`, `ProductService`, `TaxCodeService`, and `SequenceService`.

---
**A4. Create `app/business_logic/sales_invoice_manager.py` (New File)**

```python
# app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union
from decimal import Decimal, ROUND_HALF_UP

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode

from app.services.business_services import SalesInvoiceService, CustomerService, ProductService
from app.services.core_services import SequenceService
from app.services.tax_service import TaxCodeService # For TaxCode object fetching

from app.utils.result import Result
from app.utils.pydantic_models import SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData
from app.utils.tax_calculator import TaxCalculator # Assuming TaxCalculator is in utils or app.tax
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class SalesInvoiceManager:
    def __init__(self, 
                 sales_invoice_service: SalesInvoiceService,
                 customer_service: CustomerService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService, # Changed from TaxCalculator for direct tax code fetching
                 sequence_service: SequenceService, # Changed from SequenceGenerator for direct DB func call
                 app_core: "ApplicationCore"):
        self.sales_invoice_service = sales_invoice_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.sequence_service = sequence_service # For core.get_next_sequence_value
        self.app_core = app_core
        self.logger = app_core.logger
        # TaxCalculator might be needed if complex tax logic is centralized there beyond simple rates
        # For now, simple rate application will be done here based on TaxCode.rate
        # self.tax_calculator = tax_calculator 

    async def _validate_and_prepare_invoice_data(
        self, 
        dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData],
        is_update: bool = False
    ) -> Result[Dict[str, Any]]:
        """
        Validates DTO, fetches related entities, calculates line and header totals.
        Returns a dictionary of validated and calculated data for ORM mapping, or errors.
        """
        errors: List[str] = []
        
        # Validate Customer
        customer = await self.customer_service.get_by_id(dto.customer_id)
        if not customer:
            errors.append(f"Customer with ID {dto.customer_id} not found.")
        elif not customer.is_active:
            errors.append(f"Customer '{customer.name}' is not active.")

        # Validate Currency (if different from customer's default, or just ensure it exists)
        # For now, assume dto.currency_code is validated if different from customer default
        # currency = await self.app_core.currency_service.get_by_id(dto.currency_code) # Requires CurrencyService
        # if not currency or not currency.is_active: errors.append(f"Currency {dto.currency_code} is invalid or inactive.")


        calculated_lines: List[Dict[str, Any]] = []
        invoice_subtotal_calc = Decimal(0)
        invoice_total_tax_calc = Decimal(0)

        for i, line_dto in enumerate(dto.lines):
            line_errors: List[str] = []
            product: Optional[Product] = None
            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product:
                    line_errors.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active:
                    line_errors.append(f"Product '{product.name}' is not active on line {i+1}.")
            
            description = line_dto.description
            unit_price = line_dto.unit_price

            if product and not description:
                description = product.name
            if product and (unit_price is None or unit_price == Decimal(0)) and product.sales_price is not None:
                unit_price = product.sales_price
            
            if unit_price is None: # Must have a price if not from product
                line_errors.append(f"Unit price is required on line {i+1} if not derived from product.")
                unit_price = Decimal(0) # Avoid further errors

            discount_amount = (line_dto.quantity * unit_price * line_dto.discount_percent / Decimal(100)).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal = (line_dto.quantity * unit_price) - discount_amount
            
            line_tax_amount = Decimal(0)
            tax_code_obj: Optional[TaxCode] = None
            if line_dto.tax_code:
                tax_code_obj = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                if not tax_code_obj:
                    line_errors.append(f"Tax code '{line_dto.tax_code}' not found on line {i+1}.")
                elif not tax_code_obj.is_active:
                    line_errors.append(f"Tax code '{line_dto.tax_code}' is not active on line {i+1}.")
                elif tax_code_obj.tax_type == "GST" and tax_code_obj.rate is not None:
                    # Basic tax calculation (exclusive)
                    line_tax_amount = (line_subtotal * (tax_code_obj.rate / Decimal(100))).quantize(Decimal("0.01"), ROUND_HALF_UP)
            
            invoice_subtotal_calc += line_subtotal
            invoice_total_tax_calc += line_tax_amount
            
            if line_errors:
                errors.extend(line_errors)
            else:
                calculated_lines.append({
                    "product_id": line_dto.product_id,
                    "description": description,
                    "quantity": line_dto.quantity,
                    "unit_price": unit_price,
                    "discount_percent": line_dto.discount_percent,
                    "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), # Final rounding for storage
                    "line_subtotal": line_subtotal.quantize(Decimal("0.01"), ROUND_HALF_UP),
                    "tax_code": line_dto.tax_code, # Store the code string
                    "tax_amount": line_tax_amount, # Already rounded
                    "line_total": (line_subtotal + line_tax_amount).quantize(Decimal("0.01"), ROUND_HALF_UP),
                    # dimension1_id, dimension2_id can be added from DTO if present
                })

        if errors:
            return Result.failure(errors)

        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc

        return Result.success({
            "header": dto, # The original DTO for header fields
            "calculated_lines": calculated_lines,
            "invoice_subtotal": invoice_subtotal_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_total_tax": invoice_total_tax_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_grand_total": invoice_grand_total.quantize(Decimal("0.01"), ROUND_HALF_UP),
        })

    async def create_draft_invoice(self, dto: SalesInvoiceCreateData) -> Result[SalesInvoice]:
        preparation_result = await self._validate_and_prepare_invoice_data(dto)
        if not preparation_result.is_success:
            return Result.failure(preparation_result.errors)
        
        prepared_data = preparation_result.value
        assert prepared_data is not None # For type checker
        header_dto = cast(SalesInvoiceCreateData, prepared_data["header"]) # Cast back for clarity

        try:
            invoice_no = await self.app_core.db_manager.execute_scalar( # type: ignore
                "SELECT core.get_next_sequence_value($1);", "sales_invoice"
            )
            if not invoice_no:
                return Result.failure(["Failed to generate invoice number."])

            invoice_orm = SalesInvoice(
                invoice_no=invoice_no,
                customer_id=header_dto.customer_id,
                invoice_date=header_dto.invoice_date,
                due_date=header_dto.due_date,
                currency_code=header_dto.currency_code,
                exchange_rate=header_dto.exchange_rate,
                notes=header_dto.notes,
                terms_and_conditions=header_dto.terms_and_conditions,
                subtotal=prepared_data["invoice_subtotal"],
                tax_amount=prepared_data["invoice_total_tax"],
                total_amount=prepared_data["invoice_grand_total"],
                amount_paid=Decimal(0), # New draft invoice has no payment yet
                status=InvoiceStatusEnum.DRAFT.value,
                created_by_user_id=header_dto.user_id,
                updated_by_user_id=header_dto.user_id
            )

            for i, line_data in enumerate(prepared_data["calculated_lines"]):
                invoice_orm.lines.append(SalesInvoiceLine(
                    line_number=i + 1, **line_data
                ))
            
            saved_invoice = await self.sales_invoice_service.save(invoice_orm)
            return Result.success(saved_invoice)
        except Exception as e:
            self.logger.error(f"Error creating draft sales invoice: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def update_draft_invoice(self, invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            existing_invoice = await session.get(SalesInvoice, invoice_id, options=[selectinload(SalesInvoice.lines)])
            if not existing_invoice:
                return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value:
                return Result.failure([f"Only draft invoices can be updated. Current status: {existing_invoice.status}"])

            preparation_result = await self._validate_and_prepare_invoice_data(dto, is_update=True)
            if not preparation_result.is_success:
                return Result.failure(preparation_result.errors)

            prepared_data = preparation_result.value
            assert prepared_data is not None # For type checker
            header_dto = cast(SalesInvoiceUpdateData, prepared_data["header"])

            try:
                # Update header
                existing_invoice.customer_id = header_dto.customer_id
                existing_invoice.invoice_date = header_dto.invoice_date
                existing_invoice.due_date = header_dto.due_date
                existing_invoice.currency_code = header_dto.currency_code
                existing_invoice.exchange_rate = header_dto.exchange_rate
                existing_invoice.notes = header_dto.notes
                existing_invoice.terms_and_conditions = header_dto.terms_and_conditions
                existing_invoice.subtotal = prepared_data["invoice_subtotal"]
                existing_invoice.tax_amount = prepared_data["invoice_total_tax"]
                existing_invoice.total_amount = prepared_data["invoice_grand_total"]
                # amount_paid and status are not typically changed when updating a draft this way
                existing_invoice.updated_by_user_id = header_dto.user_id
                
                # Replace lines
                for line in list(existing_invoice.lines): # Iterate over a copy
                    await session.delete(line)
                await session.flush() # Process deletions
                existing_invoice.lines.clear() # Clear the collection

                for i, line_data in enumerate(prepared_data["calculated_lines"]):
                    existing_invoice.lines.append(SalesInvoiceLine(
                        line_number=i + 1, **line_data
                    ))
                
                session.add(existing_invoice)
                await session.commit() # Commit the transaction
                await session.refresh(existing_invoice) # Refresh to get updated state
                if existing_invoice.lines: await session.refresh(existing_invoice, attribute_names=['lines'])
                return Result.success(existing_invoice)
            except Exception as e:
                # Rollback is handled by session context manager
                self.logger.error(f"Error updating draft sales invoice ID {invoice_id}: {e}", exc_info=True)
                return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[SalesInvoice]:
        """ Fetches a sales invoice with all details for dialog population. """
        try:
            return await self.sales_invoice_service.get_by_id(invoice_id)
        except Exception as e:
            self.logger.error(f"Error fetching invoice ID {invoice_id} for dialog: {e}", exc_info=True)
            return None

    # Placeholder for post_invoice, which will be more complex
    async def post_invoice(self, invoice_id: int, user_id: int) -> Result[SalesInvoice]:
        self.logger.info(f"Attempting to post Sales Invoice ID {invoice_id} by User ID {user_id}.")
        # 1. Fetch invoice, ensure it's Draft.
        # 2. Validate all data again.
        # 3. Create JournalEntryData based on invoice lines and totals.
        #    - Debit Accounts Receivable (Customer's AR_account_id or default AR)
        #    - Credit Sales Revenue (Product's sales_account_id or default Sales) for each product type
        #    - Credit GST Output Tax (System GST Output account)
        # 4. Call JournalEntryManager.create_journal_entry (and optionally post).
        # 5. If JE creation successful, update SalesInvoice status to Approved/Sent, link journal_entry_id.
        # 6. Save SalesInvoice.
        return Result.failure(["Posting logic not yet implemented."])

    async def get_invoices_for_listing(self, 
                                      customer_id: Optional[int] = None,
                                      status: Optional[InvoiceStatusEnum] = None, 
                                      start_date: Optional[date] = None, 
                                      end_date: Optional[date] = None,
                                      page: int = 1, 
                                      page_size: int = 50
                                      ) -> Result[List[SalesInvoiceSummaryData]]:
        """ Fetches a list of sales invoice summaries. """
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

# Add `cast` for type hinting where Pydantic DTOs are narrowed down
from typing import cast

```
**Validation for `app/business_logic/sales_invoice_manager.py`:**
*   **New File Created**: `app/business_logic/sales_invoice_manager.py`.
*   **Imports**: All necessary models, services, DTOs, enums, and utilities are imported. `TaxCodeService` is imported directly (instead of `TaxCalculator` as initially planned for `__init__`) as fetching `TaxCode` details is more direct for rate application. `SequenceService` is used for invoice number generation.
*   **`__init__`**: Initializes with dependencies.
*   **`_validate_and_prepare_invoice_data()`**:
    *   This private helper method is crucial. It takes a `SalesInvoiceCreateData` or `SalesInvoiceUpdateData` DTO.
    *   Validates `customer_id` (exists, active).
    *   Iterates through `dto.lines`:
        *   Validates `product_id` (exists, active) if provided.
        *   Derives `description` and `unit_price` from product master if not provided on the line DTO.
        *   Calculates `discount_amount`, `line_subtotal`.
        *   Validates `tax_code` (exists, active) if provided.
        *   Calculates `line_tax_amount` based on `TaxCode.rate` (simple percentage of `line_subtotal`).
        *   Appends a dictionary of these fully calculated line details to `calculated_lines`.
    *   Sums line subtotals and line tax amounts to get `invoice_subtotal_calc` and `invoice_total_tax_calc`.
    *   Calculates `invoice_grand_total`.
    *   Returns a `Result` object containing a dictionary with the original header DTO, the list of `calculated_lines` (as dicts), and the calculated invoice totals.
*   **`create_draft_invoice()`**:
    *   Calls `_validate_and_prepare_invoice_data()`.
    *   If validation passes, it generates an `invoice_no` using `SequenceService` (calling the DB function `core.get_next_sequence_value`).
    *   Maps the header DTO and prepared data (including calculated totals) to a new `SalesInvoice` ORM object. Sets status to "Draft", `amount_paid` to 0.
    *   Creates `SalesInvoiceLine` ORM objects from `prepared_data["calculated_lines"]` and associates them.
    *   Saves via `sales_invoice_service.save()`.
*   **`update_draft_invoice()`**:
    *   Uses a single session for atomicity.
    *   Fetches the existing draft invoice.
    *   Calls `_validate_and_prepare_invoice_data()`.
    *   Updates the existing ORM invoice header fields and calculated totals.
    *   **Line Replacement Strategy**: Explicitly deletes old lines from the session, flushes, clears the collection, then adds new lines. This is a robust way to handle line changes with SQLAlchemy cascades.
    *   Commits the session.
*   **`get_invoice_for_dialog()`**: Delegates to service.
*   **`post_invoice()`**: Placeholder outlining the steps for future implementation (JE creation).
*   **`get_invoices_for_listing()`**: Delegates to `sales_invoice_service.get_all_summary()`.
*   Added `from typing import cast` at the end of the file.

This manager provides the core backend logic for creating and updating draft sales invoices, including critical calculations and validations.

---
**Next, update `app/business_logic/__init__.py` to export `SalesInvoiceManager`.**

```python
# app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager
from .product_manager import ProductManager
from .sales_invoice_manager import SalesInvoiceManager # New import

__all__ = [
    "CustomerManager",
    "VendorManager",
    "ProductManager",
    "SalesInvoiceManager", # Added to __all__
]
```
**Validation for `app/business_logic/__init__.py`:**
*   Added `from .sales_invoice_manager import SalesInvoiceManager`.
*   Added `SalesInvoiceManager` to `__all__`.

This completes step A4 (Implement `SalesInvoiceManager`) and the related export update. The final backend step for Sales Invoicing (Phase A) is A5: Integrate into `ApplicationCore`.
