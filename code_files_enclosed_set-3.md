# app/tax/__init__.py
```py
# File: app/tax/__init__.py
# (Content as previously generated, no changes needed)
from .gst_manager import GSTManager
from .tax_calculator import TaxCalculator
from .income_tax_manager import IncomeTaxManager
from .withholding_tax_manager import WithholdingTaxManager

__all__ = [
    "GSTManager",
    "TaxCalculator",
    "IncomeTaxManager",
    "WithholdingTaxManager",
]

```

# app/tax/income_tax_manager.py
```py
# File: app/tax/income_tax_manager.py
# (Content as previously generated, verified for ApplicationCore property access)
from app.core.application_core import ApplicationCore
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService

class IncomeTaxManager:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core
        # Access services via app_core properties
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

# app/tax/gst_manager.py
```py
# File: app/tax/gst_manager.py
# Update constructor and imports
from typing import Optional, Any # Added Any
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta 
from decimal import Decimal

from app.services.tax_service import TaxCodeService, GSTReturnService # Paths updated based on where they are
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import CompanySettingsService # Corrected path
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, JournalEntryLineData 
from app.core.application_core import ApplicationCore
from app.models.accounting.gst_return import GSTReturn # Corrected path
from app.models.accounting.journal_entry import JournalEntry # For type hint
from app.common.enums import GSTReturnStatus # Using enum for status

class GSTManager:
    def __init__(self, 
                 tax_code_service: TaxCodeService, 
                 journal_service: JournalService, 
                 company_settings_service: CompanySettingsService, # Updated type
                 gst_return_service: GSTReturnService,
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: ApplicationCore): # Pass app_core for user_id consistently
        self.tax_code_service = tax_code_service
        self.journal_service = journal_service
        self.company_settings_service = company_settings_service
        self.gst_return_service = gst_return_service
        self.account_service = account_service 
        self.fiscal_period_service = fiscal_period_service 
        self.sequence_generator = sequence_generator 
        self.app_core = app_core
    # ... rest of the methods remain largely the same, ensure user_id passed from app_core
    # and Pydantic DTOs are used. Example of user_id usage:
    # current_user_id = self.app_core.current_user.id if self.app_core.current_user else 0 (or raise error)

```

# app/tax/withholding_tax_manager.py
```py
# File: app/tax/withholding_tax_manager.py
# (Content as previously generated, verified for ApplicationCore property access)
from app.core.application_core import ApplicationCore
from app.services.tax_service import TaxCodeService
from app.services.journal_service import JournalService
# from app.services.vendor_service import VendorService # If a specific service for vendors exists
# from app.models.accounting.withholding_tax_certificate import WithholdingTaxCertificate

class WithholdingTaxManager:
    def __init__(self, app_core: ApplicationCore):
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

# app/tax/tax_calculator.py
```py
# File: app/tax/tax_calculator.py
# (Content as previously generated, verified)
from decimal import Decimal
from typing import List, Optional, Any

from app.services.tax_service import TaxCodeService 
from app.utils.pydantic_models import TaxCalculationResultData, TransactionTaxData, TransactionLineTaxData
from app.models.accounting.tax_code import TaxCode 

class TaxCalculator:
    def __init__(self, tax_code_service: TaxCodeService):
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
        
        tax_code_info: Optional[TaxCode] = await self.tax_code_service.get_tax_code(tax_code_str)
        if not tax_code_info:
            return result 
        
        if tax_code_info.tax_type == 'GST':
            return await self._calculate_gst(amount, tax_code_info, transaction_type)
        elif tax_code_info.tax_type == 'Withholding Tax':
            return await self._calculate_withholding_tax(amount, tax_code_info, transaction_type)
        return result
    
    async def _calculate_gst(self, amount: Decimal, tax_code_info: TaxCode, transaction_type: str) -> TaxCalculationResultData:
        tax_rate = Decimal(str(tax_code_info.rate))
        net_amount = amount 
        tax_amount = net_amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=net_amount
        )
    
    async def _calculate_withholding_tax(self, amount: Decimal, tax_code_info: TaxCode, transaction_type: str) -> TaxCalculationResultData:
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

# app/reporting/financial_statement_generator.py
```py
# File: app/reporting/financial_statement_generator.py
# (Content as previously generated and verified)
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService
from app.services.core_services import CompanySettingsService 
from app.services.accounting_services import AccountTypeService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 


