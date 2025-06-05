<think>
The application is still encountering circular import errors. The previous fix for `SalesInvoiceManager` was correct for that specific file, but the underlying pattern of direct service imports in managers initialized by `ApplicationCore` is causing subsequent failures as Python's import machinery hits the next manager in the chain.

**Current Error Analysis (New Traceback):**
The traceback now points to `app/business_logic/purchase_invoice_manager.py` (line 18) attempting a direct module-level import: `from app.services.account_service import AccountService`.

The import chain is:
1.  App starts -> ... -> `app.utils.sequence_generator` imports `app.services.core_services.SequenceService`.
2.  This triggers `app.services.__init__.py` to load, which attempts to import `AccountService`.
3.  `app.services.account_service.py` starts loading.
4.  ... (chain through core) ... -> `app.core.application_core.py` starts loading.
5.  `ApplicationCore` (likely via `app.business_logic.__init__.py`) imports `PurchaseInvoiceManager`.
6.  `app.business_logic/purchase_invoice_manager.py` then attempts its direct import of `AccountService`.

This is the identical cycle, just with `PurchaseInvoiceManager` as the current trigger point.

**Solution Strategy (Consistent & Proactive):**
As per my previous commitment to systematically fix all affected files, I will apply the same solution pattern (conditional imports for service type hints in constructor arguments) to `PurchaseInvoiceManager` and the remaining identified managers and utilities from my list that were provided in the user's codebase snippets.

**Files to Modify in this Batch (Continuing Proactive Fixes):**
1.  `app/business_logic/purchase_invoice_manager.py` (current error)
2.  `app/tax/tax_calculator.py`
3.  `app/tax/gst_manager.py`
4.  `app/tax/income_tax_manager.py`
5.  `app/tax/withholding_tax_manager.py`
6.  `app/reporting/financial_statement_generator.py`

I will generate the updated versions for these files.

**Detailed Plan for Each File:**
For each file listed above:
1.  Identify all direct service imports at the top of the file that are used as type hints for constructor arguments.
2.  Move these imports into an `if TYPE_CHECKING:` block.
3.  Update the constructor's type hints for these services to be string literals (e.g., `service_name: "ServiceName"`) or ensure they refer to the types imported under `TYPE_CHECKING`.

Let's start with `PurchaseInvoiceManager`.
</think>

Understood. The circular import issue is indeed a pattern affecting multiple manager classes due to their direct, module-level imports of services that are also part of `ApplicationCore`'s initialization sequence (or dependencies thereof).

We will continue to systematically apply the fix:
1.  Remove direct service imports used for constructor type hints from the top of the manager/utility file.
2.  Place these imports under an `if TYPE_CHECKING:` block.
3.  Adjust the constructor's type hints for these injected services to use string literals (e.g., `service_name: "ServiceName"`) or rely on the conditionally imported types.

I will now provide the updated files for `PurchaseInvoiceManager` (which is causing the current error) and the rest of the previously identified affected managers and utilities that were part of the provided codebase snippets.

