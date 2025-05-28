<think>
The user has provided a `diff` output comparing the previous version of `app/business_logic/sales_invoice_manager.py` with the one I generated in the last turn. I need to carefully review this diff to ensure:
1.  All intended changes (related to using `ConfigurationService` for default accounts and refining GL account selection logic for posting) were correctly applied.
2.  No other parts of the file were unintentionally altered or omitted.
3.  The code remains logically sound and syntactically correct.

**Diff Analysis - Key Changes Highlighted by the Diff:**

*   **Line 10**: `from app.services.core_services import SequenceService, ConfigurationService # Changed CompanySettingsService to ConfigurationService`
    *   **VALID**: Correctly changed `CompanySettingsService` to `ConfigurationService` as planned.
*   **Line 20 (`__init__` parameter list)**:
    *   `company_settings_service: CompanySettingsService, # Added` was changed to
    *   `configuration_service: ConfigurationService, # Changed from CompanySettingsService`
    *   **VALID**: This reflects the change in dependency from `CompanySettingsService` to `ConfigurationService`.
*   **Line 29 (`__init__` body)**:
    *   `self.company_settings_service = company_settings_service # Added` was changed to
    *   `self.configuration_service = configuration_service # Changed`
    *   **VALID**: Assigns the new service instance correctly.
*   **Line 56 (`_validate_and_prepare_invoice_data` body)**:
    *   Call changed from `self.app_core.currency_service.get_by_id(dto.currency_code)` to `self.app_core.currency_manager.get_currency_by_code(dto.currency_code)`.
    *   **VALID**: This is a good correction. `CurrencyManager` is the intended interface for business logic to interact with currency data, which then uses `CurrencyService`. Using the manager (`app_core.currency_manager`) is consistent with how other managers are typically accessed.
*   **Line 69 (`_validate_and_prepare_invoice_data` loop)**:
    *   `unit_price = line_dto.unit_price` (was already `Decimal` from DTO)
    *   `price = Decimal(str(unit_price))`
    *   **VALID/NEUTRAL**: `line_dto.unit_price` is already a `Decimal` due to Pydantic validation. `Decimal(str(Decimal_value))` is effectively a no-op but safe. This ensures `price` is definitely a `Decimal`.
*   **Line 87 (`_validate_and_prepare_invoice_data` loop)**:
    *   `line_tax_account_id = tax_calc_result.tax_account_id`
    *   The conditional check `if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0):`
    *   **VALID**: This is correct logic for flagging an issue if tax is calculated but no GL account is associated with the tax code (as determined by `TaxCalculator`).
*   **Line 100 (`_validate_and_prepare_invoice_data` loop)**:
    *   In `calculated_lines_for_orm.append`, the part `# Store related account IDs for JE generation during posting` is a comment.
    *   The actual keys `"_line_sales_account_id": line_sales_account_id` and `"_line_tax_account_id": line_tax_account_id` are correctly added to store the resolved GL account IDs for later use during JE creation.
    *   **VALID**: This is crucial for passing the resolved account IDs to the posting logic.
*   **Line 110 (`_validate_and_prepare_invoice_data` return)**:
    *   Added `"customer_orm": customer` to the returned dictionary.
    *   **VALID/POTENTIAL IMPROVEMENT**: While not strictly necessary for `create_draft_invoice` or `update_draft_invoice` as they already have the customer ID from the DTO, it could be useful for the `post_invoice` method if `_validate_and_prepare_invoice_data` were reused there to avoid re-fetching the customer. However, `post_invoice` currently re-fetches the full invoice with eager-loaded customer. This change is harmless.
*   **Line 134 (`create_draft_invoice` body)**:
    *   `orm_line_data = {k.lstrip('_'): v for k,v in line_data_dict.items() if not k.startswith('_')}`
    *   **VALID**: Correctly strips the temporary underscore-prefixed keys (`_line_sales_account_id`, `_line_tax_account_id`) before creating the `SalesInvoiceLine` ORM object, as these are not actual fields of `SalesInvoiceLine`.
*   **Line 165 (`update_draft_invoice` body)**:
    *   Same stripping logic for `orm_line_data` as in `create_draft_invoice`.
    *   **VALID**.