class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService,
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             # Assuming AccountType.category is the primary key like 'Asset', 'Liability'
             # And Account.account_type stores this category string.
             self._account_type_map_cache = {at.category: at for at in ats} 
        return self._account_type_map_cache

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        result_list = []
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date)
            display_balance = balance_value 
            
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])

            if not is_debit_nature: 
                display_balance = -balance_value 

            result_list.append({
                'id': account.id, 'code': account.code, 'name': account.name,
                'balance': display_balance 
            })
        return result_list

    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        result_list = []
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            display_activity = activity_value
            if account.account_type in ['Revenue']: 
                display_activity = -activity_value
            result_list.append({
                'id': account.id, 'code': account.code, 'name': account.name,
                'balance': display_activity 
            })
        return result_list

    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active()
        
        assets_orm = [a for a in accounts if a.account_type == 'Asset']
        liabilities_orm = [a for a in accounts if a.account_type == 'Liability']
        equity_orm = [a for a in accounts if a.account_type == 'Equity']
        
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date)
        liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date)
        equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date:
            comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date)
            comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date)
            comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)

        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]
            liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]
            equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date:
                comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None
                comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None
                comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None

        total_assets = sum(a['balance'] for a in asset_accounts)
        total_liabilities = sum(a['balance'] for a in liability_accounts)
        total_equity = sum(a['balance'] for a in equity_accounts)
        
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None
        comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None
        comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None

        return {
            'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",
            'as_of_date': as_of_date, 'comparative_date': comparative_date,
            'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},
            'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},
            'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},
            'total_liabilities_equity': total_liabilities + total_equity,
            'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,
            'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")
        }

    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active()
        
        revenues_orm = [a for a in accounts if a.account_type == 'Revenue']
        expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date)
        expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end:
            comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end)
            comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)

        total_revenue = sum(a['balance'] for a in revenue_accounts)
        total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None
        comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None

        return {
            'title': 'Profit & Loss Statement', 
            'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
            'start_date': start_date, 'end_date': end_date, 
            'comparative_start': comparative_start, 'comparative_end': comparative_end,
            'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},
            'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},
            'net_profit': net_profit, 'comparative_net_profit': comp_net_profit
        }

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active()
        debit_accounts_list, credit_accounts_list = [], [] 
        total_debits_val, total_credits_val = Decimal(0), Decimal(0) 

        acc_type_map = await self._get_account_type_map()

        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue

            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])

            if is_debit_nature: 
                if raw_balance >= Decimal(0): 
                    debit_accounts_list.append(account_data)
                    total_debits_val += raw_balance
                else: 
                    account_data['balance'] = abs(raw_balance) 
                    credit_accounts_list.append(account_data)
                    total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): 
                    credit_accounts_list.append(account_data)
                    total_credits_val += abs(raw_balance)
                else: 
                    account_data['balance'] = raw_balance 
                    debit_accounts_list.append(account_data)
                    total_debits_val += raw_balance
        
        debit_accounts_list.sort(key=lambda a: a['code'])
        credit_accounts_list.sort(key=lambda a: a['code'])
        
        return {
            'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",
            'as_of_date': as_of_date,
            'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,
            'total_debits': total_debits_val, 'total_credits': total_credits_val,
            'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")
        }

    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: 
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value)
        if not fiscal_year_obj:
            raise ValueError(f"Fiscal year definition for {year_int_value} not found.")

        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date)
        net_profit = pl_data['net_profit']
        
        adjustments = []
        tax_effect = Decimal(0)
        
        tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')

        for account in tax_adj_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            
            adj_is_addition = activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0)
            
            adjustments.append({
                'id': account.id, 'code': account.code, 'name': account.name, 
                'amount': activity, 'is_addition': adj_is_addition
            })
            tax_effect += activity 
            
        taxable_income = net_profit + tax_effect
        
        return {
            'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', 
            'report_date_description': f"For Financial Year Ended {fiscal_year_obj.end_date.strftime('%d %b %Y')}",
            'year': year_int_value, 'fiscal_year_start': start_date, 'fiscal_year_end': end_date,
            'net_profit': net_profit, 'adjustments': adjustments, 
            'tax_effect': tax_effect, 'taxable_income': taxable_income
        }

    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        if not self.company_settings_service or not self.tax_code_service:
            raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")

        company = await self.company_settings_service.get_company_settings()
        if not company:
             raise ValueError("Company settings not found.")

        report_data: Dict[str, Any] = {
            'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
            'company_name': company.company_name,
            'gst_registration_no': company.gst_registration_no,
            'period_start': start_date, 'period_end': end_date,
            'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),
            'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),
            'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),
            'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)
        }
        
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                
                line_net_amount = (line.debit_amount or line.credit_amount) 
                tax_on_line = line.tax_amount

                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR':
                        report_data['standard_rated_supplies'] += line_net_amount
                        report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR':
                        report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES':
                        report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': 
                        report_data['taxable_purchases'] += line_net_amount
                        report_data['input_tax'] += tax_on_line
        
        report_data['total_supplies'] = (
            report_data['standard_rated_supplies'] + 
            report_data['zero_rated_supplies'] + 
            report_data['exempt_supplies']
        )
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        
        return report_data