---
**1. Updated File: `app/business_logic/purchase_invoice_manager.py`**
---
```python
# File: app/business_logic/purchase_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

from sqlalchemy.orm import selectinload 
from sqlalchemy import text # Added text

from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
# REMOVED: from app.models.business.vendor import Vendor # Not directly used, VendorService is
# REMOVED: from app.models.business.product import Product # Not directly used, ProductService is
# REMOVED: from app.models.accounting.tax_code import TaxCode # Not directly used, TaxCodeService is
# REMOVED: from app.models.accounting.journal_entry import JournalEntry # Not directly used, JournalEntryManager is
from app.models.business.inventory_movement import InventoryMovement 

# REMOVED: from app.services.business_services import PurchaseInvoiceService, VendorService, ProductService, InventoryMovementService
# REMOVED: from app.services.core_services import SequenceService, ConfigurationService
# REMOVED: from app.services.tax_service import TaxCodeService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.tax.tax_calculator import TaxCalculator

from app.utils.result import Result
from app.utils.pydantic_models import (
    PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceSummaryData,
    PurchaseInvoiceLineBaseData, TaxCalculationResultData,
    JournalEntryData, JournalEntryLineData 
)
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum, InventoryMovementTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import PurchaseInvoiceService, VendorService, ProductService, InventoryMovementService
    from app.services.core_services import SequenceService, ConfigurationService
    from app.services.tax_service import TaxCodeService
    from app.services.account_service import AccountService
    from app.tax.tax_calculator import TaxCalculator
    from app.models.business.vendor import Vendor # For type hint
    from app.models.business.product import Product # For type hint
    from app.models.accounting.tax_code import TaxCode # For type hint


class PurchaseInvoiceManager:
    def __init__(self,
                 purchase_invoice_service: "PurchaseInvoiceService",
                 vendor_service: "VendorService",
                 product_service: "ProductService",
                 tax_code_service: "TaxCodeService",
                 tax_calculator: "TaxCalculator",
                 sequence_service: "SequenceService", 
                 account_service: "AccountService",
                 configuration_service: "ConfigurationService",
                 app_core: "ApplicationCore",
                 inventory_movement_service: "InventoryMovementService"): 
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
        self.inventory_movement_service = inventory_movement_service
        
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

        if dto.vendor_invoice_no and not is_update: 
            existing_pi = await self.purchase_invoice_service.get_by_vendor_and_vendor_invoice_no(dto.vendor_id, dto.vendor_invoice_no)
            if existing_pi:
                errors.append(f"Duplicate vendor invoice number '{dto.vendor_invoice_no}' already exists for this vendor.")
        elif dto.vendor_invoice_no and is_update and isinstance(dto, PurchaseInvoiceUpdateData): 
            existing_pi_for_update = await self.purchase_invoice_service.get_by_id(dto.id) 
            if existing_pi_for_update and existing_pi_for_update.vendor_invoice_no != dto.vendor_invoice_no:
                colliding_pi = await self.purchase_invoice_service.get_by_vendor_and_vendor_invoice_no(dto.vendor_id, dto.vendor_invoice_no)
                if colliding_pi and colliding_pi.id != dto.id:
                    errors.append(f"Duplicate vendor invoice number '{dto.vendor_invoice_no}' already exists for this vendor on another record.")

        calculated_lines_for_orm: List[Dict[str, Any]] = []
        invoice_subtotal_calc = Decimal(0)
        invoice_total_tax_calc = Decimal(0)

        if not dto.lines: errors.append("Purchase invoice must have at least one line item.")
        
        for i, line_dto in enumerate(dto.lines):
            line_errors_current_line: List[str] = []
            product: Optional["Product"] = None # Use TYPE_CHECKING import
            line_description = line_dto.description
            unit_price = line_dto.unit_price
            line_purchase_account_id: Optional[int] = None 
            line_tax_account_id: Optional[int] = None
            product_type_for_line: Optional[ProductTypeEnum] = None


            if line_dto.product_id:
                product = await self.product_service.get_by_id(line_dto.product_id)
                if not product: line_errors_current_line.append(f"Product ID {line_dto.product_id} not found on line {i+1}.")
                elif not product.is_active: line_errors_current_line.append(f"Product '{product.name}' is not active on line {i+1}.")
                if product: 
                    if not line_description: line_description = product.name
                    if (unit_price is None or unit_price == Decimal(0)) and product.purchase_price is not None: unit_price = product.purchase_price
                    line_purchase_account_id = product.purchase_account_id
                    product_type_for_line = ProductTypeEnum(product.product_type) 
            
            if not line_description: line_errors_current_line.append(f"Description is required on line {i+1}.")
            if unit_price is None: line_errors_current_line.append(f"Unit price is required on line {i+1}."); unit_price = Decimal(0) 

            try:
                qty = Decimal(str(line_dto.quantity)); price = Decimal(str(unit_price)); discount_pct = Decimal(str(line_dto.discount_percent))
                if qty <= 0: line_errors_current_line.append(f"Quantity must be positive on line {i+1}.")
                if not (0 <= discount_pct <= 100): line_errors_current_line.append(f"Discount percent must be between 0 and 100 on line {i+1}.")
            except InvalidOperation: line_errors_current_line.append(f"Invalid numeric value for quantity, price, or discount on line {i+1}."); errors.extend(line_errors_current_line); continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(amount=line_subtotal_before_tax, tax_code_str=line_dto.tax_code, transaction_type="PurchaseInvoiceLine")
                line_tax_amount_calc = tax_calc_result.tax_amount; line_tax_account_id = tax_calc_result.tax_account_id
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0):
                    tc_check_orm = await self.tax_code_service.get_tax_code(line_dto.tax_code) # Use TYPE_CHECKING import
                    if not tc_check_orm or not tc_check_orm.is_active: line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
            invoice_subtotal_calc += line_subtotal_before_tax; invoice_total_tax_calc += line_tax_amount_calc
            if line_errors_current_line: errors.extend(line_errors_current_line)
            
            calculated_lines_for_orm.append({
                "product_id": line_dto.product_id, "description": line_description, "quantity": qty, "unit_price": price, "discount_percent": discount_pct,
                "discount_amount": discount_amount.quantize(Decimal("0.01"), ROUND_HALF_UP), "line_subtotal": line_subtotal_before_tax.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "tax_code": line_dto.tax_code, "tax_amount": line_tax_amount_calc.quantize(Decimal("0.01"), ROUND_HALF_UP), 
                "line_total": (line_subtotal_before_tax + line_tax_amount_calc).quantize(Decimal("0.01"), ROUND_HALF_UP),
                "dimension1_id": line_dto.dimension1_id, "dimension2_id": line_dto.dimension2_id,
                "_line_purchase_account_id": line_purchase_account_id, "_line_tax_account_id": line_tax_account_id, "_product_type": product_type_for_line
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
        if not preparation_result.is_success: return Result.failure(preparation_result.errors)
        prepared_data = preparation_result.value; assert prepared_data is not None 
        header_dto = cast(PurchaseInvoiceCreateData, prepared_data["header_dto"])
        try:
            our_internal_ref_no = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "purchase_invoice")
            if not our_internal_ref_no or not isinstance(our_internal_ref_no, str): return Result.failure(["Failed to generate internal invoice number."])
            invoice_orm = PurchaseInvoice(
                invoice_no=our_internal_ref_no, vendor_invoice_no=header_dto.vendor_invoice_no, vendor_id=header_dto.vendor_id,
                invoice_date=header_dto.invoice_date, due_date=header_dto.due_date, currency_code=header_dto.currency_code, 
                exchange_rate=header_dto.exchange_rate, notes=header_dto.notes, subtotal=prepared_data["invoice_subtotal"], 
                tax_amount=prepared_data["invoice_total_tax"], total_amount=prepared_data["invoice_grand_total"], 
                amount_paid=Decimal(0), status=InvoiceStatusEnum.DRAFT.value, 
                created_by_user_id=header_dto.user_id, updated_by_user_id=header_dto.user_id
            )
            for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_') and k != "_product_type"}
                invoice_orm.lines.append(PurchaseInvoiceLine(line_number=i + 1, **orm_line_data))
            saved_invoice = await self.purchase_invoice_service.save(invoice_orm)
            self.logger.info(f"Draft PI '{saved_invoice.invoice_no}' created for vendor ID {saved_invoice.vendor_id}.")
            return Result.success(saved_invoice)
        except Exception as e: self.logger.error(f"Error creating draft PI: {e}", exc_info=True); return Result.failure([f"Error creating PI: {str(e)}"])

    async def update_draft_purchase_invoice(self, invoice_id: int, dto: PurchaseInvoiceUpdateData) -> Result[PurchaseInvoice]:
        async with self.app_core.db_manager.session() as session: 
            existing_invoice = await session.get(PurchaseInvoice, invoice_id, options=[selectinload(PurchaseInvoice.lines)])
            if not existing_invoice: return Result.failure([f"PI ID {invoice_id} not found."])
            if existing_invoice.status != InvoiceStatusEnum.DRAFT.value: return Result.failure([f"Only draft PIs can be updated. Status: {existing_invoice.status}"])
            preparation_result = await self._validate_and_prepare_pi_data(dto, is_update=True)
            if not preparation_result.is_success: return Result.failure(preparation_result.errors)
            prepared_data = preparation_result.value; assert prepared_data is not None 
            header_dto = cast(PurchaseInvoiceUpdateData, prepared_data["header_dto"])
            try:
                existing_invoice.vendor_id = header_dto.vendor_id; existing_invoice.vendor_invoice_no = header_dto.vendor_invoice_no
                existing_invoice.invoice_date = header_dto.invoice_date; existing_invoice.due_date = header_dto.due_date
                existing_invoice.currency_code = header_dto.currency_code; existing_invoice.exchange_rate = header_dto.exchange_rate
                existing_invoice.notes = header_dto.notes; existing_invoice.subtotal = prepared_data["invoice_subtotal"]
                existing_invoice.tax_amount = prepared_data["invoice_total_tax"]; existing_invoice.total_amount = prepared_data["invoice_grand_total"]
                existing_invoice.updated_by_user_id = header_dto.user_id
                for line_orm_to_delete in list(existing_invoice.lines): await session.delete(line_orm_to_delete)
                await session.flush() 
                new_lines_orm: List[PurchaseInvoiceLine] = []
                for i, line_data_dict in enumerate(prepared_data["calculated_lines_for_orm"]):
                    orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_') and k != "_product_type"}
                    new_lines_orm.append(PurchaseInvoiceLine(line_number=i + 1, **orm_line_data))
                existing_invoice.lines = new_lines_orm 
                await session.flush(); await session.refresh(existing_invoice, attribute_names=['lines'])
                self.logger.info(f"Draft PI '{existing_invoice.invoice_no}' (ID: {invoice_id}) updated.")
                return Result.success(existing_invoice)
            except Exception as e: self.logger.error(f"Error updating draft PI ID {invoice_id}: {e}", exc_info=True); return Result.failure([f"Error updating PI: {str(e)}"])

    async def post_purchase_invoice(self, invoice_id: int, user_id: int) -> Result[PurchaseInvoice]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            try:
                invoice_to_post = await session.get(
                    PurchaseInvoice, invoice_id, 
                    options=[
                        selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product).selectinload(Product.purchase_account),
                        selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product).selectinload(Product.inventory_account),
                        selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj).selectinload(TaxCode.affects_account), 
                        selectinload(PurchaseInvoice.vendor).selectinload(Vendor.payables_account)
                    ]
                )
                if not invoice_to_post:
                    return Result.failure([f"Purchase Invoice ID {invoice_id} not found."])
                if invoice_to_post.status != InvoiceStatusEnum.DRAFT.value:
                    return Result.failure([f"Only Draft invoices can be posted. Current status: {invoice_to_post.status}."])

                if not invoice_to_post.vendor or not invoice_to_post.vendor.is_active:
                    return Result.failure(["Vendor is inactive or not found."])
                
                ap_account_id_from_vendor = invoice_to_post.vendor.payables_account_id
                ap_account_code_fallback = await self.configuration_service.get_config_value("SysAcc_DefaultAP", "2110")
                ap_account_final_id: Optional[int] = None

                if ap_account_id_from_vendor:
                    ap_acc_orm = await self.account_service.get_by_id(ap_account_id_from_vendor) 
                    if ap_acc_orm and ap_acc_orm.is_active: ap_account_final_id = ap_acc_orm.id
                    else: self.logger.warning(f"Vendor AP account ID {ap_account_id_from_vendor} is invalid/inactive for PI {invoice_to_post.invoice_no}. Falling back.")
                
                if not ap_account_final_id and ap_account_code_fallback:
                    fallback_ap_acc_orm = await self.account_service.get_by_code(ap_account_code_fallback)
                    if fallback_ap_acc_orm and fallback_ap_acc_orm.is_active: ap_account_final_id = fallback_ap_acc_orm.id
                
                if not ap_account_final_id:
                    return Result.failure([f"Could not determine a valid Accounts Payable account for PI {invoice_to_post.invoice_no}."])

                default_purchase_expense_code = await self.configuration_service.get_config_value("SysAcc_DefaultPurchaseExpense", "5100")
                default_inventory_asset_code = await self.configuration_service.get_config_value("SysAcc_DefaultInventoryAsset", "1130") 
                default_gst_input_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultGSTInput", "SYS-GST-INPUT")
                
                je_lines_data: List[JournalEntryLineData] = []
                
                je_lines_data.append(JournalEntryLineData(
                    account_id=ap_account_final_id, debit_amount=Decimal(0), credit_amount=invoice_to_post.total_amount,
                    description=f"A/P for P.Inv {invoice_to_post.invoice_no} from {invoice_to_post.vendor.name}",
                    currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate ))

                for line in invoice_to_post.lines:
                    debit_account_id_for_line: Optional[int] = None
                    product_type_for_line: Optional[ProductTypeEnum] = None
                    if line.product: product_type_for_line = ProductTypeEnum(line.product.product_type)
                    
                    if product_type_for_line == ProductTypeEnum.INVENTORY and line.product and line.product.inventory_account:
                        if line.product.inventory_account.is_active: debit_account_id_for_line = line.product.inventory_account.id
                        else: self.logger.warning(f"Product '{line.product.name}' inventory account '{line.product.inventory_account.code}' is inactive for PI {invoice_to_post.invoice_no}.")
                    elif line.product and line.product.purchase_account: 
                         if line.product.purchase_account.is_active: debit_account_id_for_line = line.product.purchase_account.id
                         else: self.logger.warning(f"Product '{line.product.name}' purchase account '{line.product.purchase_account.code}' is inactive for PI {invoice_to_post.invoice_no}.")
                    
                    if not debit_account_id_for_line: 
                        fallback_code = default_inventory_asset_code if product_type_for_line == ProductTypeEnum.INVENTORY else default_purchase_expense_code
                        fallback_acc = await self.account_service.get_by_code(fallback_code)
                        if not fallback_acc or not fallback_acc.is_active: return Result.failure([f"Default debit account '{fallback_code}' for line '{line.description}' is invalid/inactive."])
                        debit_account_id_for_line = fallback_acc.id
                    
                    if not debit_account_id_for_line: return Result.failure([f"Could not determine Debit GL account for line: {line.description}"])

                    je_lines_data.append(JournalEntryLineData(
                        account_id=debit_account_id_for_line, debit_amount=line.line_subtotal, credit_amount=Decimal(0), 
                        description=f"Purchase: {line.description[:100]} (P.Inv {invoice_to_post.invoice_no})",
                        currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate ))

                    if line.tax_amount and line.tax_amount != Decimal(0) and line.tax_code:
                        gst_gl_id_for_line: Optional[int] = None
                        line_tax_code_obj_orm = line.tax_code_obj 
                        if line_tax_code_obj_orm and line_tax_code_obj_orm.affects_account:
                            if line_tax_code_obj_orm.affects_account.is_active: gst_gl_id_for_line = line_tax_code_obj_orm.affects_account.id
                            else: self.logger.warning(f"Tax code '{line.tax_code}' affects account '{line_tax_code_obj_orm.affects_account.code}' is inactive. Falling back.")
                        
                        if not gst_gl_id_for_line and default_gst_input_acc_code: 
                            def_gst_input_acc = await self.account_service.get_by_code(default_gst_input_acc_code)
                            if not def_gst_input_acc or not def_gst_input_acc.is_active: return Result.failure([f"Default GST Input account '{default_gst_input_acc_code}' is invalid or inactive."])
                            gst_gl_id_for_line = def_gst_input_acc.id

                        if not gst_gl_id_for_line: return Result.failure([f"Could not determine GST Input account for tax on line: {line.description}"])
                        
                        je_lines_data.append(JournalEntryLineData(
                            account_id=gst_gl_id_for_line, debit_amount=line.tax_amount, credit_amount=Decimal(0),
                            description=f"GST Input ({line.tax_code}) for P.Inv {invoice_to_post.invoice_no}",
                            currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate ))
                
                je_dto = JournalEntryData(
                    journal_type=JournalTypeEnum.PURCHASE.value, entry_date=invoice_to_post.invoice_date,
                    description=f"Purchase Invoice {invoice_to_post.invoice_no} from {invoice_to_post.vendor.name}",
                    source_type="PurchaseInvoice", source_id=invoice_to_post.id, user_id=user_id, lines=je_lines_data
                )

                create_je_result = await self.app_core.journal_entry_manager.create_journal_entry(je_dto, session=session)
                if not create_je_result.is_success or not create_je_result.value: return Result.failure(["Failed to create JE for PI."] + create_je_result.errors)
                
                created_je: JournalEntry = create_je_result.value
                post_je_result = await self.app_core.journal_entry_manager.post_journal_entry(created_je.id, user_id, session=session)
                if not post_je_result.is_success: return Result.failure([f"JE (ID: {created_je.id}) created but failed to post."] + post_je_result.errors)

                for line in invoice_to_post.lines:
                    if line.product and ProductTypeEnum(line.product.product_type) == ProductTypeEnum.INVENTORY:
                        inv_movement = InventoryMovement(
                            product_id=line.product_id, movement_date=invoice_to_post.invoice_date,
                            movement_type=InventoryMovementTypeEnum.PURCHASE.value,
                            quantity=line.quantity, unit_cost=(line.line_subtotal / line.quantity if line.quantity else Decimal(0)),
                            total_cost=line.line_subtotal, reference_type='PurchaseInvoiceLine', reference_id=line.id,
                            created_by_user_id=user_id
                        )
                        await self.inventory_movement_service.save(inv_movement, session=session)
                
                invoice_to_post.status = InvoiceStatusEnum.APPROVED.value 
                invoice_to_post.journal_entry_id = created_je.id
                invoice_to_post.updated_by_user_id = user_id
                
                session.add(invoice_to_post) 
                await session.flush(); await session.refresh(invoice_to_post)
                self.logger.info(f"PI {invoice_to_post.invoice_no} (ID: {invoice_id}) posted. JE ID: {created_je.id}")
                return Result.success(invoice_to_post)

            except Exception as e: self.logger.error(f"Error posting PI ID {invoice_id}: {e}", exc_info=True); return Result.failure([f"Unexpected error posting PI: {str(e)}"])

    async def get_invoice_for_dialog(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        try: return await self.purchase_invoice_service.get_by_id(invoice_id)
        except Exception as e: self.logger.error(f"Error fetching PI ID {invoice_id} for dialog: {e}", exc_info=True); return None

    async def get_invoices_for_listing(self, vendor_id: Optional[int]=None, status:Optional[InvoiceStatusEnum]=None, start_date:Optional[date]=None, end_date:Optional[date]=None, page:int=1, page_size:int=50) -> Result[List[PurchaseInvoiceSummaryData]]:
        try:
            summaries = await self.purchase_invoice_service.get_all_summary(vendor_id=vendor_id, status=status, start_date=start_date, end_date=end_date, page=page, page_size=page_size)
            return Result.success(summaries)
        except Exception as e: self.logger.error(f"Error fetching PI listing: {e}", exc_info=True); return Result.failure([f"Failed to retrieve PI list: {str(e)}"])
```

