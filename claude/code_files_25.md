<think>
The application is encountering another `ImportError` due to a circular import. This time, the cycle involves `app/core/application_core.py` and `app/tax/gst_manager.py`.

**Error Analysis:**

The traceback shows:
`ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core' (most likely due to a circular import) (/cdrom/project/SG-Bookkeeper/app/core/application_core.py)`

This specific error is raised when `app/tax/gst_manager.py` tries to import `ApplicationCore`:
```
File "/cdrom/project/SG-Bookkeeper/app/core/application_core.py", line 24, in <module>
    from app.tax.gst_manager import GSTManager  # ApplicationCore imports GSTManager
  File "/cdrom/project/SG-Bookkeeper/app/tax/__init__.py", line 3, in <module>
    from .gst_manager import GSTManager
  File "/cdrom/project/SG-Bookkeeper/app/tax/gst_manager.py", line 16, in <module>
    from app.core.application_core import ApplicationCore # GSTManager imports ApplicationCore
```

**The Circular Import Path:**
1.  `app/core/application_core.py` imports `GSTManager` from `app/tax/gst_manager.py`.
2.  `app/tax/gst_manager.py` then tries to import `ApplicationCore` from `app/core/application_core.py`.

This creates the import loop.

**Solution Approach:**
Just like before, the solution is to use forward references for type hinting in the module that is lower in the dependency chain or is being imported by `ApplicationCore`. In this case, `GSTManager` needs to type-hint `ApplicationCore` using a string literal and the `if TYPE_CHECKING:` guard.

**Files to be Updated:**
1.  `app/tax/gst_manager.py`: Modify the import of `ApplicationCore` and the type hint for the `app_core` parameter in its `__init__` method.

The `project_file_structure.txt` indicates `app/tax/income_tax_manager.py` and `app/tax/withholding_tax_manager.py` also exist and were provided. These also import `ApplicationCore` at the top level:

`app/tax/income_tax_manager.py`:
```python
from app.core.application_core import ApplicationCore
# ...
class IncomeTaxManager:
    def __init__(self, app_core: ApplicationCore): # Direct type hint
        # ...
```

`app/tax/withholding_tax_manager.py`:
```python
from app.core.application_core import ApplicationCore
# ...
class WithholdingTaxManager:
    def __init__(self, app_core: ApplicationCore): # Direct type hint
        # ...
```

Since `ApplicationCore` also imports from `app.tax.__init__` (which then imports these managers), these files will also need the forward reference treatment for `ApplicationCore`.

**Plan:**
1.  Modify `app/tax/gst_manager.py`:
    *   Remove `from app.core.application_core import ApplicationCore`.
    *   Add `from typing import TYPE_CHECKING`.
    *   Add `if TYPE_CHECKING: from app.core.application_core import ApplicationCore`.
    *   Change `app_core: ApplicationCore` to `app_core: "ApplicationCore"` in the `__init__` signature.
2.  Modify `app/tax/income_tax_manager.py` similarly.
3.  Modify `app/tax/withholding_tax_manager.py` similarly.

The file `app/tax/tax_calculator.py` was also provided but does *not* import `ApplicationCore`, so it doesn't need changes for this specific issue.

Let's prepare the updated versions of the three tax manager files.
</think>

You've hit another circular import! This is common as different parts of a complex application start referencing each other.

**Error Analysis:**

The traceback is clear:
`ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core' (most likely due to a circular import) (/cdrom/project/SG-Bookkeeper/app/core/application_core.py)`

This happens because:
1.  `app/core/application_core.py` (line 24) imports `GSTManager` from `app.tax.gst_manager` (via `app/tax/__init__.py`).
2.  Then, `app/tax/gst_manager.py` (line 16) tries to import `ApplicationCore` from `app.core.application_core`.

This creates the cycle: `application_core` -> `gst_manager` -> `application_core`.

**Solution:**

