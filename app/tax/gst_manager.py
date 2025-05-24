# File: app/tax/gst_manager.py
# Update constructor and imports
from typing import Optional, Any, TYPE_CHECKING, List 
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
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.journal_entry import JournalEntry 
from app.common.enums import GSTReturnStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class GSTManager:
    def __init__(self, 
                 tax_code_service: TaxCodeService, 
                 journal_service: JournalService, 
                 company_settings_service: CompanySettingsService, 
                 gst_return_service: GSTReturnService,
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
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
        
        sr_tax_code = await self.tax_code_service.get_tax_code('SR')
        gst_rate_decimal = Decimal('0.09') # Default to 9%
        if sr_tax_code and sr_tax_code.tax_type == 'GST' and sr_tax_code.rate is not None:
            gst_rate_decimal = sr_tax_code.rate / Decimal(100)
        else:
            print("Warning: Standard Rate GST tax code 'SR' not found or not GST type or rate is null. Defaulting to 9% for calculation.")
        
        # --- Placeholder for actual data aggregation ---
        # This section needs to query JournalEntryLines within the date range,
        # join with Accounts and TaxCodes to categorize amounts correctly.
        # Example structure (conceptual, actual queries would be more complex):
        #
        # async with self.app_core.db_manager.session() as session:
        #     # Output Tax related (Sales)
        #     sales_lines = await session.execute(
        #         select(JournalEntryLine, Account.account_type, TaxCode.code)
        #         .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
        #         .join(Account, Account.id == JournalEntryLine.account_id)
        #         .outerjoin(TaxCode, TaxCode.code == JournalEntryLine.tax_code)
        #         .where(JournalEntry.is_posted == True)
        #         .where(JournalEntry.entry_date >= start_date)
        #         .where(JournalEntry.entry_date <= end_date)
        #         .where(Account.account_type == 'Revenue') # Example: Only revenue lines for supplies
        #     )
        #     for line, acc_type, tax_c in sales_lines.all():
        #         amount = line.credit_amount - line.debit_amount # Net credit for revenue
        #         if tax_c == 'SR':
        #             std_rated_supplies += amount
        #             output_tax_calc += line.tax_amount # Assuming tax_amount is correctly populated
        #         elif tax_c == 'ZR':
        #             zero_rated_supplies += amount
        #         elif tax_c == 'ES':
        #             exempt_supplies += amount
            
        #     # Input Tax related (Purchases/Expenses)
        #     purchase_lines = await session.execute(...) # Similar query for expense/asset accounts
        #     for line, acc_type, tax_c in purchase_lines.all():
        #         amount = line.debit_amount - line.credit_amount # Net debit for expense/asset
        #         if tax_c == 'TX':
        #             taxable_purchases += amount
        #             input_tax_calc += line.tax_amount
        #         # Handle 'BL' - Blocked Input Tax if necessary
        # --- End of Placeholder ---

        # For now, using illustrative fixed values for demonstration (if above is commented out)
        std_rated_supplies = Decimal('10000.00') 
        zero_rated_supplies = Decimal('2000.00')  
        exempt_supplies = Decimal('500.00')     
        taxable_purchases = Decimal('5000.00')   
        output_tax_calc = (std_rated_supplies * gst_rate_decimal).quantize(Decimal("0.01"))
        input_tax_calc = (taxable_purchases * gst_rate_decimal).quantize(Decimal("0.01"))

        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc

        filing_due_date = end_date + relativedelta(months=1, day=31) 

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
            tax_adjustments=Decimal(0), 
            tax_payable=tax_payable,
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id 
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        current_user_id = gst_return_data.user_id

        if gst_return_data.id: 
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            
            orm_return = existing_return
            update_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            for key, value in update_dict.items():
                if hasattr(orm_return, key):
                    setattr(orm_return, key, value)
            orm_return.updated_by_user_id = current_user_id
        else: 
            create_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            orm_return = GSTReturn(
                **create_dict,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
            if not orm_return.filing_due_date: 
                 orm_return.filing_due_date = orm_return.end_date + relativedelta(months=1, day=31)

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

        if gst_return.tax_payable != Decimal(0): # Only create JE if there's a net payable/refundable
            # System account codes from config or defaults
            sys_acc_config = self.app_core.config_manager.parser['SystemAccounts'] if self.app_core.config_manager.parser.has_section('SystemAccounts') else {}
            gst_output_tax_acc_code = sys_acc_config.get("GSTOutputTax", "SYS-GST-OUTPUT")
            gst_input_tax_acc_code = sys_acc_config.get("GSTInputTax", "SYS-GST-INPUT")
            gst_payable_control_acc_code = sys_acc_config.get("GSTPayableControl", "GST-PAYABLE")


            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code)
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code)
            payable_control_acc = await self.account_service.get_by_code(gst_payable_control_acc_code)

            if not (output_tax_acc and input_tax_acc and payable_control_acc):
                try:
                    updated_return_no_je = await self.gst_return_service.save_gst_return(gst_return)
                    return Result.failure([f"GST Return finalized and saved (ID: {updated_return_no_je.id}), but essential GST GL accounts ({gst_output_tax_acc_code}, {gst_input_tax_acc_code}, {gst_payable_control_acc_code}) not found. Cannot create journal entry."])
                except Exception as e_save:
                    return Result.failure([f"Failed to finalize GST return and also failed to save it before JE creation: {str(e_save)}"])

            lines = []
            # To clear Output Tax (usually a credit balance): Debit Output Tax Account
            if gst_return.output_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description=f"Clear GST Output Tax for period {gst_return.return_period}"))
            # To clear Input Tax (usually a debit balance): Credit Input Tax Account
            if gst_return.input_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description=f"Clear GST Input Tax for period {gst_return.return_period}"))
            
            # Net effect on GST Payable/Control Account
            if gst_return.tax_payable > Decimal(0): # Tax Payable (Liability)
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable to IRAS for period {gst_return.return_period}"))
            elif gst_return.tax_payable < Decimal(0): # Tax Refundable (Asset)
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=abs(gst_return.tax_payable), credit_amount=Decimal(0), description=f"GST Refundable from IRAS for period {gst_return.return_period}"))
            
            if lines:
                if not hasattr(self.app_core, 'journal_entry_manager') or not self.app_core.journal_entry_manager:
                    return Result.failure(["Journal Entry Manager not available in Application Core. Cannot create GST settlement JE."])

                je_data = JournalEntryData(
                    journal_type="General", entry_date=submission_date, 
                    description=f"GST settlement for period {gst_return.return_period}",
                    reference=f"GST F5: {gst_return.return_period}", user_id=user_id, lines=lines,
                    source_type="GSTReturn", source_id=gst_return.id
                )
                je_result = await self.app_core.journal_entry_manager.create_journal_entry(je_data) 
                if not je_result.is_success:
                    try:
                        updated_return_je_fail = await self.gst_return_service.save_gst_return(gst_return)
                        return Result.failure([f"GST Return finalized and saved (ID: {updated_return_je_fail.id}) but JE creation failed."] + je_result.errors)
                    except Exception as e_save_2:
                         return Result.failure([f"Failed to finalize GST return and also failed during JE creation and subsequent save: {str(e_save_2)}"] + je_result.errors)
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    # Optionally auto-post the JE
                    # post_result = await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)
                    # if not post_result.is_success:
                    #     print(f"Warning: GST JE created (ID: {je_result.value.id}) but failed to auto-post: {post_result.errors}")
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])