---
**2. Updated File: `app/tax/tax_calculator.py`**
---
```python
# File: app/tax/tax_calculator.py
from decimal import Decimal
from typing import List, Optional, Any, TYPE_CHECKING

# REMOVED: from app.services.tax_service import TaxCodeService 
from app.utils.pydantic_models import TaxCalculationResultData, TransactionTaxData, TransactionLineTaxData
from app.models.accounting.tax_code import TaxCode as TaxCodeModel

if TYPE_CHECKING:
    from app.services.tax_service import TaxCodeService # ADDED

class TaxCalculator:
    def __init__(self, tax_code_service: "TaxCodeService"):
        self.tax_code_service = tax_code_service
    
    async def calculate_transaction_taxes(self, transaction_data: TransactionTaxData) -> List[dict]:
        results = []
        for line in transaction_data.lines:
            tax_result: TaxCalculationResultData = await self.calculate_line_tax(
                line.amount,
                line.tax_code,
                transaction_data.transaction_type,
                line.account_id 
            )
            results.append({ 
                'line_index': line.index,
                'tax_amount': tax_result.tax_amount,
                'tax_account_id': tax_result.tax_account_id,
                'taxable_amount': tax_result.taxable_amount
            })
        return results
    
    async def calculate_line_tax(self, amount: Decimal, tax_code_str: Optional[str], 
                                 transaction_type: str, account_id: Optional[int] = None) -> TaxCalculationResultData:
        result = TaxCalculationResultData(
            tax_amount=Decimal(0),
            tax_account_id=None,
            taxable_amount=amount
        )
        
        if not tax_code_str or abs(amount) < Decimal("0.01"):
            return result
        
        tax_code_info: Optional[TaxCodeModel] = await self.tax_code_service.get_tax_code(tax_code_str) # Use TYPE_CHECKING for TaxCodeModel
        if not tax_code_info:
            return result 
        
        if tax_code_info.tax_type == 'GST':
            return await self._calculate_gst(amount, tax_code_info, transaction_type)
        elif tax_code_info.tax_type == 'Withholding Tax':
            return await self._calculate_withholding_tax(amount, tax_code_info, transaction_type)
        return result
    
    async def _calculate_gst(self, amount: Decimal, tax_code_info: TaxCodeModel, transaction_type: str) -> TaxCalculationResultData:
        tax_rate = Decimal(str(tax_code_info.rate))
        net_amount = amount 
        tax_amount = net_amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=net_amount
        )
    
    async def _calculate_withholding_tax(self, amount: Decimal, tax_code_info: TaxCodeModel, transaction_type: str) -> TaxCalculationResultData:
        applicable_transaction_types = ['Purchase Payment', 'Expense Payment'] 
        if transaction_type not in applicable_transaction_types:
            return TaxCalculationResultData(
                tax_amount=Decimal(0), tax_account_id=None, taxable_amount=amount
            )
        
        tax_rate = Decimal(str(tax_code_info.rate))
        tax_amount = amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=amount
        )
```