As with the previous circular import errors, we'll use forward references for type hinting in the modules that are imported by `ApplicationCore`. In this case, `GSTManager`, `IncomeTaxManager`, and `WithholdingTaxManager` all import `ApplicationCore` for type hinting their `app_core` parameter.

**Files to be Updated:**

1.  `app/tax/gst_manager.py`
2.  `app/tax/income_tax_manager.py`
3.  `app/tax/withholding_tax_manager.py`

We will apply the `if TYPE_CHECKING:` guard and string literal type hints for `ApplicationCore` in these files.

Here are the updated files:

```python
# File: app/tax/gst_manager.py
# Update constructor and imports
from typing import Optional, Any, TYPE_CHECKING # Added TYPE_CHECKING
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta 
from decimal import Decimal

from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import CompanySettingsService 
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, JournalEntryLineData 
# from app.core.application_core import ApplicationCore # Removed direct import
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.journal_entry import JournalEntry # For type hint
from app.common.enums import GSTReturnStatus 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class GSTManager:
    def __init__(self, 
                 tax_code_service: TaxCodeService, 
                 journal_service: JournalService, 
                 company_settings_service: CompanySettingsService, 
                 gst_return_service: GSTReturnService,
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: "ApplicationCore"): # Use string literal for ApplicationCore
        self.tax_code_service = tax_code_service
        self.journal_service = journal_service
        self.company_settings_service = company_settings_service
        self.gst_return_service = gst_return_service
        self.account_service = account_service 
        self.fiscal_period_service = fiscal_period_service 
        self.sequence_generator = sequence_generator 
        self.app_core = app_core

    async def prepare_gst_return_data(self, start_date: date, end_date: date, user_id: int) -> Result[GSTReturnData]:
        # Simplified example, actual logic would query JournalEntryLines with tax codes
        company_settings = await self.company_settings_service.get_company_settings()
        if not company_settings:
            return Result.failure(["Company settings not found."])

        # These would be calculated based on transactions in the period
        # Summing from relevant journal entry lines based on tax codes and account types
        std_rated_supplies = Decimal('10000.00') # Placeholder
        zero_rated_supplies = Decimal('2000.00')  # Placeholder
        exempt_supplies = Decimal('500.00')     # Placeholder
        taxable_purchases = Decimal('5000.00')   # Placeholder
        output_tax_calc = std_rated_supplies * Decimal('0.08') # Assuming 8% GST
        input_tax_calc = taxable_purchases * Decimal('0.08') # Assuming 8% GST
        
        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc

        filing_due_date = end_date + relativedelta(months=1, day=31) # End of month following period end

        return_data = GSTReturnData(
            return_period=f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}",
            start_date=start_date,
            end_date=end_date,
            filing_due_date=filing_due_date,
            standard_rated_supplies=std_rated_supplies,
            zero_rated_supplies=zero_rated_supplies,
            exempt_supplies=exempt_supplies,
            total_supplies=total_supplies,
            taxable_purchases=taxable_purchases,
            output_tax=output_tax_calc,
            input_tax=input_tax_calc,
            tax_adjustments=Decimal(0), # Placeholder
            tax_payable=tax_payable,
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id # From UserAuditData mixin
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        current_user_id = gst_return_data.user_id

        if gst_return_data.id: # Update
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            
            # Update fields
            existing_return.return_period = gst_return_data.return_period
            # ... update all other fields ...
            existing_return.standard_rated_supplies=gst_return_data.standard_rated_supplies
            existing_return.zero_rated_supplies=gst_return_data.zero_rated_supplies
            existing_return.exempt_supplies=gst_return_data.exempt_supplies
            existing_return.total_supplies=gst_return_data.total_supplies
            existing_return.taxable_purchases=gst_return_data.taxable_purchases
            existing_return.output_tax=gst_return_data.output_tax
            existing_return.input_tax=gst_return_data.input_tax
            existing_return.tax_adjustments=gst_return_data.tax_adjustments
            existing_return.tax_payable=gst_return_data.tax_payable
            existing_return.status=gst_return_data.status
            existing_return.submission_date=gst_return_data.submission_date
            existing_return.submission_reference=gst_return_data.submission_reference
            existing_return.notes=gst_return_data.notes
            existing_return.updated_by_user_id = current_user_id
            orm_return = existing_return
        else: # Create
            orm_return = GSTReturn(
                return_period=gst_return_data.return_period,
                start_date=gst_return_data.start_date,
                end_date=gst_return_data.end_date,
                filing_due_date=gst_return_data.filing_due_date,
                standard_rated_supplies=gst_return_data.standard_rated_supplies,
                zero_rated_supplies=gst_return_data.zero_rated_supplies,
                exempt_supplies=gst_return_data.exempt_supplies,
                total_supplies=gst_return_data.total_supplies,
                taxable_purchases=gst_return_data.taxable_purchases,
                output_tax=gst_return_data.output_tax,
                input_tax=gst_return_data.input_tax,
                tax_adjustments=gst_return_data.tax_adjustments,
                tax_payable=gst_return_data.tax_payable,
                status=gst_return_data.status,
                submission_date=gst_return_data.submission_date,
                submission_reference=gst_return_data.submission_reference,
                notes=gst_return_data.notes,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
        
        try:
            saved_return = await self.gst_return_service.save_gst_return(orm_return)
            return Result.success(saved_return)
        except Exception as e:
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

        # Create Journal Entry for GST payable/refundable
        if gst_return.tax_payable != Decimal(0):
            # Determine GST control accounts (from company settings or default)
            # This is a placeholder - actual account codes should be configurable
            gst_output_tax_acc_code = "SYS-GST-OUTPUT" # Placeholder
            gst_input_tax_acc_code = "SYS-GST-INPUT"   # Placeholder
            gst_payable_control_acc_code = "GST-PAYABLE" # Placeholder, for net GST liability/asset

            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code)
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code)
            payable_control_acc = await self.account_service.get_by_code(gst_payable_control_acc_code)

            if not (output_tax_acc and input_tax_acc and payable_control_acc):
                return Result.failure(["Essential GST GL accounts not found. Cannot create journal entry."])

            lines = []
            # Clear Output Tax (Credit Output Tax, Debit GST Payable/Control)
            if gst_return.output_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description="Clear GST Output Tax"))
            # Clear Input Tax (Debit Input Tax, Credit GST Payable/Control)
            if gst_return.input_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description="Clear GST Input Tax"))
            
            # Net effect on GST Payable/Control Account
            if gst_return.tax_payable > Decimal(0): # Tax Payable
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description="GST Payable to IRAS"))
            elif gst_return.tax_payable < Decimal(0): # Tax Refundable
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=abs(gst_return.tax_payable), credit_amount=Decimal(0), description="GST Refundable from IRAS"))
            
            if lines:
                je_data = JournalEntryData(
                    journal_type="General", entry_date=submission_date, # Or period end date
                    description=f"GST payment/refund for period {gst_return.return_period}",
                    reference=f"GST F5: {gst_return.return_period}", user_id=user_id, lines=lines,
                    source_type="GSTReturn", source_id=gst_return.id
                )
                je_result = await self.app_core.journal_entry_manager.create_journal_entry(je_data) # type: ignore
                if not je_result.is_success:
                    # Return failure but GST return is still marked submitted. Log this.
                    print(f"Warning: GST Return finalized but JE creation failed: {je_result.errors}")
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    # Optionally post the JE
                    # await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)


        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            return Result.failure([f"Failed to finalize GST return: {str(e)}"])

```

