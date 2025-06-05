<think>
Alright, we've cleared the `ImportError` related to `VendorManager`, and now the traceback points to `app/business_logic/sales_invoice_manager.py` as the next module causing a circular import with `AccountService`. This is consistent with the proactive list I identified.

**Error Analysis (New Traceback):**
The import chain follows the same pattern:
1.  App starts -> ... -> `app.utils.sequence_generator` imports `app.services.core_services.SequenceService`.
2.  This triggers `app.services.__init__.py`, which attempts to import `AccountService`.
3.  `app.services.account_service.py` starts loading.
4.  ... (chain through core) ... -> `app.core.application_core.py` starts loading.
5.  `ApplicationCore` (likely via `app.business_logic.__init__.py`) imports `SalesInvoiceManager`.
6.  `app/business_logic/sales_invoice_manager.py` (line 19) attempts a direct module-level import: `from app.services.account_service import AccountService`.

This again creates the cycle where `AccountService` is being imported while it's already in the middle of its own import process.

**Solution Strategy (Consistent with previous fixes):**
Modify `SalesInvoiceManager` to use conditional imports (`if TYPE_CHECKING:`) or string literals for type hinting its numerous service dependencies that are injected via its constructor by `ApplicationCore`.

**Files to Modify:**
For this specific traceback, only `app/business_logic/sales_invoice_manager.py`.
However, given the instruction "systematically fix each file affected" and the previous agreement to proactively fix, I will address all remaining managers from my identified list that are present in the user's provided codebase files.

The list from before was:
*   `app/business_logic/sales_invoice_manager.py` (current error)
*   `app/business_logic/purchase_invoice_manager.py`
*   `app/tax/tax_calculator.py`
*   `app/tax/gst_manager.py`
*   `app/tax/income_tax_manager.py`
*   `app.tax/withholding_tax_manager.py`
*   `app/reporting/financial_statement_generator.py`

I will provide the updated `sales_invoice_manager.py` first, and then the others that were part of the provided file sets.

**Detailed Plan for Fixing `SalesInvoiceManager`:**
1.  **Modify `app/business_logic/sales_invoice_manager.py`**:
    *   Identify all direct service imports at the top of the file that are used as type hints for constructor arguments. These include:
        *   `SalesInvoiceService`, `CustomerService`, `ProductService`, `InventoryMovementService` (from `app.services.business_services`)
        *   `SequenceService`, `ConfigurationService` (from `app.services.core_services`)
        *   `TaxCodeService` (from `app.services.tax_service`)
        *   `AccountService` (from `app.services.account_service`)
        *   `TaxCalculator` (from `app.tax.tax_calculator`) - Note: `TaxCalculator` is not a service but a utility class. If `TaxCalculator` itself has dependencies that could lead to cycles when imported by `ApplicationCore`, it might also need similar treatment. For now, focusing on services.
    *   Move these imports into the `if TYPE_CHECKING:` block.
    *   Update the constructor's type hints for these services to be string literals or ensure they refer to the conditionally imported types.

Looking at `app/business_logic/sales_invoice_manager.py` from `project_codebase_files_set-1.md`:
```python
# Imports are extensive
from app.services.business_services import SalesInvoiceService, CustomerService, ProductService, InventoryMovementService
from app.services.core_services import SequenceService, ConfigurationService 
from app.services.tax_service import TaxCodeService 
from app.services.account_service import AccountService 
from app.tax.tax_calculator import TaxCalculator # This is a utility, not a service injected by AppCore typically, but passed in.

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    # JournalEntryManager is also used, but for method calls, not constructor.
    # Its import seems to be handled via app_core.journal_entry_manager.

class SalesInvoiceManager:
    def __init__(self, 
                 sales_invoice_service: SalesInvoiceService,
                 customer_service: CustomerService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService, 
                 tax_calculator: TaxCalculator, 
                 sequence_service: SequenceService,
                 account_service: AccountService, 
                 configuration_service: ConfigurationService, 
                 app_core: "ApplicationCore",
                 inventory_movement_service: InventoryMovementService):
        # ...
```
All these constructor-injected dependencies that are imported directly at the module level are candidates for conditional import. `TaxCalculator` is passed in, so its type hint also needs to be handled.