---
**3. Updated File: `app/tax/gst_manager.py`**
---
```python
# File: app/tax/gst_manager.py
from typing import Optional, Any, TYPE_CHECKING, List, Dict
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta 
from decimal import Decimal

# REMOVED: from app.services.tax_service import TaxCodeService, GSTReturnService 
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService
# REMOVED: from app.services.core_services import CompanySettingsService 
from app.utils.result import Result
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, JournalEntryLineData, GSTTransactionLineDetail
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine # Keep specific model imports
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.common.enums import GSTReturnStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.utils.sequence_generator import SequenceGenerator
    from app.services.tax_service import TaxCodeService, GSTReturnService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.fiscal_period_service import FiscalPeriodService # ADDED
    from app.services.core_services import CompanySettingsService # ADDED


class GSTManager:
    def __init__(self, 
                 tax_code_service: "TaxCodeService", 
                 journal_service: "JournalService", 
                 company_settings_service: "CompanySettingsService", 
                 gst_return_service: "GSTReturnService",
                 account_service: "AccountService", 
                 fiscal_period_service: "FiscalPeriodService", 
                 sequence_generator: "SequenceGenerator", 
                 app_core: "ApplicationCore"): 
        self.tax_code_service = tax_code_service
        self.journal_service = journal_service
        self.company_settings_service = company_settings_service
        self.gst_return_service = gst_return_service
        self.account_service = account_service 
        self.fiscal_period_service = fiscal_period_service 
        self.sequence_generator = sequence_generator
        self.app_core = app_core

    async def prepare_gst_return_data(self, start_date: date, end_date: date, user_id: int) -> Result[GSTReturnData]:
        company_settings = await self.company_settings_service.get_company_settings()
        if not company_settings:
            return Result.failure(["Company settings not found."])

        std_rated_supplies = Decimal('0.00') 
        zero_rated_supplies = Decimal('0.00')  
        exempt_supplies = Decimal('0.00')     
        taxable_purchases = Decimal('0.00')   
        output_tax_calc = Decimal('0.00') 
        input_tax_calc = Decimal('0.00')  
        
        detailed_breakdown: Dict[str, List[GSTTransactionLineDetail]] = {
            "box1_standard_rated_supplies": [], "box2_zero_rated_supplies": [],
            "box3_exempt_supplies": [], "box5_taxable_purchases": [],
            "box6_output_tax_details": [], "box7_input_tax_details": []
        }
        
        posted_entries: List[JournalEntry] = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)

        for entry in posted_entries:
            for line in entry.lines:
                if not line.account or not line.tax_code_obj: continue

                account_orm: Account = line.account
                tax_code_orm: TaxCode = line.tax_code_obj
                
                line_net_value_for_gst_box: Decimal = Decimal('0.00')
                if account_orm.account_type == 'Revenue':
                    line_net_value_for_gst_box = line.credit_amount - line.debit_amount 
                elif account_orm.account_type in ['Expense', 'Asset']:
                    line_net_value_for_gst_box = line.debit_amount - line.credit_amount 

                if tax_code_orm.tax_type != 'GST' or abs(line_net_value_for_gst_box) < Decimal('0.01') and abs(line.tax_amount) < Decimal('0.01'):
                    continue

                transaction_detail = GSTTransactionLineDetail(
                    transaction_date=entry.entry_date,
                    document_no=entry.reference or entry.entry_no, 
                    entity_name=None, 
                    description=line.description or entry.description or "N/A",
                    account_code=account_orm.code,
                    account_name=account_orm.name,
                    net_amount=line_net_value_for_gst_box.quantize(Decimal("0.01")),
                    gst_amount=line.tax_amount.quantize(Decimal("0.01")),
                    tax_code_applied=tax_code_orm.code
                )

                if account_orm.account_type == 'Revenue':
                    if tax_code_orm.code == 'SR': 
                        std_rated_supplies += line_net_value_for_gst_box
                        output_tax_calc += line.tax_amount
                        detailed_breakdown["box1_standard_rated_supplies"].append(transaction_detail)
                        if line.tax_amount != Decimal(0):
                             detailed_breakdown["box6_output_tax_details"].append(transaction_detail)
                    elif tax_code_orm.code == 'ZR': 
                        zero_rated_supplies += line_net_value_for_gst_box
                        detailed_breakdown["box2_zero_rated_supplies"].append(transaction_detail)
                    elif tax_code_orm.code == 'ES': 
                        exempt_supplies += line_net_value_for_gst_box
                        detailed_breakdown["box3_exempt_supplies"].append(transaction_detail)
                    
                elif account_orm.account_type in ['Expense', 'Asset']:
                    if tax_code_orm.code == 'TX': 
                        taxable_purchases += line_net_value_for_gst_box
                        input_tax_calc += line.tax_amount
                        detailed_breakdown["box5_taxable_purchases"].append(transaction_detail)
                        if line.tax_amount != Decimal(0):
                            detailed_breakdown["box7_input_tax_details"].append(transaction_detail)
                    elif tax_code_orm.code == 'BL': 
                        taxable_purchases += line_net_value_for_gst_box
                        detailed_breakdown["box5_taxable_purchases"].append(transaction_detail)
        
        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc 

        temp_due_date = end_date + relativedelta(months=1)
        filing_due_date = temp_due_date + relativedelta(day=31) 

        return_data = GSTReturnData(
            return_period=f"{start_date.strftime('%d%m%Y')}-{end_date.strftime('%d%m%Y')}",
            start_date=start_date, end_date=end_date,
            filing_due_date=filing_due_date,
            standard_rated_supplies=std_rated_supplies.quantize(Decimal("0.01")),
            zero_rated_supplies=zero_rated_supplies.quantize(Decimal("0.01")),
            exempt_supplies=exempt_supplies.quantize(Decimal("0.01")),
            total_supplies=total_supplies.quantize(Decimal("0.01")), 
            taxable_purchases=taxable_purchases.quantize(Decimal("0.01")), 
            output_tax=output_tax_calc.quantize(Decimal("0.01")), 
            input_tax=input_tax_calc.quantize(Decimal("0.01")),   
            tax_adjustments=Decimal(0),
            tax_payable=tax_payable.quantize(Decimal("0.01")), 
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id,
            detailed_breakdown=detailed_breakdown
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        current_user_id = gst_return_data.user_id
        orm_return: GSTReturn
        core_data_dict = gst_return_data.model_dump(exclude={'id', 'user_id', 'detailed_breakdown'}, exclude_none=True)

        if gst_return_data.id: 
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            orm_return = existing_return
            for key, value in core_data_dict.items():
                if hasattr(orm_return, key):
                    setattr(orm_return, key, value)
            orm_return.updated_by_user_id = current_user_id
        else: 
            orm_return = GSTReturn(
                **core_data_dict,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
            if not orm_return.filing_due_date and orm_return.end_date: 
                 temp_due_date = orm_return.end_date + relativedelta(months=1)
                 orm_return.filing_due_date = temp_due_date + relativedelta(day=31)
        try:
            saved_return = await self.gst_return_service.save_gst_return(orm_return)
            return Result.success(saved_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save GST return: {str(e)}"])

    async def finalize_gst_return(self, return_id: int, submission_reference: str, submission_date: date, user_id: int) -> Result[GSTReturn]:
        gst_return = await self.gst_return_service.get_by_id(return_id)
        if not gst_return:
            return Result.failure([f"GST Return ID {return_id} not found."])
        if gst_return.status != GSTReturnStatusEnum.DRAFT.value:
            return Result.failure([f"GST Return must be in Draft status to be finalized. Current status: {gst_return.status}"])

        gst_return.status = GSTReturnStatusEnum.SUBMITTED.value
        gst_return.submission_date = submission_date
        gst_return.submission_reference = submission_reference
        gst_return.updated_by_user_id = user_id

        if gst_return.tax_payable != Decimal(0):
            gst_output_tax_acc_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultGSTOutput", "SYS-GST-OUTPUT")
            gst_input_tax_acc_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultGSTInput", "SYS-GST-INPUT")
            gst_control_acc_code = await self.app_core.configuration_service.get_config_value("SysAcc_GSTControl", "SYS-GST-CONTROL")
            
            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code) # type: ignore
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code) # type: ignore
            control_acc = await self.account_service.get_by_code(gst_control_acc_code) if gst_control_acc_code else None # type: ignore

            if not (output_tax_acc and input_tax_acc and control_acc):
                missing_accs = []
                if not output_tax_acc: missing_accs.append(str(gst_output_tax_acc_code))
                if not input_tax_acc: missing_accs.append(str(gst_input_tax_acc_code))
                if not control_acc: missing_accs.append(str(gst_control_acc_code))
                error_msg = f"Essential GST GL accounts not found: {', '.join(missing_accs)}. Cannot create settlement journal entry."
                self.app_core.logger.error(error_msg) # type: ignore
                try:
                    updated_return_no_je = await self.gst_return_service.save_gst_return(gst_return)
                    return Result.failure([f"GST Return finalized (ID: {updated_return_no_je.id}), but JE creation failed: " + error_msg])
                except Exception as e_save:
                    return Result.failure([f"Failed to finalize GST return and also failed to save it before JE creation: {str(e_save)}"] + [error_msg])

            lines: List[JournalEntryLineData] = []
            desc_period = f"GST for period {gst_return.start_date.strftime('%d/%m/%y')}-{gst_return.end_date.strftime('%d/%m/%y')}"
            
            if gst_return.output_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description=f"Clear Output Tax - {desc_period}"))
            if gst_return.input_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description=f"Clear Input Tax - {desc_period}"))
            
            if gst_return.tax_payable > Decimal(0): 
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable - {desc_period}"))
            elif gst_return.tax_payable < Decimal(0): 
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=abs(gst_return.tax_payable), credit_amount=Decimal(0), description=f"GST Refundable - {desc_period}"))
            
            if lines:
                if not hasattr(self.app_core, 'journal_entry_manager') or not self.app_core.journal_entry_manager:
                    return Result.failure(["Journal Entry Manager not available in Application Core. Cannot create GST settlement JE."])

                je_data = JournalEntryData(
                    journal_type="General", entry_date=submission_date, 
                    description=f"GST Settlement for period {gst_return.return_period}",
                    reference=f"GST F5 Finalized: {gst_return.submission_reference or gst_return.return_period}", 
                    user_id=user_id, lines=lines,
                    source_type="GSTReturnSettlement", source_id=gst_return.id
                )
                je_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.create_journal_entry(je_data) 
                if not je_result.is_success:
                    try:
                        updated_return_je_fail = await self.gst_return_service.save_gst_return(gst_return)
                        return Result.failure([f"GST Return finalized and saved (ID: {updated_return_je_fail.id}) but settlement JE creation failed."] + (je_result.errors or []))
                    except Exception as e_save_2:
                         return Result.failure([f"Failed to finalize GST return and also failed during JE creation and subsequent save: {str(e_save_2)}"] + (je_result.errors or []))
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    post_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)
                    if not post_result.is_success:
                        self.app_core.logger.warning(f"GST Settlement JE (ID: {je_result.value.id}) created but failed to auto-post: {post_result.errors}") # type: ignore
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save finalized GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])
```