```python
# File: app/tax/income_tax_manager.py
# (Content as previously generated, verified for ApplicationCore property access)
from typing import TYPE_CHECKING # Added TYPE_CHECKING
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting


class IncomeTaxManager:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal
        self.app_core = app_core
        self.account_service: AccountService = app_core.account_service
        self.journal_service: JournalService = app_core.journal_service
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service
        # self.company_settings_service = app_core.company_settings_service
        print("IncomeTaxManager initialized (stub).")
    
    async def calculate_provisional_tax(self, fiscal_year_id: int):
        print(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        # Example:
        # financial_reports = self.app_core.financial_statement_generator
        # income_comp = await financial_reports.generate_income_tax_computation_for_fy_id(fiscal_year_id)
        # apply tax rates...
        return {"provisional_tax_payable": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int):
        print(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        return {"company_name": "Example Pte Ltd", "revenue": 100000.00, "profit_before_tax": 20000.00}

```

```python
# File: app/tax/withholding_tax_manager.py
# (Content as previously generated, verified for ApplicationCore property access)
from typing import TYPE_CHECKING # Added TYPE_CHECKING
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.tax_service import TaxCodeService
from app.services.journal_service import JournalService
# from app.services.vendor_service import VendorService 
# from app.models.accounting.withholding_tax_certificate import WithholdingTaxCertificate

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class WithholdingTaxManager:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal
        self.app_core = app_core
        self.tax_code_service: TaxCodeService = app_core.tax_code_service # type: ignore
        self.journal_service: JournalService = app_core.journal_service # type: ignore
        # self.vendor_service = app_core.vendor_service 
        print("WithholdingTaxManager initialized (stub).")

    async def generate_s45_form_data(self, wht_certificate_id: int):
        print(f"Generating S45 form data for WHT certificate ID {wht_certificate_id} (stub).")
        return {"s45_field_1": "data", "s45_field_2": "more_data"}

    async def record_wht_payment(self, certificate_id: int, payment_date: str, reference: str):
        print(f"Recording WHT payment for certificate {certificate_id} (stub).")
        return True

```