I will apply the fixes systematically.
</think>

You're absolutely right to continue with the systematic approach. We have another circular import error, this time pinpointing `app/business_logic/sales_invoice_manager.py` attempting to import `AccountService` prematurely.

The pattern is consistent: `ApplicationCore` imports various managers. These managers, in turn, directly import services. If the initialization of these services (or their dependencies like `DatabaseManager`) requires parts of `ApplicationCore` that are not yet fully defined because `ApplicationCore` is still processing its own imports (like the current manager), a cycle occurs.

We will apply the same fix strategy: move direct module-level imports of service dependencies (that are injected via constructor) into an `if TYPE_CHECKING:` block and use string literals or the conditionally imported names for type hints in the `__init__` signature.

I will fix `app/business_logic/sales_invoice_manager.py` first, as it's the cause of the current traceback. Then, as per your instruction for thoroughness, I will proceed to fix the remaining managers and utilities from my previously identified list that were included in the codebase snippets you've shared.

**Files to be proactively fixed in this response (following `SalesInvoiceManager`):**
*   `app/business_logic/purchase_invoice_manager.py`
*   `app/tax/tax_calculator.py`
*   `app/tax/gst_manager.py`
*   `app/tax/income_tax_manager.py`
*   `app/tax/withholding_tax_manager.py`
*   `app/reporting/financial_statement_generator.py`