---
**4. Updated File: `app/tax/income_tax_manager.py`**
---
```python
# File: app/tax/income_tax_manager.py
from typing import TYPE_CHECKING 
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.account_service import AccountService # ADDED
    from app.services.fiscal_period_service import FiscalPeriodService # ADDED


class IncomeTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.account_service: "AccountService" = app_core.account_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.fiscal_period_service: "FiscalPeriodService" = app_core.fiscal_period_service # type: ignore
        print("IncomeTaxManager initialized (stub).")
    
    async def calculate_provisional_tax(self, fiscal_year_id: int):
        print(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        return {"provisional_tax_payable": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int):
        print(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        return {"company_name": "Example Pte Ltd", "revenue": 100000.00, "profit_before_tax": 20000.00}
```

---
**5. Updated File: `app/tax/withholding_tax_manager.py`**
---
```python
# File: app/tax/withholding_tax_manager.py
from typing import TYPE_CHECKING
# REMOVED: from app.services.tax_service import TaxCodeService

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.tax_service import TaxCodeService # ADDED

class WithholdingTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.tax_code_service: "TaxCodeService" = app_core.tax_code_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        print("WithholdingTaxManager initialized (stub).")

    async def generate_s45_form_data(self, wht_certificate_id: int):
        print(f"Generating S45 form data for WHT certificate ID {wht_certificate_id} (stub).")
        return {"s45_field_1": "data", "s45_field_2": "more_data"}

    async def record_wht_payment(self, certificate_id: int, payment_date: str, reference: str):
        print(f"Recording WHT payment for certificate {certificate_id} (stub).")
        return True
```

