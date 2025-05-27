# File: app/tax/gst_manager.py
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
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
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
        output_tax_calc = Decimal('0.00') # Box 6
        input_tax_calc = Decimal('0.00')  # Box 7
        
        # Fetch posted journal entries for the period.
        # The service method now eager loads lines, accounts, and tax_code_obj.
        posted_entries: List[JournalEntry] = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)

        for entry in posted_entries:
            for line in entry.lines:
                if not line.account or not line.tax_code_obj: # Skip lines without account or tax code info
                    continue

                account_orm: Account = line.account
                tax_code_orm: TaxCode = line.tax_code_obj
                
                # Determine net amount for the line based on its nature in JE
                # For revenue accounts (credit nature), a credit amount on the line increases revenue.
                # For expense/asset accounts (debit nature), a debit amount on the line increases expense/asset.
                line_net_value_for_gst_box: Decimal = Decimal('0.00')
                if account_orm.account_type == 'Revenue':
                    line_net_value_for_gst_box = line.credit_amount - line.debit_amount # Positive for revenue
                elif account_orm.account_type in ['Expense', 'Asset']:
                    line_net_value_for_gst_box = line.debit_amount - line.credit_amount # Positive for expense/asset

                if line_net_value_for_gst_box <= Decimal('0.00') and tax_code_orm.tax_type == 'GST' : # Only process if it contributes to the total
                    # This condition might be too strict if, e.g., a sales credit note (debit to revenue)
                    # should reduce standard-rated supplies. For now, assuming positive contributions.
                    # For a more robust system, credit notes would have their own handling or specific tax codes.
                    pass # Or log a warning if a negative value with GST code is encountered

                # Categorize based on account type and tax code
                if tax_code_orm.tax_type == 'GST':
                    if account_orm.account_type == 'Revenue':
                        if tax_code_orm.code == 'SR': # Standard-Rated Supply
                            std_rated_supplies += line_net_value_for_gst_box
                            output_tax_calc += line.tax_amount # tax_amount on JE line IS the GST
                        elif tax_code_orm.code == 'ZR': # Zero-Rated Supply
                            zero_rated_supplies += line_net_value_for_gst_box
                        elif tax_code_orm.code == 'ES': # Exempt Supply
                            exempt_supplies += line_net_value_for_gst_box
                        # OP (Out of Scope) supplies are typically not included in these boxes.
                    
                    elif account_orm.account_type in ['Expense', 'Asset']:
                        if tax_code_orm.code == 'TX': # Taxable Purchase
                            taxable_purchases += line_net_value_for_gst_box
                            input_tax_calc += line.tax_amount # tax_amount on JE line IS the GST
                        elif tax_code_orm.code == 'BL': # Blocked Input Tax
                            # The net amount IS part of taxable purchases (Box 5)
                            taxable_purchases += line_net_value_for_gst_box
                            # However, the tax_amount is NOT claimable as input tax (Box 7)
                            # So, no addition to input_tax_calc for BL code.
                        # Other codes like ME (Imported Goods under Major Exporter Scheme) etc. would need specific handling.
        
        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc # Ignores Box 8 (adjustments) for now

        # Filing due date is typically one month after the end of the accounting period.
        # Example: Period ends 31 Mar, due 30 Apr. Period ends 30 Apr, due 31 May.
        # Using relativedelta for more robust month-end calculation.
        filing_due_date = end_date + relativedelta(months=1) 
        # If period ends mid-month, due date is end of next month. If period ends end-of-month, due date is end of next month.
        # A common rule is simply "one month after the end of the prescribed accounting period".
        # If end_date is always month-end, then +1 month then last day of that month works.
        # For simplicity, let's assume end_date is the actual period end. IRAS specifies due date.
        # For quarterly, it's 1 month after quarter end. Let's use a simpler rule for now.
        # Safest might be to refer to company settings for GST period type to calculate precisely.
        # For now: last day of the month following the end_date.
        temp_due_date = end_date + relativedelta(months=1)
        filing_due_date = temp_due_date + relativedelta(day=31) # Clamp to last day of that month

        return_data = GSTReturnData(
            return_period=f"{start_date.strftime('%d%m%Y')}-{end_date.strftime('%d%m%Y')}", # IRAS format for period
            start_date=start_date, end_date=end_date,
            filing_due_date=filing_due_date,
            standard_rated_supplies=std_rated_supplies.quantize(Decimal("0.01")),
            zero_rated_supplies=zero_rated_supplies.quantize(Decimal("0.01")),
            exempt_supplies=exempt_supplies.quantize(Decimal("0.01")),
            total_supplies=total_supplies.quantize(Decimal("0.01")), # Box 4
            taxable_purchases=taxable_purchases.quantize(Decimal("0.01")), # Box 5
            output_tax=output_tax_calc.quantize(Decimal("0.01")), # Box 6
            input_tax=input_tax_calc.quantize(Decimal("0.01")),   # Box 7
            tax_adjustments=Decimal(0), # Box 8 - Placeholder
            tax_payable=tax_payable.quantize(Decimal("0.01")), # Box 9
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id 
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        # ... (method remains largely the same as previous version, was already robust)
        current_user_id = gst_return_data.user_id

        orm_return: GSTReturn
        if gst_return_data.id: 
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            
            orm_return = existing_return
            # Use .model_dump() for Pydantic v2
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
            if not orm_return.filing_due_date and orm_return.end_date: # Calculate if not provided
                 temp_due_date = orm_return.end_date + relativedelta(months=1)
                 orm_return.filing_due_date = temp_due_date + relativedelta(day=31)


        try:
            saved_return = await self.gst_return_service.save_gst_return(orm_return)
            return Result.success(saved_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save GST return: {str(e)}"])

    async def finalize_gst_return(self, return_id: int, submission_reference: str, submission_date: date, user_id: int) -> Result[GSTReturn]:
        # ... (method remains largely the same as previous version, ensure logger for errors)
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
            sys_acc_config_section = 'SystemAccounts'
            sys_acc_config = {}
            if self.app_core.config_manager.parser.has_section(sys_acc_config_section):
                sys_acc_config = self.app_core.config_manager.parser[sys_acc_config_section]
            
            gst_output_tax_acc_code = sys_acc_config.get("GSTOutputTax", "SYS-GST-OUTPUT")
            gst_input_tax_acc_code = sys_acc_config.get("GSTInputTax", "SYS-GST-INPUT")
            gst_payable_control_acc_code = sys_acc_config.get("GSTPayableControl", "GST-PAYABLE") # For net payable to IRAS
            gst_receivable_control_acc_code = sys_acc_config.get("GSTReceivableControl", "GST-RECEIVABLE") # For net refundable from IRAS

            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code)
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code)
            # Determine if it's payable or receivable for the control account
            control_acc_code = gst_payable_control_acc_code if gst_return.tax_payable > 0 else gst_receivable_control_acc_code
            control_acc = await self.account_service.get_by_code(control_acc_code)


            if not (output_tax_acc and input_tax_acc and control_acc):
                missing_accs = []
                if not output_tax_acc: missing_accs.append(gst_output_tax_acc_code)
                if not input_tax_acc: missing_accs.append(gst_input_tax_acc_code)
                if not control_acc: missing_accs.append(control_acc_code)
                
                error_msg = f"Essential GST GL accounts not found: {', '.join(missing_accs)}. Cannot create settlement journal entry."
                self.app_core.logger.error(error_msg) # type: ignore
                # Save the GST return status update even if JE fails
                try:
                    updated_return_no_je = await self.gst_return_service.save_gst_return(gst_return)
                    return Result.failure([f"GST Return finalized (ID: {updated_return_no_je.id}), but JE creation failed: " + error_msg])
                except Exception as e_save:
                    return Result.failure([f"Failed to finalize GST return and also failed to save it before JE creation: {str(e_save)}"] + [error_msg])


            lines: List[JournalEntryLineData] = []
            desc_period = f"GST for period {gst_return.start_date.strftime('%d/%m/%y')}-{gst_return.end_date.strftime('%d/%m/%y')}"
            
            # To clear Output Tax (usually a credit balance): Debit Output Tax Account
            if gst_return.output_tax != Decimal(0): # Use actual output_tax from return
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description=f"Clear Output Tax - {desc_period}"))
            # To clear Input Tax (usually a debit balance): Credit Input Tax Account
            if gst_return.input_tax != Decimal(0): # Use actual input_tax from return
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description=f"Clear Input Tax - {desc_period}"))
            
            # Net effect on GST Payable/Receivable Control Account
            if gst_return.tax_payable > Decimal(0): # Tax Payable (Liability)
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable - {desc_period}"))
            elif gst_return.tax_payable < Decimal(0): # Tax Refundable (Asset)
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
                        return Result.failure([f"GST Return finalized and saved (ID: {updated_return_je_fail.id}) but settlement JE creation failed."] + je_result.errors)
                    except Exception as e_save_2:
                         return Result.failure([f"Failed to finalize GST return and also failed during JE creation and subsequent save: {str(e_save_2)}"] + je_result.errors)
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    # Optionally auto-post the JE
                    post_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)
                    if not post_result.is_success:
                        self.app_core.logger.warning(f"GST Settlement JE (ID: {je_result.value.id}) created but failed to auto-post: {post_result.errors}") # type: ignore
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save finalized GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])