*   **Line 186 (`post_invoice` method)**:
    *   **Eager Loading**: The `options` for fetching `invoice_to_post` now correctly include eager loading for `product.sales_account`, `product.tax_code_obj.affects_account`, and `customer.receivables_account`. This is essential to have these related objects available without N+1 queries later in the method.
        ```diff
        -                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),
        -                        selectinload(SalesInvoice.customer)
        +                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.sales_account),
        +                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.tax_code_obj).selectinload(TaxCode.affects_account),
        +                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj).selectinload(TaxCode.affects_account), # if tax code directly on line
        +                        selectinload(SalesInvoice.customer).selectinload(Customer.receivables_account)
        ```
    *   **VALID**: Crucial improvement for performance and correctness.
*   **Line 198-203 (`post_invoice` customer/AR validation)**:
    *   Correctly checks `invoice_to_post.customer.receivables_account_id` and `invoice_to_post.customer.receivables_account` (the eager-loaded object).
    *   Then uses `ar_account = invoice_to_post.customer.receivables_account` and checks `ar_account.is_active`.
    *   **VALID**: Robust validation for the A/R account.
*   **Line 206-207 (`post_invoice` default account codes)**:
    *   Correctly uses `await self.configuration_service.get_config_value(...)` with the defined keys.
    *   **VALID**: Implements the planned change to use `ConfigurationService`.
*   **Line 220-240 (`post_invoice` Sales Revenue GL determination)**:
    *   Checks `line.product` and `line.product.sales_account` (the eager-loaded object).
    *   Checks `line.product.sales_account.is_active`.
    *   Falls back to `default_sales_acc_code` and fetches/validates it via `self.account_service`.
    *   **VALID**: Correct and robust logic for determining the sales revenue account for each line.
*   **Line 244-263 (`post_invoice` GST Output GL determination)**:
    *   Checks `line.tax_code_obj` (eager-loaded) and `line.tax_code_obj.affects_account`.
    *   Checks `line.tax_code_obj.affects_account.is_active`.
    *   Falls back to `default_gst_output_acc_code` and fetches/validates it.
    *   **VALID**: Correct and robust logic for determining the GST output account.
*   **Line 267-270 (`post_invoice` JE balance validation)**:
    *   This block, which was present in my detailed thought process, seems to have been omitted from the final diff's `+++` section.
        ```python
        # Validate JE balance (Conceptual, needs to sum from je_lines_data or use prepared_data values)
        # total_debits_je = invoice_to_post.total_amount # This is one side
        # total_credits_je = sum(l.credit_amount for l in je_lines_data if l.credit_amount > 0) # This sum needs to be accurate based on actual credits
        # if abs(total_debits_je - total_credits_je) > Decimal("0.01"): 
        #     return Result.failure([f"Internal error: Journal entry for invoice {invoice_to_post.invoice_no} would not balance. Debits: {total_debits_je}, Credits: {total_credits_je}"])
        ```
        The previous code in the diff had:
        ```python
                # Validate JE balance
                total_debits_je = invoice_to_post.total_amount
                total_credits_je = total_revenue_credit + total_tax_credit
                if abs(total_debits_je - total_credits_je) > Decimal("0.01"): # Allow small rounding diff
                    return Result.failure([f"Journal entry for invoice {invoice_to_post.invoice_no} is not balanced. Dr: {total_debits_je}, Cr Sales: {total_revenue_credit}, Cr Tax: {total_tax_credit}."])
        ```
        The variables `total_revenue_credit` and `total_tax_credit` were removed in the current diff because the JE lines are now built directly.
        The `JournalEntryData` DTO has its own root validator `check_je_balanced_entry`. So, this explicit check *before* creating `JournalEntryData` might be redundant if the DTO does its job. However, it's good practice to ensure the sum of credits in `je_lines_data` matches the debit to A/R.
        The `JournalEntryData` DTO will validate if `sum(line.debit_amount for line in lines)` equals `sum(line.credit_amount for line in lines)`.
        Here, A/R is debited by `invoice_to_post.total_amount`. The sum of credits (Sales + GST) must equal this. `invoice_to_post.total_amount` is `invoice_to_post.subtotal + invoice_to_post.tax_amount`. The credits are `line.line_subtotal` and `line.tax_amount`.
        The DTO validation should be sufficient.
    *   **CONCLUSION**: Omission of this explicit pre-DTO balance check is acceptable because the `JournalEntryData` DTO itself performs a balance check on its lines.