---
**6. Updated File: `app/reporting/financial_statement_generator.py`**
---
```python
# File: app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import date, timedelta 
from decimal import Decimal

# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.journal_service import JournalService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService
# REMOVED: from app.services.tax_service import TaxCodeService 
# REMOVED: from app.services.core_services import CompanySettingsService 
# REMOVED: from app.services.accounting_services import AccountTypeService, DimensionService 
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.account_service import AccountService # ADDED
    from app.services.journal_service import JournalService # ADDED
    from app.services.fiscal_period_service import FiscalPeriodService # ADDED
    from app.services.tax_service import TaxCodeService # ADDED
    from app.services.core_services import CompanySettingsService # ADDED
    from app.services.accounting_services import AccountTypeService, DimensionService # ADDED


class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: "AccountService", 
                 journal_service: "JournalService", 
                 fiscal_period_service: "FiscalPeriodService", 
                 account_type_service: "AccountTypeService", 
                 tax_code_service: Optional["TaxCodeService"] = None, 
                 company_settings_service: Optional["CompanySettingsService"] = None,
                 dimension_service: Optional["DimensionService"] = None 
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self.dimension_service = dimension_service 
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             self._account_type_map_cache = {at.category: at for at in ats} 
        return self._account_type_map_cache

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        result_list = []; acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date); display_balance = balance_value 
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_balance = -balance_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_balance})
        return result_list

    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        result_list = []; acc_type_map = await self._get_account_type_map()
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date); display_activity = activity_value
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_activity = -activity_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_activity})
        return result_list

    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); assets_orm = [a for a in accounts if a.account_type == 'Asset']; liabilities_orm = [a for a in accounts if a.account_type == 'Liability']; equity_orm = [a for a in accounts if a.account_type == 'Equity']
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date); liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date); equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date: comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date); comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date); comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)
        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]; liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]; equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date: comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None; comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None; comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None
        total_assets = sum(a['balance'] for a in asset_accounts); total_liabilities = sum(a['balance'] for a in liability_accounts); total_equity = sum(a['balance'] for a in equity_accounts)
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None; comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None; comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None
        return {'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date, 'comparative_date': comparative_date,'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},'total_liabilities_equity': total_liabilities + total_equity,'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")}

    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); revenues_orm = [a for a in accounts if a.account_type == 'Revenue']; expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date); expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end: comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end); comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)
        total_revenue = sum(a['balance'] for a in revenue_accounts); total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None; comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None
        return {'title': 'Profit & Loss Statement', 'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'start_date': start_date, 'end_date': end_date, 'comparative_start': comparative_start, 'comparative_end': comparative_end,'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},'net_profit': net_profit, 'comparative_net_profit': comp_net_profit}

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); debit_accounts_list, credit_accounts_list = [], []; total_debits_val, total_credits_val = Decimal(0), Decimal(0) 
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue
            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if is_debit_nature: 
                if raw_balance >= Decimal(0): debit_accounts_list.append(account_data); total_debits_val += raw_balance
                else: account_data['balance'] = abs(raw_balance); credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
                else: account_data['balance'] = raw_balance; debit_accounts_list.append(account_data); total_debits_val += raw_balance
        debit_accounts_list.sort(key=lambda a: a['code']); credit_accounts_list.sort(key=lambda a: a['code'])
        return {'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date,'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,'total_debits': total_debits_val, 'total_credits': total_credits_val,'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")}

    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: 
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value) 
        if not fiscal_year_obj: raise ValueError(f"Fiscal year definition for {year_int_value} not found.")
        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date); net_profit = pl_data['net_profit']
        adjustments = []; tax_effect = Decimal(0)
        tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')
        for account in tax_adj_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            adj_is_addition = activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0)
            adjustments.append({'id': account.id, 'code': account.code, 'name': account.name, 'amount': activity, 'is_addition': adj_is_addition})
            tax_effect += activity 
        taxable_income = net_profit + tax_effect
        return {'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', 'report_date_description': f"For Financial Year Ended {fiscal_year_obj.end_date.strftime('%d %b %Y')}",'year': year_int_value, 'fiscal_year_start': start_date, 'fiscal_year_end': end_date,'net_profit': net_profit, 'adjustments': adjustments, 'tax_effect': tax_effect, 'taxable_income': taxable_income}

    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        if not self.company_settings_service or not self.tax_code_service: raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")
        company = await self.company_settings_service.get_company_settings();
        if not company: raise ValueError("Company settings not found.")
        report_data: Dict[str, Any] = {'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'company_name': company.company_name,'gst_registration_no': company.gst_registration_no,'period_start': start_date, 'period_end': end_date,'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)}
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                line_net_amount = (line.debit_amount if line.debit_amount > Decimal(0) else line.credit_amount) 
                tax_on_line = line.tax_amount if line.tax_amount is not None else Decimal(0)
                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR': report_data['standard_rated_supplies'] += line_net_amount; report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR': report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES': report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': report_data['taxable_purchases'] += line_net_amount; report_data['input_tax'] += tax_on_line
                    elif tax_code_info.code == 'BL': report_data['taxable_purchases'] += line_net_amount 
        report_data['total_supplies'] = (report_data['standard_rated_supplies'] + report_data['zero_rated_supplies'] + report_data['exempt_supplies'])
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        return report_data

    async def generate_general_ledger(self, account_id: int, start_date: date, end_date: date,
                                      dimension1_id: Optional[int] = None, 
                                      dimension2_id: Optional[int] = None) -> Dict[str, Any]:
        account_orm = await self.account_service.get_by_id(account_id)
        if not account_orm:
            raise ValueError(f"Account with ID {account_id} not found.")

        ob_date = start_date - timedelta(days=1)
        opening_balance = await self.journal_service.get_account_balance(account_id, ob_date)

        lines: List[JournalEntryLine] = await self.journal_service.get_posted_lines_for_account_in_range(
            account_id, start_date, end_date, dimension1_id, dimension2_id 
        )

        transactions_data = []
        current_balance = opening_balance
        for line in lines:
            if not line.journal_entry: continue 
            movement = line.debit_amount - line.credit_amount
            current_balance += movement
            transactions_data.append({
                "date": line.journal_entry.entry_date, "entry_no": line.journal_entry.entry_no,
                "je_description": line.journal_entry.description or "", "line_description": line.description or "",
                "debit": line.debit_amount, "credit": line.credit_amount, "balance": current_balance,
                "dim1_id": line.dimension1_id, "dim2_id": line.dimension2_id 
            })
        closing_balance = current_balance
        
        report_desc = f"For Account: {account_orm.code} - {account_orm.name} from {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
        if dimension1_id and self.dimension_service:
            dim1 = await self.dimension_service.get_by_id(dimension1_id)
            if dim1: report_desc += f" (Dim1: {dim1.dimension_type}-{dim1.code})"
        if dimension2_id and self.dimension_service:
            dim2 = await self.dimension_service.get_by_id(dimension2_id)
            if dim2: report_desc += f" (Dim2: {dim2.dimension_type}-{dim2.code})"


        return {
            "title": "General Ledger", "report_date_description": report_desc,
            "account_code": account_orm.code, "account_name": account_orm.name,
            "start_date": start_date, "end_date": end_date,
            "opening_balance": opening_balance, "transactions": transactions_data,
            "closing_balance": closing_balance
        }
```