```

# app/reporting/__init__.py
```py
# File: app/reporting/__init__.py
# (Content as previously generated, verified)
from .financial_statement_generator import FinancialStatementGenerator
from .tax_report_generator import TaxReportGenerator
from .report_engine import ReportEngine

__all__ = [
    "FinancialStatementGenerator",
    "TaxReportGenerator",
    "ReportEngine",
]

```

# app/reporting/report_engine.py
```py
# File: app/reporting/report_engine.py
# (Content as previously generated, verified)
from typing import Dict, Any, Literal, List, Optional 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4 
from reportlab.lib.units import inch, cm 
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
from app.core.application_core import ApplicationCore 
from decimal import Decimal 

class ReportEngine:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core

    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        if format_type == "pdf":
            return self._export_to_pdf_generic(report_data)
        elif format_type == "excel":
            return self._export_to_excel_generic(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2) -> str:
        if value is None: return ""
        if not isinstance(value, Decimal): 
            try:
                value = Decimal(str(value))
            except: 
                return "ERR_DEC"
        return f"{value:,.{places}f}"

    def _export_to_pdf_generic(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story: List[Any] = [] 

        title_text = report_data.get('title', "Financial Report")
        date_desc_text = report_data.get('report_date_description', "")
        
        story.append(Paragraph(title_text, styles['h1']))
        if date_desc_text:
            story.append(Paragraph(date_desc_text, styles['h3']))
        story.append(Spacer(1, 0.5*cm))
        
        table_data_list: List[List[Any]] = [] 

        if 'debit_accounts' in report_data: 
            table_data_list = [["Account Code", "Account Name", "Debit", "Credit"]]
            for acc in report_data.get('debit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            
            totals_row = ["", Paragraph("TOTALS", styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_debits')), styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_credits')), styles['Heading3'])]
            table_data_list.append(totals_row) # type: ignore

        elif 'assets' in report_data: 
            table_data_list = [["Section", "Account", "Current Period", "Comparative Period"]] 
            sections = ['assets', 'liabilities', 'equity']
            for section_key in sections:
                section_data = report_data.get(section_key, {})
                table_data_list.append([Paragraph(section_key.title(), styles['h2']), "", "", ""])
                for acc in section_data.get('accounts', []):
                    comp_val_str = ""
                    if section_data.get('comparative_accounts'):
                        comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                        comp_val_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                    table_data_list.append(["", f"{acc['code']} - {acc['name']}", self._format_decimal(acc['balance']), comp_val_str])
                
                total_str = self._format_decimal(section_data.get('total'))
                comp_total_str = self._format_decimal(section_data.get('comparative_total')) if section_data.get('comparative_total') is not None else ""
                table_data_list.append(["", Paragraph(f"Total {section_key.title()}", styles['Heading3']), total_str, comp_total_str])
        else:
            story.append(Paragraph("Report data structure not recognized for detailed PDF export.", styles['Normal']))

        if table_data_list:
            table = Table(table_data_list, colWidths=[doc.width/len(table_data_list[0])]*len(table_data_list[0])) 
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (2,1), (-1,-1), 'RIGHT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('LEFTPADDING', (0,0), (-1,-1), 3), 
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _export_to_excel_generic(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active 
        
        title = report_data.get('title', "Financial Report")
        ws.title = title[:30] # type: ignore

        row_num = 1
        ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=14) # type: ignore
        row_num += 1
        date_desc = report_data.get('report_date_description', "")
        if date_desc:
            ws.cell(row=row_num, column=1, value=date_desc).font = Font(italic=True) # type: ignore
            row_num += 1
        row_num += 1 

        if 'debit_accounts' in report_data: 
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col_num, header_text in enumerate(headers, 1): 
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=4, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            row_num +=1 
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True) # type: ignore
            ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
            ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
        else:
            ws.cell(row=row_num, column=1, value="Report data structure not recognized for Excel export.") # type: ignore

        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].auto_size = True # type: ignore
            
        excel_bytes_io = BytesIO()
        wb.save(excel_bytes_io)
        excel_bytes = excel_bytes_io.getvalue()
        excel_bytes_io.close()
        return excel_bytes