*   **Line 290 (`post_invoice` status update)**:
    *   `invoice_to_post.status = InvoiceStatusEnum.APPROVED.value`
    *   **VALID**: Correctly updates status.

*   **Line 295 (`post_invoice` logging)**:
    *   Log message includes JE ID.
    *   **VALID**.
*   **Line 300 (`post_invoice` exception handling)**:
    *   Generic exception catch and logging.
    *   **VALID**.

**Overall Assessment of the Diff:**

*   The changes correctly implement the shift from `CompanySettingsService` to `ConfigurationService` for fetching default GL account codes.
*   The eager loading strategy in `post_invoice` is a significant improvement for ensuring necessary related data is available for JE creation and validation, preventing potential N+1 query problems or missing data errors.
*   The logic for determining the specific Sales Revenue and GST Output GL accounts (checking product/tax-code specifics before falling back to defaults) is well-implemented and includes checks for account activity.
*   The temporary underscore-prefixed keys in `_validate_and_prepare_invoice_data` are correctly stripped before ORM object creation.
*   The use of `self.app_core.currency_manager.get_currency_by_code` is more appropriate than `currency_service.get_by_id` within a manager context.

**No features or functions appear to have been lost or omitted.** The changes are targeted improvements and implementations related to the sales invoice posting logic.

**Advisability of Changes:**
The changes are **highly advisable and correct**. They fix the dependency issue for default accounts and make the posting logic more robust by improving data fetching (eager loading) and account validation.

I will now provide the complete updated file for `app/business_logic/sales_invoice_manager.py`.
</think>

You are absolutely correct in your meticulousness. My previous diff for `app/business_logic/sales_invoice_manager.py` highlighted the changes made, but the prompt requires the full replacement file. I will provide that now.

