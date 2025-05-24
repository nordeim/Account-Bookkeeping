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
# from app.core.application_core import ApplicationCore # Removed direct import
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
        gst_rate = Decimal('0.09') # Default to 9%
        if sr_tax_code and sr_tax_code.tax_type == 'GST' and sr_tax_code.rate is not None: # Ensure rate is not None
            gst_rate = sr_tax_code.rate / Decimal(100)
        else:
            print("Warning: Standard Rate GST tax code 'SR' not found, not GST type, or rate is null. Defaulting to 9% for calculation.")

        # Placeholder logic for calculating GST figures.
        # In a real implementation, this would iterate through relevant transactions (e.g., JournalEntryLine)
        # within the date range, check their tax codes, and sum up amounts.
        # Example:
        # std_rated_supplies = await self.journal_service.get_sum_for_gst_box(start_date, end_date, 'SR_SUPPLIES_BOX')
        # output_tax_calc = await self.journal_service.get_sum_for_gst_box(start_date, end_date, 'OUTPUT_TAX_BOX')
        # etc.
        
        # For now, using illustrative fixed values for demonstration
        std_rated_supplies = Decimal('10000.00') 
        zero_rated_supplies = Decimal('2000.00')  
        exempt_supplies = Decimal('500.00')     
        taxable_purchases = Decimal('5000.00')   
        output_tax_calc = (std_rated_supplies * gst_rate).quantize(Decimal("0.01"))
        input_tax_calc = (taxable_purchases * gst_rate).quantize(Decimal("0.01"))

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
            # Update all fields from DTO
            update_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            for key, value in update_dict.items():
                if hasattr(orm_return, key):
                    setattr(orm_return, key, value)
            orm_return.updated_by_user_id = current_user_id
        else: 
            # Create new
            # Ensure all NOT NULL fields are present in GSTReturnData or have defaults in model
            create_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            orm_return = GSTReturn(
                **create_dict,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
            if not orm_return.filing_due_date: # Calculate if not provided
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

        if gst_return.tax_payable != Decimal(0):
            # Define system account codes
            gst_output_tax_acc_code = self.app_core.config_manager.get_setting("SystemAccounts", "GSTOutputTax", "SYS-GST-OUTPUT") or "SYS-GST-OUTPUT"
            gst_input_tax_acc_code = self.app_core.config_manager.get_setting("SystemAccounts", "GSTInputTax", "SYS-GST-INPUT") or "SYS-GST-INPUT"
            gst_payable_control_acc_code = self.app_core.config_manager.get_setting("SystemAccounts", "GSTPayableControl", "GST-PAYABLE") or "GST-PAYABLE"

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
            if gst_return.output_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description="Clear GST Output Tax for period " + gst_return.return_period))
            if gst_return.input_tax != Decimal(0): # Input tax reduces liability, so it's a debit to Input Tax (asset) when clearing, meaning credit here
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description="Clear GST Input Tax for period " + gst_return.return_period))
            
            if gst_return.tax_payable > Decimal(0): 
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable to IRAS for period {gst_return.return_period}"))
            elif gst_return.tax_payable < Decimal(0): 
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
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])