```

# app/reporting/tax_report_generator.py
```py
# File: app/reporting/tax_report_generator.py
# (Content as previously generated, verified)
from app.core.application_core import ApplicationCore
from datetime import date 

class TaxReportGenerator:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core

    async def generate_gst_audit_file(self, start_date: date, end_date: date):
        print(f"Generating GST Audit File for {start_date} to {end_date} (stub).")
        return {"filename": "gst_audit.xlsx", "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data": b"dummy_excel_data"}

    async def generate_income_tax_schedules(self, fiscal_year_id: int):
        print(f"Generating Income Tax Schedules for fiscal year ID {fiscal_year_id} (stub).")
        return {"schedule_name": "Capital Allowances", "data": []}

```

# app/common/enums.py
```py
# File: app/common/enums.py
# (Content as previously generated and verified)
from enum import Enum

class AccountCategory(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class AccountTypeEnum(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class JournalTypeEnum(Enum): 
    GENERAL = "General" 
    SALES = "Sales"
    PURCHASE = "Purchase"
    CASH_RECEIPT = "Cash Receipt" 
    CASH_DISBURSEMENT = "Cash Disbursement" 
    PAYROLL = "Payroll"
    OPENING_BALANCE = "Opening Balance"
    ADJUSTMENT = "Adjustment"

class FiscalPeriodTypeEnum(Enum): 
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year" 

class FiscalPeriodStatusEnum(Enum): 
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

class TaxTypeEnum(Enum): 
    GST = "GST"
    INCOME_TAX = "Income Tax"
    WITHHOLDING_TAX = "Withholding Tax"

class ProductTypeEnum(Enum): 
    INVENTORY = "Inventory"
    SERVICE = "Service"
    NON_INVENTORY = "Non-Inventory"

class GSTReturnStatusEnum(Enum): 
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AMENDED = "Amended"

class InventoryMovementTypeEnum(Enum): 
    PURCHASE = "Purchase"
    SALE = "Sale"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"
    RETURN = "Return"
    OPENING = "Opening"

class InvoiceStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    SENT = "Sent" 
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    VOIDED = "Voided"
    DISPUTED = "Disputed" 

class BankTransactionTypeEnum(Enum): 
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"
    INTEREST = "Interest"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"

class PaymentTypeEnum(Enum): 
    CUSTOMER_PAYMENT = "Customer Payment"
    VENDOR_PAYMENT = "Vendor Payment"
    REFUND = "Refund"
    CREDIT_NOTE_APPLICATION = "Credit Note" 
    OTHER = "Other"

class PaymentMethodEnum(Enum): 
    CASH = "Cash"
    CHECK = "Check"
    BANK_TRANSFER = "Bank Transfer"
    CREDIT_CARD = "Credit Card"
    GIRO = "GIRO"
    PAYNOW = "PayNow"
    OTHER = "Other"

class PaymentEntityTypeEnum(Enum): 
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    OTHER = "Other"

class PaymentStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    COMPLETED = "Completed" 
    VOIDED = "Voided"
    RETURNED = "Returned" 

class PaymentAllocationDocTypeEnum(Enum): 
    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    OTHER = "Other"

class WHCertificateStatusEnum(Enum): 
    DRAFT = "Draft"
    ISSUED = "Issued"
    VOIDED = "Voided"

class DataChangeTypeEnum(Enum): 
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"

class RecurringFrequencyEnum(Enum): 
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"

```