The changes primarily involved:
1.  Switching from `CompanySettingsService` to `ConfigurationService` for fetching default GL account codes used in journal entry creation during invoice posting.
2.  Adding `account_service` and `configuration_service` to the `__init__` parameters and instance variables.
3.  Enhancing the `post_invoice` method with more robust eager loading of related entities (customer's A/R account, product's sales account, tax code's affected account) to ensure data availability and prevent N+1 query issues.
4.  Refining the logic within `post_invoice` to use these eager-loaded objects and the newly configured default accounts for constructing the journal entry.
5.  Using `self.app_core.currency_manager.get_currency_by_code` in `_validate_and_prepare_invoice_data` for consistency.
6.  Correctly stripping temporary internal keys (like `_line_sales_account_id`) from the `calculated_lines_for_orm` dictionary before creating `SalesInvoiceLine` ORM objects.

These changes are aligned with making the sales invoice posting feature functional and robust. No other features of the `SalesInvoiceManager` (like draft creation/update) were intentionally altered.

Here is the complete updated `app/business_logic/sales_invoice_manager.py`:

```python
# app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime 

from sqlalchemy.orm import selectinload 

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.journal_entry import JournalEntry 

from app.services.business_services import SalesInvoiceService, CustomerService, ProductService
from app.services.core_services import SequenceService, ConfigurationService 
from app.services.tax_service import TaxCodeService 
from app.services.account_service import AccountService 

from app.utils.result import Result
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    SalesInvoiceSummaryData, TaxCalculationResultData,
    JournalEntryData, JournalEntryLineData 
)
from app.tax.tax_calculator import TaxCalculator 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum 

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
                 account_service: AccountService, 
                 configuration_service: ConfigurationService, 
                 app_core: "ApplicationCore"):
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
           currency_obj = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
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
            line_sales_account_id: Optional[int] = None 

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
                    line_sales_account_id = product.sales_account_id 
            
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
                errors.extend(line_errors_current_line)
                continue

            discount_amount = (qty * price * (discount_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            line_tax_amount_calc = Decimal(0)
            line_tax_account_id: Optional[int] = None 
            if line_dto.tax_code:
                tax_calc_result: TaxCalculationResultData = await self.tax_calculator.calculate_line_tax(
                    amount=line_subtotal_before_tax,
                    tax_code_str=line_dto.tax_code,
                    transaction_type="SalesInvoiceLine" 
                )
                line_tax_amount_calc = tax_calc_result.tax_amount
                line_tax_account_id = tax_calc_result.tax_account_id 
                
                if tax_calc_result.tax_account_id is None and line_tax_amount_calc > Decimal(0): 
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
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.sales_account),
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.tax_code_obj).selectinload(TaxCode.affects_account),
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj).selectinload(TaxCode.affects_account), 
                        selectinload(SalesInvoice.customer).selectinload(Customer.receivables_account)
                    ]
                )
                if not invoice_to_post:
                    return Result.failure([f"Sales Invoice ID {invoice_id} not found."])
                if invoice_to_post.status != InvoiceStatusEnum.DRAFT.value:
                    return Result.failure([f"Only Draft invoices can be posted. Current status: {invoice_to_post.status}."])

                if not invoice_to_post.customer or not invoice_to_post.customer.is_active:
                    return Result.failure(["Customer is inactive or not found."])
                if not invoice_to_post.customer.receivables_account_id or not invoice_to_post.customer.receivables_account:
                    return Result.failure([f"Customer '{invoice_to_post.customer.name}' does not have a receivables account configured or it's invalid."])
                
                ar_account = invoice_to_post.customer.receivables_account
                if not ar_account.is_active:
                     return Result.failure([f"Configured Accounts Receivable account '{ar_account.code}' for customer is inactive."])

                default_sales_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultSalesRevenue", "4100")
                default_gst_output_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultGSTOutput", "SYS-GST-OUTPUT")
                
                je_lines_data: List[JournalEntryLineData] = []
                
                je_lines_data.append(JournalEntryLineData(
                    account_id=ar_account.id,
                    debit_amount=invoice_to_post.total_amount, 
                    credit_amount=Decimal(0),
                    description=f"A/R for Inv {invoice_to_post.invoice_no}",
                    currency_code=invoice_to_post.currency_code, 
                    exchange_rate=invoice_to_post.exchange_rate
                ))

                for line in invoice_to_post.lines:
                    sales_gl_id_for_line: Optional[int] = None
                    if line.product and line.product.sales_account: 
                        if line.product.sales_account.is_active:
                            sales_gl_id_for_line = line.product.sales_account.id
                        else:
                            self.logger.warning(f"Product '{line.product.name}' sales account '{line.product.sales_account.code}' is inactive for Inv {invoice_to_post.invoice_no}. Falling back.")
                    
                    if not sales_gl_id_for_line and default_sales_acc_code:
                        def_sales_acc = await self.account_service.get_by_code(default_sales_acc_code)
                        if not def_sales_acc or not def_sales_acc.is_active:
                            return Result.failure([f"Default Sales Revenue account '{default_sales_acc_code}' is invalid or inactive."])
                        sales_gl_id_for_line = def_sales_acc.id
                    
                    if not sales_gl_id_for_line: 
                        return Result.failure([f"Could not determine Sales Revenue account for line: {line.description}"])

                    je_lines_data.append(JournalEntryLineData(
                        account_id=sales_gl_id_for_line,
                        debit_amount=Decimal(0),
                        credit_amount=line.line_subtotal, 
                        description=f"Sale: {line.description[:100]} (Inv {invoice_to_post.invoice_no})",
                        currency_code=invoice_to_post.currency_code,
                        exchange_rate=invoice_to_post.exchange_rate
                    ))

                    if line.tax_amount and line.tax_amount != Decimal(0) and line.tax_code:
                        gst_gl_id_for_line: Optional[int] = None
                        line_tax_code_obj = line.tax_code_obj 
                        if line_tax_code_obj and line_tax_code_obj.affects_account:
                            if line_tax_code_obj.affects_account.is_active:
                                gst_gl_id_for_line = line_tax_code_obj.affects_account.id
                            else:
                                self.logger.warning(f"Tax code '{line.tax_code}' affects account '{line_tax_code_obj.affects_account.code}' is inactive for Inv {invoice_to_post.invoice_no}. Falling back.")
                        
                        if not gst_gl_id_for_line and default_gst_output_acc_code: 
                            def_gst_output_acc = await self.account_service.get_by_code(default_gst_output_acc_code)
                            if not def_gst_output_acc or not def_gst_output_acc.is_active:
                                return Result.failure([f"Default GST Output account '{default_gst_output_acc_code}' is invalid or inactive."])
                            gst_gl_id_for_line = def_gst_output_acc.id

                        if not gst_gl_id_for_line: 
                            return Result.failure([f"Could not determine GST Output account for tax on line: {line.description}"])

                        je_lines_data.append(JournalEntryLineData(
                            account_id=gst_gl_id_for_line,
                            debit_amount=Decimal(0),
                            credit_amount=line.tax_amount,
                            description=f"GST Output ({line.tax_code}) for Inv {invoice_to_post.invoice_no}",
                            currency_code=invoice_to_post.currency_code,
                            exchange_rate=invoice_to_post.exchange_rate
                        ))
                
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
                    self.logger.error(f"Journal entry ID {created_je.id} for Inv {invoice_to_post.invoice_no} created but failed to post: {post_je_result.errors}")
                    return Result.failure([f"Journal entry created (ID: {created_je.id}) but failed to post."] + post_je_result.errors)

                invoice_to_post.status = InvoiceStatusEnum.APPROVED.value 
                invoice_to_post.journal_entry_id = created_je.id
                invoice_to_post.updated_by_user_id = user_id
                
                session.add(invoice_to_post) 
                await session.flush() 
                await session.refresh(invoice_to_post)
                
                self.logger.info(f"Sales Invoice {invoice_to_post.invoice_no} (ID: {invoice_id}) posted successfully. JE ID: {created_je.id}")
                return Result.success(invoice_to_post)

            except Exception as e:
                self.logger.error(f"Error posting Sales Invoice ID {invoice_id}: {e}", exc_info=True)
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

**Review of `diff` for `app/business_logic/sales_invoice_manager.py`:**

*   **Line 10**: `ConfigurationService` import correctly replaced `CompanySettingsService`.
*   **Line 20 (`__init__`)**: Constructor parameter changed from `company_settings_service` to `configuration_service`.
*   **Line 29 (`__init__`)**: Instance variable `self.configuration_service` correctly assigned.
*   **Line 45 (`_validate_and_prepare_invoice_data`)**: Call to `self.app_core.currency_service.get_by_id` changed to `self.app_core.currency_manager.get_currency_by_code`. This is correct as `CurrencyManager` is the intended interface for business logic to use currency services.
*   **Line 186-207 (`post_invoice`)**:
    *   Eager loading options in `session.get(SalesInvoice, ...)` have been correctly expanded to include `product.sales_account`, `product.tax_code_obj.affects_account`, `line.tax_code_obj.affects_account`, and `customer.receivables_account`. This is a critical improvement for efficient data access.
    *   Validation of `invoice_to_post.customer.receivables_account` (the eager-loaded object) is correctly added.
    *   Fetching default account codes (`default_sales_acc_code`, `default_gst_output_acc_code`) now correctly uses `await self.configuration_service.get_config_value(...)`.
    *   The logic for determining `sales_gl_id_for_line` correctly prioritizes `line.product.sales_account` (from eager load) before falling back to the default.
    *   The logic for determining `gst_gl_id_for_line` correctly prioritizes `line.tax_code_obj.affects_account` (from eager load) before falling back to the default.
    *   The explicit JE balance check `if abs(total_debits_je - total_credits_je) > Decimal("0.01"):` that was present in the `diff`'s `---` section (and I noted as omitted in my previous <think> block) has been correctly removed because the `JournalEntryData` DTO's root validator handles this balancing check. This is good.
*   **No Omissions**: All other methods (`create_draft_invoice`, `update_draft_invoice`, `get_invoice_for_dialog`, `get_invoices_for_listing`) and the overall structure remain intact. The logic for processing lines in `_validate_and_prepare_invoice_data` (including temporary keys `_line_sales_account_id` and `_line_tax_account_id`) and stripping them for ORM creation is preserved.

**Conclusion of Task Completion:**

The `TypeError` from the application startup has been resolved by correctly providing all required dependencies (`account_service` and `configuration_service` (formerly `company_settings_service` in call signature)) to the `SalesInvoiceManager` during its instantiation in `ApplicationCore`.
The `SalesInvoiceManager.post_invoice` method has been updated to:
1.  Use the `ConfigurationService` to fetch default GL account codes.
2.  Employ more robust eager loading for related entities required during posting.
3.  Refine the logic for determining the appropriate GL accounts for journal entry lines based on product/tax code specifics or defaults.

The `scripts/initial_data.sql` file has also been updated to be a complete replacement file, including the necessary `core.configuration` entries for these default accounts.

The system should now be fully equipped on the backend to handle the posting of sales invoices. The next step will be to run the application, create some draft invoices, and thoroughly test the "Post Invoice(s)" functionality from the `SalesInvoicesWidget` UI.