---
**1. Updated File: `app/business_logic/sales_invoice_manager.py`**
---
```python
# File: app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime 

from sqlalchemy import text 
from sqlalchemy.orm import selectinload 

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
# REMOVED: from app.models.accounting.tax_code import TaxCode # Not directly used here, TaxCodeService is
from app.models.accounting.journal_entry import JournalEntry 
from app.models.business.inventory_movement import InventoryMovement 

# REMOVED: from app.services.business_services import SalesInvoiceService, CustomerService, ProductService, InventoryMovementService
# REMOVED: from app.services.core_services import SequenceService, ConfigurationService 
# REMOVED: from app.services.tax_service import TaxCodeService 
# REMOVED: from app.services.account_service import AccountService 
# REMOVED: from app.tax.tax_calculator import TaxCalculator 

from app.utils.result import Result
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    SalesInvoiceSummaryData, TaxCalculationResultData,
    JournalEntryData, JournalEntryLineData 
)
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum, InventoryMovementTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import SalesInvoiceService, CustomerService, ProductService, InventoryMovementService
    from app.services.core_services import SequenceService, ConfigurationService
    from app.services.tax_service import TaxCodeService
    from app.services.account_service import AccountService
    from app.tax.tax_calculator import TaxCalculator
    from app.models.accounting.tax_code import TaxCode # Keep for TaxCodeService method returns if needed

class SalesInvoiceManager:
    def __init__(self, 
                 sales_invoice_service: "SalesInvoiceService",
                 customer_service: "CustomerService",
                 product_service: "ProductService",
                 tax_code_service: "TaxCodeService", 
                 tax_calculator: "TaxCalculator", 
                 sequence_service: "SequenceService",
                 account_service: "AccountService", 
                 configuration_service: "ConfigurationService", 
                 app_core: "ApplicationCore",
                 inventory_movement_service: "InventoryMovementService"): 
        self.sales_invoice_service = sales_invoice_service
        self.customer_service = customer_service
        self.product_service = product_service
        self.tax_code_service = tax_code_service
        self.tax_calculator = tax_calculator 
        self.sequence_service = sequence_service 
        self.account_service = account_service 
        self.configuration_service = configuration_service 
        self.app_core = app_core
        self.logger = app_core.logger
        self.inventory_movement_service = inventory_movement_service

    async def _validate_and_prepare_invoice_data(
        self, 
        dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData],
        is_update: bool = False 
    ) -> Result[Dict[str, Any]]:
        errors: List[str] = []
        customer = await self.customer_service.get_by_id(dto.customer_id)
        if not customer: errors.append(f"Customer with ID {dto.customer_id} not found.")
        elif not customer.is_active: errors.append(f"Customer '{customer.name}' (ID: {dto.customer_id}) is not active.")
        if not dto.currency_code or len(dto.currency_code) != 3: errors.append(f"Invalid currency code: '{dto.currency_code}'.")
        else:
           currency_obj = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
           if not currency_obj or not currency_obj.is_active: errors.append(f"Currency '{dto.currency_code}' is invalid or not active.")
        calculated_lines_for_orm: List[Dict[str, Any]] = []; invoice_subtotal_calc = Decimal(0); invoice_total_tax_calc = Decimal(0)
        if not dto.lines: errors.append("Sales invoice must have at least one line item.")
        for i, line_dto in enumerate(dto.lines):
            line_errors_current_line: List[str] = []; product: Optional[Product] = None; line_description = line_dto.description
            unit_price = line_dto.unit_price; line_sales_account_id: Optional[int] = None; product_type_for_line: Optional[ProductTypeEnum] = None
            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product: line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active: line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                if product: 
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.sales_price is not None: unit_price = product.sales_price
                    line_sales_account_id = product.sales_account_id; product_type_for_line = ProductTypeEnum(product.product_type)
            if not line_description: line_errors_current_line.append(f"Description is required on line {i+1}.")
            if unit_price is None: line_errors_current_line.append(f"Unit price is required on line {i+1}."); unit_price = Decimal(0) 
            try:
                qty = Decimal(str(line_dto.quantity)); price = Decimal(str(unit_price)); discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if price < 0: line_errors_current_line.append(f"Unit price cannot be negative on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation: line_errors_current_line.append(f"Invalid numeric for qty/price/disc on line {i+1}."); errors.extend(line_errors_current_line); continue
            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount; line_tax_amount_calc = Decimal(0); line_tax_account_id: Optional[int] = None 
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(amount=line_subtotal_before_tax, tax_code_str=line_dto.tax_code, transaction_type="SalesInvoiceLine")
                line_tax_amount_calc = tax_calc_result.tax_amount; line_tax_account_id = tax_calc_result.tax_account_id 
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0): 
                    tc_check_orm = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check_orm or not tc_check_orm.is_active: line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            invoice_subtotal_calc += line_subtotal_before_tax; invoice_total_tax_calc += line_tax_amount_calc
            if line_errors_current_line: errors.extend(line_errors_current_line)
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": line_description, "quantity": qty, "unit_price": price, "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc, "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
                "_line_sales_account_id": line_sales_account_id, "_line_tax_account_id": line_tax_account_id, "_product_type": product_type_for_line
            })
        if errors: return Result.failure(errors)
        invoice_grand_total = invoice_subtotal_calc + invoice_total_tax_calc
        return Result.success({
            "header_dto": dto, "customer_orm": customer, "calculated_lines_for_orm": calculated_lines_for_orm,
            "invoice_subtotal": invoice_subtotal_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_total_tax": invoice_total_tax_calc.quantize(Decimal("0.01"), ROUND_HALF_UP),
            "invoice_grand_total": invoice_grand_total.quantize(Decimal("0.01"), ROUND_HALF_UP),
        })

    async def create_draft_invoice(self, dto: SalesInvoiceCreateData) -> Result[SalesInvoice]:
        preparation_result = await self._validate_and_prepare_invoice_data(dto)
        if not preparation_result.is_success: return Result.failure(preparation_result.errors)
        prepared_data = preparation_result.value; assert prepared_data is not None 
        header_dto = cast(SalesInvoiceCreateData, prepared_data["header_dto"])
        try:
            invoice_no_val = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "sales_invoice")
            if not invoice_no_val or not isinstance(invoice_no_val, str): return Result.failure(["Failed to generate invoice number."])
            invoice_no = invoice_no_val
            invoice_orm = SalesInvoice(
                invoice_no=invoice_no, customer_id=header_dto.customer_id, invoice_date=header_dto.invoice_date, due_date=header_dto.due_date,
                currency_code=header_dto.currency_code, exchange_rate=header_dto.exchange_rate, notes=header_dto.notes, 
                terms_and_conditions=header_dto.terms_and_conditions, subtotal=prepared_data["invoice_subtotal"], 
                tax_amount=prepared_data["invoice_total_tax"], total_amount=prepared_data["invoice_grand_total"], 
                amount_paid=Decimal(0), status=InvoiceStatusEnum.DRAFT.value,
                created_by_user_id=header_dto.user_id, updated_by_user_id=header_dto.user_id
            )
            for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_') and k != "_product_type"}
                invoice_orm.lines.append(SalesInvoiceLine(line_number=i + 1, **orm_line_data))
            saved_invoice = await self.sales_invoice_service.save(invoice_orm)
            return Result.success(saved_invoice)
        except Exception as e: self.logger.error(f"Error creating draft SI: {e}", exc_info=True); return Result.failure([f"Error creating SI: {str(e)}"])

    async def update_draft_invoice(self, invoice_id: int, dto: SalesInvoiceUpdateData) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(SalesInvoice, invoice_id, options=[selectinload(SalesInvoice.lines)])
            if not existing_invoice: return Result.failure([f"SI ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft invoices can be updated. Status: {existing_invoice.status}"])
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
                existing_invoice.total_amount = prepared_data["invoice_grand_total"]; existing_invoice.updated_by_user_id = header_dto.user_id
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() 
                new_lines_orm: List[SalesInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_') and k != "_product_type"}
                    new_lines_orm.append(SalesInvoiceLine(line_number=i + 1, **orm_line_data))
                existing_invoice.lines = new_lines_orm 
                await session.flush(); await session.refresh(existing_invoice)
                if existing_invoice.lines: await session.refresh(existing_invoice, attribute_names=['lines'])
                return Result.success(existing_invoice)
            except Exception as e: self.logger.error(f"Error updating draft SI ID {invoice_id}: {e}", exc_info=True); return Result.failure([f"Error updating SI: {str(e)}"])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[SalesInvoice]:
        try: return await self.sales_invoice_service.get_by_id(invoice_id)
        except Exception as e: self.logger.error(f"Error fetching SI ID {invoice_id} for dialog: {e}", exc_info=True); return None


    async def post_invoice(self, invoice_id: int, user_id: int) -> Result[SalesInvoice]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            try:
                invoice_to_post = await session.get(
                    SalesInvoice, invoice_id, 
                    options=[
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.sales_account),
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.inventory_account), 
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.purchase_account), 
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj).selectinload(TaxCode.affects_account), 
                        selectinload(SalesInvoice.customer).selectinload(Customer.receivables_account)
                    ]
                )
                if not invoice_to_post: return Result.failure([f"SI ID {invoice_id} not found."])
                if invoice_to_post.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only Draft invoices can be posted. Status: {invoice_to_post.status}."])
                if not invoice_to_post.customer or not invoice_to_post.customer.is_active: return Result.failure(["Customer is inactive or not found."])
                if not invoice_to_post.customer.receivables_account_id or not invoice_to_post.customer.receivables_account: return Result.failure([f"Customer '{invoice_to_post.customer.name}' AR account not configured or invalid."])
                ar_account = invoice_to_post.customer.receivables_account
                if not ar_account.is_active: return Result.failure([f"Configured AR account '{ar_account.code}' for customer is inactive."])

                default_sales_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultSalesRevenue", "4100")
                default_gst_output_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultGSTOutput", "SYS-GST-OUTPUT")
                default_cogs_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultCOGS", "5100") 

                fin_je_lines_data: List[JournalEntryLineData] = []
                fin_je_lines_data.append(JournalEntryLineData( account_id=ar_account.id, debit_amount=invoice_to_post.total_amount, credit_amount=Decimal(0), description=f"A/R for Inv {invoice_to_post.invoice_no}", currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate))
                for line in invoice_to_post.lines:
                    sales_gl_id = line.product.sales_account.id if line.product and line.product.sales_account and line.product.sales_account.is_active else (await self.account_service.get_by_code(default_sales_acc_code)).id # type: ignore
                    if not sales_gl_id: return Result.failure([f"Could not determine Sales Revenue account for line: {line.description}"])
                    fin_je_lines_data.append(JournalEntryLineData( account_id=sales_gl_id, debit_amount=Decimal(0), credit_amount=line.line_subtotal, description=f"Sale: {line.description[:100]} (Inv {invoice_to_post.invoice_no})", currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate))
                    if line.tax_amount and line.tax_amount != Decimal(0) and line.tax_code:
                        gst_gl_id_orm = line.tax_code_obj.affects_account if line.tax_code_obj and line.tax_code_obj.affects_account else None
                        gst_gl_id = gst_gl_id_orm.id if gst_gl_id_orm and gst_gl_id_orm.is_active else (await self.account_service.get_by_code(default_gst_output_acc_code)).id if default_gst_output_acc_code else None # type: ignore
                        if not gst_gl_id: return Result.failure([f"Could not determine GST Output account for tax on line: {line.description}"])
                        fin_je_lines_data.append(JournalEntryLineData( account_id=gst_gl_id, debit_amount=Decimal(0), credit_amount=line.tax_amount, description=f"GST Output ({line.tax_code}) for Inv {invoice_to_post.invoice_no}", currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate))
                
                fin_je_dto = JournalEntryData( journal_type=JournalTypeEnum.SALES.value, entry_date=invoice_to_post.invoice_date, description=f"Sales Invoice {invoice_to_post.invoice_no} to {invoice_to_post.customer.name}", source_type="SalesInvoice", source_id=invoice_to_post.id, user_id=user_id, lines=fin_je_lines_data)
                create_fin_je_result = await self.app_core.journal_entry_manager.create_journal_entry(fin_je_dto, session=session)
                if not create_fin_je_result.is_success or not create_fin_je_result.value: return Result.failure(["Failed to create financial JE for SI."] + create_fin_je_result.errors)
                created_fin_je: JournalEntry = create_fin_je_result.value
                post_fin_je_result = await self.app_core.journal_entry_manager.post_journal_entry(created_fin_je.id, user_id, session=session)
                if not post_fin_je_result.is_success: return Result.failure([f"Financial JE (ID: {created_fin_je.id}) created but failed to post."] + post_fin_je_result.errors)

                cogs_je_lines_data: List[JournalEntryLineData] = []
                for line in invoice_to_post.lines:
                    if line.product and ProductTypeEnum(line.product.product_type) == ProductTypeEnum.INVENTORY:
                        wac_query = text("SELECT average_cost FROM business.inventory_summary WHERE product_id = :pid")
                        wac_result = await session.execute(wac_query, {"pid": line.product_id})
                        current_wac = wac_result.scalar_one_or_none()
                        if current_wac is None: current_wac = line.product.purchase_price or Decimal(0) 
                        
                        cogs_amount_for_line = (line.quantity * current_wac).quantize(Decimal("0.01"), ROUND_HALF_UP)

                        inv_movement = InventoryMovement(
                            product_id=line.product_id, movement_date=invoice_to_post.invoice_date,
                            movement_type=InventoryMovementTypeEnum.SALE.value, quantity=-line.quantity, 
                            unit_cost=current_wac, total_cost=cogs_amount_for_line,
                            reference_type='SalesInvoiceLine', reference_id=line.id, created_by_user_id=user_id
                        )
                        await self.inventory_movement_service.save(inv_movement, session=session)

                        cogs_acc_orm = line.product.purchase_account if line.product.purchase_account and line.product.purchase_account.is_active else (await self.account_service.get_by_code(default_cogs_acc_code))
                        inv_asset_acc_orm = line.product.inventory_account if line.product.inventory_account and line.product.inventory_account.is_active else None # No easy system default for this specific product's asset account
                        if not cogs_acc_orm or not cogs_acc_orm.is_active or not inv_asset_acc_orm or not inv_asset_acc_orm.is_active: return Result.failure(["COGS or Inventory Asset account setup issue for product."])
                        
                        cogs_je_lines_data.append(JournalEntryLineData(account_id=cogs_acc_orm.id, debit_amount=cogs_amount_for_line, credit_amount=Decimal(0), description=f"COGS: {line.description[:50]}"))
                        cogs_je_lines_data.append(JournalEntryLineData(account_id=inv_asset_acc_orm.id, debit_amount=Decimal(0), credit_amount=cogs_amount_for_line, description=f"Inventory Sold: {line.description[:50]}"))

                if cogs_je_lines_data:
                    cogs_je_dto = JournalEntryData(journal_type=JournalTypeEnum.GENERAL.value, entry_date=invoice_to_post.invoice_date, description=f"COGS for SI {invoice_to_post.invoice_no}", source_type="SalesInvoiceCOGS", source_id=invoice_to_post.id, user_id=user_id, lines=cogs_je_lines_data)
                    create_cogs_je_result = await self.app_core.journal_entry_manager.create_journal_entry(cogs_je_dto, session=session)
                    if not create_cogs_je_result.is_success or not create_cogs_je_result.value: return Result.failure(["Failed to create COGS JE."] + create_cogs_je_result.errors)
                    post_cogs_je_result = await self.app_core.journal_entry_manager.post_journal_entry(create_cogs_je_result.value.id, user_id, session=session)
                    if not post_cogs_je_result.is_success: return Result.failure([f"COGS JE (ID: {create_cogs_je_result.value.id}) created but failed to post."] + post_cogs_je_result.errors)

                invoice_to_post.status = InvoiceStatusEnum.APPROVED.value 
                invoice_to_post.journal_entry_id = created_fin_je.id
                invoice_to_post.updated_by_user_id = user_id
                session.add(invoice_to_post); await session.flush(); await session.refresh(invoice_to_post)
                self.logger.info(f"SI {invoice_to_post.invoice_no} (ID: {invoice_id}) posted. Fin JE ID: {created_fin_je.id}")
                return Result.success(invoice_to_post)

            except Exception as e: self.logger.error(f"Error posting SI ID {invoice_id}: {e}", exc_info=True); return Result.failure([f"Unexpected error posting SI: {str(e)}"])

    async def get_invoices_for_listing(self, customer_id: Optional[int]=None, status:Optional[InvoiceStatusEnum]=None, start_date:Optional[date]=None, end_date:Optional[date]=None, page:int=1, page_size:int=50) -> Result[List[SalesInvoiceSummaryData]]:
        try:
            summaries = await self.sales_invoice_service.get_all_summary(customer_id=customer_id, status=status, start_date=start_date, end_date=end_date, page=page, page_size=page_size)
            return Result.success(summaries)
        except Exception as e: self.logger.error(f"Error fetching SI listing: {e}", exc_info=True); return Result.failure([f"Failed to retrieve SI list: {str(e)}"])
```

---
**Continuation of Proactive Fixes for Other Managers and Utilities:**
I will continue applying the same fix pattern to the remaining identified files. Due to response length, I will provide them in batches or confirm once all are done.
The principle remains: replace direct module-level imports of constructor-injected services with conditional imports under `if TYPE_CHECKING:` and use string literals or the conditional type hints in `__init__` signatures.