**Validation of Changes:**

*   **`app/tax/gst_manager.py`**:
    *   Added `from typing import TYPE_CHECKING`.
    *   Removed the direct import `from app.core.application_core import ApplicationCore`.
    *   Added the `if TYPE_CHECKING:` block for importing `ApplicationCore`.
    *   Changed the type hint for `app_core` in `__init__` to the string literal `"ApplicationCore"`.
    *   Corrected `created_by` and `updated_by` to `created_by_user_id` and `updated_by_user_id` in `save_gst_return` method to align with ORM model (assuming `GSTReturn` uses these names from `UserAuditMixin` or similar).
    *   Used `GSTReturnStatusEnum` for status comparisons and assignments.
    *   Placeholder values in `prepare_gst_return_data` remain, but the structure is for demonstration.
    *   Journal entry creation in `finalize_gst_return` assumes `self.app_core.journal_entry_manager` is available and functional.

*   **`app/tax/income_tax_manager.py`**:
    *   Added `from typing import TYPE_CHECKING`.
    *   Removed the direct import `from app.core.application_core import ApplicationCore`.
    *   Added the `if TYPE_CHECKING:` block for importing `ApplicationCore`.
    *   Changed the type hint for `app_core` in `__init__` to the string literal `"ApplicationCore"`.

*   **`app/tax/withholding_tax_manager.py`**:
    *   Added `from typing import TYPE_CHECKING`.
    *   Removed the direct import `from app.core.application_core import ApplicationCore`.
    *   Added the `if TYPE_CHECKING:` block for importing `ApplicationCore`.
    *   Changed the type hint for `app_core` in `__init__` to the string literal `"ApplicationCore"`.

**Next Steps:**

These changes should resolve the current circular import error involving the tax managers. Please try running the application again:

```bash
poetry run sg_bookkeeper
```

Continue to monitor the output for any further import errors or runtime issues. The next set of errors might point to unprovided service implementations (like `FiscalYearService` if not correctly set up in `ApplicationCore` and `accounting_services.py`) or manager classes that `ApplicationCore` tries to instantiate.

