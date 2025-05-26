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
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING # Added TYPE_CHECKING
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4 
from reportlab.lib.units import inch, cm 
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
# from app.core.application_core import ApplicationCore # Removed direct import
from decimal import Decimal 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal for ApplicationCore
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
                return "ERR_DEC" # Or handle as appropriate
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

        # Trial Balance specific structure
        if 'debit_accounts' in report_data and 'credit_accounts' in report_data: 
            table_data_list = [["Account Code", "Account Name", "Debit", "Credit"]]
            for acc in report_data.get('debit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            
            totals_row = ["", Paragraph("TOTALS", styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_debits')), styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_credits')), styles['Heading3'])]
            table_data_list.append(totals_row) # type: ignore

        # Balance Sheet / P&L specific structure
        elif 'assets' in report_data or 'revenue' in report_data: 
            headers = ["Section", "Account", "Current Period"]
            if report_data.get('comparative_date') or report_data.get('comparative_start'):
                headers.append("Comparative Period")
            table_data_list = [headers]
            
            sections_map = {
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'revenue': 'Revenue', 'expenses': 'Expenses'
            }

            for section_key, section_title in sections_map.items():
                if section_key not in report_data: continue
                section_data = report_data.get(section_key, {})
                table_data_list.append([Paragraph(section_title, styles['h2']), ""] + (["", ""] if len(headers) == 4 else [""])) # Span section title
                
                for acc in section_data.get('accounts', []):
                    row_data = ["", f"{acc['code']} - {acc['name']}", self._format_decimal(acc['balance'])]
                    if len(headers) == 4:
                        comp_val_str = ""
                        if section_data.get('comparative_accounts'):
                            comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                            comp_val_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                        row_data.append(comp_val_str)
                    table_data_list.append(row_data)
                
                total_str = self._format_decimal(section_data.get('total'))
                comp_total_str = ""
                if len(headers) == 4:
                     comp_total_str = self._format_decimal(section_data.get('comparative_total')) if section_data.get('comparative_total') is not None else ""
                
                total_row_data = ["", Paragraph(f"Total {section_title}", styles['Heading3']), total_str]
                if len(headers) == 4: total_row_data.append(comp_total_str)
                table_data_list.append(total_row_data)

            if 'net_profit' in report_data: # For P&L
                net_profit_str = self._format_decimal(report_data.get('net_profit'))
                comp_net_profit_str = ""
                if len(headers) == 4:
                    comp_net_profit_str = self._format_decimal(report_data.get('comparative_net_profit')) if report_data.get('comparative_net_profit') is not None else ""
                
                net_profit_row_data = ["", Paragraph("Net Profit/(Loss)", styles['Heading2']), net_profit_str]
                if len(headers) == 4: net_profit_row_data.append(comp_net_profit_str)
                table_data_list.append(net_profit_row_data)

        else:
            story.append(Paragraph("Report data structure not recognized for detailed PDF export.", styles['Normal']))

        if table_data_list and len(table_data_list) > 1 : # Ensure there's data beyond headers
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
                # Span section titles
                ('SPAN', (0,1), (1,1)), # Example for first section title if it's in row 1 (index after header)
                # This needs to be dynamic based on where section titles appear
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

        if 'debit_accounts' in report_data and 'credit_accounts' in report_data: 
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
        
        elif 'assets' in report_data or 'revenue' in report_data:
            headers = ["Section/Account Code", "Account Name", "Current Period"]
            has_comparative = report_data.get('comparative_date') or report_data.get('comparative_start')
            if has_comparative:
                headers.append("Comparative Period")
            
            for col_num, header_text in enumerate(headers, 1):
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            sections_map = {
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'revenue': 'Revenue', 'expenses': 'Expenses'
            }
            for section_key, section_title in sections_map.items():
                if section_key not in report_data: continue
                section_data = report_data.get(section_key, {})
                
                ws.cell(row=row_num, column=1, value=section_title).font = Font(bold=True, size=12) # type: ignore
                row_num += 1

                for acc in section_data.get('accounts', []):
                    ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                    ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                    ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                    if has_comparative:
                        comp_val = ""
                        if section_data.get('comparative_accounts'):
                            comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                            if comp_acc and comp_acc['balance'] is not None:
                                comp_val = float(comp_acc['balance'])
                        ws.cell(row=row_num, column=4, value=comp_val).number_format = '#,##0.00' # type: ignore
                    row_num += 1
                
                ws.cell(row=row_num, column=2, value=f"Total {section_title}").font = Font(bold=True) # type: ignore
                total_val = section_data.get('total')
                ws.cell(row=row_num, column=3, value=float(total_val) if total_val is not None else "").font = Font(bold=True) # type: ignore
                ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
                if has_comparative:
                    comp_total_val = section_data.get('comparative_total')
                    ws.cell(row=row_num, column=4, value=float(comp_total_val) if comp_total_val is not None else "").font = Font(bold=True) # type: ignore
                    ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            if 'net_profit' in report_data: # For P&L
                row_num += 1
                ws.cell(row=row_num, column=2, value="Net Profit/(Loss)").font = Font(bold=True, size=12) # type: ignore
                net_profit_val = report_data.get('net_profit')
                ws.cell(row=row_num, column=3, value=float(net_profit_val) if net_profit_val is not None else "").font = Font(bold=True) # type: ignore
                ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
                if has_comparative:
                    comp_net_profit_val = report_data.get('comparative_net_profit')
                    ws.cell(row=row_num, column=4, value=float(comp_net_profit_val) if comp_net_profit_val is not None else "").font = Font(bold=True) # type: ignore
                    ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore

        else:
            ws.cell(row=row_num, column=1, value="Report data structure not recognized for Excel export.") # type: ignore

        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            current_width = ws.column_dimensions[column_letter].width # type: ignore
            if current_width == 0: # openpyxl default if not set
                 ws.column_dimensions[column_letter].width = 20 # type: ignore
            else: # Auto size might make it too wide, or too narrow if default value was used.
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
from typing import TYPE_CHECKING # Added TYPE_CHECKING
from datetime import date 

# from app.core.application_core import ApplicationCore # Removed direct import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class TaxReportGenerator:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal for ApplicationCore
        self.app_core = app_core
        # Services would be accessed via self.app_core if needed, e.g., self.app_core.journal_service
        print("TaxReportGenerator initialized (stub).")

    async def generate_gst_audit_file(self, start_date: date, end_date: date):
        print(f"Generating GST Audit File for {start_date} to {end_date} (stub).")
        # Example access: company_name = (await self.app_core.company_settings_service.get_company_settings()).company_name
        return {"filename": "gst_audit.xlsx", "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data": b"dummy_excel_data"}

    async def generate_income_tax_schedules(self, fiscal_year_id: int):
        print(f"Generating Income Tax Schedules for fiscal year ID {fiscal_year_id} (stub).")
        return {"schedule_name": "Capital Allowances", "data": []}

```

# app/accounting/__init__.py
```py
# File: app/accounting/__init__.py
# (Content as previously generated, verified)
from .chart_of_accounts_manager import ChartOfAccountsManager
from .journal_entry_manager import JournalEntryManager
from .fiscal_period_manager import FiscalPeriodManager
from .currency_manager import CurrencyManager

__all__ = [
    "ChartOfAccountsManager",
    "JournalEntryManager",
    "FiscalPeriodManager",
    "CurrencyManager",
]

```

# app/accounting/journal_entry_manager.py
```py
# File: app/accounting/journal_entry_manager.py
# Updated for new JournalEntry/Line fields and RecurringPattern model
from typing import List, Optional, Any, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
# from app.core.application_core import ApplicationCore # Removed direct import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        self.sequence_generator = sequence_generator 
        self.app_core = app_core

    async def create_journal_entry(self, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # Validation for balanced entry is in Pydantic model JournalEntryData
        
        fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date)
        if not fiscal_period: 
            return Result.failure([f"No open fiscal period found for the entry date {entry_data.entry_date}."])
        
        entry_no_str = await self.sequence_generator.next_sequence("journal_entry", prefix="JE-")
        current_user_id = entry_data.user_id

        journal_entry_orm = JournalEntry(
            entry_no=entry_no_str,
            journal_type=entry_data.journal_type,
            entry_date=entry_data.entry_date,
            fiscal_period_id=fiscal_period.id,
            description=entry_data.description,
            reference=entry_data.reference,
            is_recurring=entry_data.is_recurring, 
            recurring_pattern_id=entry_data.recurring_pattern_id, 
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            created_by_user_id=current_user_id, # Corrected field name
            updated_by_user_id=current_user_id  # Corrected field name
        )
        
        for i, line_dto in enumerate(entry_data.lines, 1):
            account = await self.account_service.get_by_id(line_dto.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
            
            line_orm = JournalEntryLine(
                line_number=i,
                account_id=line_dto.account_id,
                description=line_dto.description,
                debit_amount=line_dto.debit_amount,
                credit_amount=line_dto.credit_amount,
                currency_code=line_dto.currency_code, 
                exchange_rate=line_dto.exchange_rate,
                tax_code=line_dto.tax_code, 
                tax_amount=line_dto.tax_amount,
                dimension1_id=line_dto.dimension1_id, 
                dimension2_id=line_dto.dimension2_id  
            )
            journal_entry_orm.lines.append(line_orm)
        
        try:
            saved_entry = await self.journal_service.save(journal_entry_orm)
            return Result.success(saved_entry)
        except Exception as e:
            return Result.failure([f"Failed to save journal entry: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        entry = await self.journal_service.get_by_id(entry_id)
        if not entry:
            return Result.failure([f"Journal entry ID {entry_id} not found."])
        
        if entry.is_posted:
            return Result.failure([f"Journal entry '{entry.entry_no}' is already posted."])
        
        fiscal_period = await self.fiscal_period_service.get_by_id(entry.fiscal_period_id)
        if not fiscal_period or fiscal_period.status != 'Open': 
            return Result.failure([f"Cannot post to a non-open fiscal period. Current status: {fiscal_period.status if fiscal_period else 'Unknown' }."])
        
        entry.is_posted = True
        entry.updated_by_user_id = user_id # Corrected field name
        
        try:
            updated_entry_orm = await self.journal_service.save(entry) 
            return Result.success(updated_entry_orm)
        except Exception as e:
            return Result.failure([f"Failed to post journal entry: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        original_entry = await self.journal_service.get_by_id(entry_id) 
        if not original_entry:
            return Result.failure([f"Journal entry ID {entry_id} not found for reversal."])
        
        if not original_entry.is_posted:
            return Result.failure(["Only posted entries can be reversed."])
        
        if original_entry.is_reversed or original_entry.reversing_entry_id is not None:
            return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed or marked as having a reversing entry."])

        reversal_fiscal_period = await self.fiscal_period_service.get_by_date(reversal_date)
        if not reversal_fiscal_period:
            return Result.failure([f"No open fiscal period found for reversal date {reversal_date}."])

        reversal_entry_no = await self.sequence_generator.next_sequence("journal_entry", prefix="RJE-")
        
        reversal_lines_data = []
        for orig_line in original_entry.lines:
            reversal_lines_data.append(JournalEntryLineData(
                account_id=orig_line.account_id,
                description=f"Reversal: {orig_line.description or ''}",
                debit_amount=orig_line.credit_amount, 
                credit_amount=orig_line.debit_amount, 
                currency_code=orig_line.currency_code,
                exchange_rate=orig_line.exchange_rate,
                tax_code=orig_line.tax_code, 
                tax_amount=-orig_line.tax_amount, 
                dimension1_id=orig_line.dimension1_id,
                dimension2_id=orig_line.dimension2_id
            ))
        
        reversal_entry_data = JournalEntryData(
            journal_type=original_entry.journal_type,
            entry_date=reversal_date,
            description=description or f"Reversal of entry {original_entry.entry_no}",
            reference=f"REV:{original_entry.entry_no}",
            user_id=user_id,
            lines=reversal_lines_data,
            source_type="JournalEntryReversal",
            source_id=original_entry.id 
        )
        
        create_reversal_result = await self.create_journal_entry(reversal_entry_data)
        if not create_reversal_result.is_success:
            return create_reversal_result 
        
        saved_reversal_entry = create_reversal_result.value
        assert saved_reversal_entry is not None 

        original_entry.is_reversed = True
        original_entry.reversing_entry_id = saved_reversal_entry.id
        original_entry.updated_by_user_id = user_id # Corrected field name
        
        try:
            await self.journal_service.save(original_entry)
            return Result.success(saved_reversal_entry) 
        except Exception as e:
            return Result.failure([f"Failed to finalize reversal: {str(e)}"])


    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        next_date = last_date
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                # Try to set to specific day, handle month ends carefully
                try:
                    next_date = next_date.replace(day=day_of_month)
                except ValueError: # Day is out of range for month (e.g. Feb 30)
                    # Go to last day of that month
                    next_date = next_date + relativedelta(day=31) # this will clamp to last day
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month: # And if month is specified (e.g. via template JE's date's month)
                 try:
                    next_date = next_date.replace(day=day_of_month, month=last_date.month)
                 except ValueError:
                    next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)

        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            if day_of_week is not None: # 0=Monday, 6=Sunday for relativedelta, but schema is 0=Sunday
                # Adjust day_of_week from schema (0=Sun) to dateutil (0=Mon) if needed.
                # For simplicity, assuming day_of_week aligns or is handled by direct addition.
                # This part needs more careful mapping if day_of_week from schema has different convention.
                # relativedelta(weekday=MO(+interval)) where MO is a constant.
                 pass # Complex, for now just interval based
        elif frequency == 'Daily':
            next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                 try:
                    next_date = next_date.replace(day=day_of_month)
                 except ValueError:
                    next_date = next_date + relativedelta(day=31)
        else:
            raise NotImplementedError(f"Frequency '{frequency}' not yet supported for next date calculation.")
        return next_date


    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date)
        
        generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.next_generation_date: # Should not happen if get_recurring_patterns_due is correct
                print(f"Warning: Pattern '{pattern.name}' has no next_generation_date, skipping.")
                continue

            entry_date_for_new_je = pattern.next_generation_date

            template_entry = await self.journal_service.get_by_id(pattern.template_entry_id) 
            if not template_entry:
                generated_results.append(Result.failure([f"Template JE ID {pattern.template_entry_id} for pattern '{pattern.name}' not found."]))
                continue
            
            new_je_lines_data = [
                JournalEntryLineData(
                    account_id=line.account_id, description=line.description,
                    debit_amount=line.debit_amount, credit_amount=line.credit_amount,
                    currency_code=line.currency_code, exchange_rate=line.exchange_rate,
                    tax_code=line.tax_code, tax_amount=line.tax_amount,
                    dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id
                ) for line in template_entry.lines
            ]
            
            new_je_data = JournalEntryData(
                journal_type=template_entry.journal_type,
                entry_date=entry_date_for_new_je,
                description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})",
                reference=template_entry.reference,
                user_id=user_id, 
                lines=new_je_lines_data,
                recurring_pattern_id=pattern.id, 
                source_type="RecurringPattern",
                source_id=pattern.id
            )
            
            create_result = await self.create_journal_entry(new_je_data)
            generated_results.append(create_result)
            
            if create_result.is_success:
                pattern.last_generated_date = entry_date_for_new_je
                try:
                    pattern.next_generation_date = self._calculate_next_generation_date(
                        pattern.last_generated_date, pattern.frequency, pattern.interval_value,
                        pattern.day_of_month, pattern.day_of_week
                    )
                    if pattern.end_date and pattern.next_generation_date > pattern.end_date:
                        pattern.is_active = False 
                except NotImplementedError:
                    pattern.is_active = False 
                    print(f"Warning: Next generation date calculation not implemented for pattern {pattern.name}, deactivating.")
                
                pattern.updated_by_user_id = user_id # Corrected field name
                await self.journal_service.save_recurring_pattern(pattern)
        
        return generated_results

```

# app/accounting/currency_manager.py
```py
# File: app/accounting/currency_manager.py
# (Content as previously generated, verified - needs TYPE_CHECKING for ApplicationCore)
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.accounting_services import CurrencyService, ExchangeRateService 
from typing import Optional, List, Any, TYPE_CHECKING
from datetime import date
from decimal import Decimal
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class CurrencyManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        # Assuming these service properties exist on app_core and are correctly typed there
        self.currency_service: CurrencyService = app_core.currency_repo_service # type: ignore 
        self.exchange_rate_service: ExchangeRateService = app_core.exchange_rate_service # type: ignore
    
    async def get_active_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all_active()

    async def get_exchange_rate(self, from_currency_code: str, to_currency_code: str, rate_date: date) -> Optional[Decimal]:
        rate_obj = await self.exchange_rate_service.get_rate_for_date(from_currency_code, to_currency_code, rate_date)
        return rate_obj.exchange_rate_value if rate_obj else None

    async def update_exchange_rate(self, from_code:str, to_code:str, r_date:date, rate:Decimal, user_id:int) -> Result[ExchangeRate]:
        existing_rate = await self.exchange_rate_service.get_rate_for_date(from_code, to_code, r_date)
        orm_object: ExchangeRate
        if existing_rate:
            existing_rate.exchange_rate_value = rate
            existing_rate.updated_by_user_id = user_id
            orm_object = existing_rate
        else:
            orm_object = ExchangeRate(
                from_currency_code=from_code, to_currency_code=to_code, rate_date=r_date,
                exchange_rate_value=rate, 
                created_by_user_id=user_id, updated_by_user_id=user_id 
            )
        
        saved_obj = await self.exchange_rate_service.save(orm_object)
        return Result.success(saved_obj)

    async def get_all_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all()

    async def get_currency_by_code(self, code: str) -> Optional[Currency]:
        return await self.currency_service.get_by_id(code)

```

# app/accounting/chart_of_accounts_manager.py
```py
# File: app/accounting/chart_of_accounts_manager.py
# (Content previously updated to use AccountCreateData/UpdateData, ensure consistency)
# Key: Uses AccountService. User ID comes from DTO which inherits UserAuditData.
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from app.models.accounting.account import Account 
from app.services.account_service import AccountService 
from app.utils.result import Result
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData, AccountValidator
# from app.core.application_core import ApplicationCore # Removed direct import
from decimal import Decimal
from datetime import date # Added for type hint in deactivate_account

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class ChartOfAccountsManager:
    def __init__(self, account_service: AccountService, app_core: "ApplicationCore"):
        self.account_service = account_service
        self.account_validator = AccountValidator() 
        self.app_core = app_core 

    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        validation_result = self.account_validator.validate_create(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        existing = await self.account_service.get_by_code(account_data.code)
        if existing:
            return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        account = Account(
            code=account_data.code, name=account_data.name,
            account_type=account_data.account_type, sub_type=account_data.sub_type,
            tax_treatment=account_data.tax_treatment, gst_applicable=account_data.gst_applicable,
            description=account_data.description, parent_id=account_data.parent_id,
            report_group=account_data.report_group, is_control_account=account_data.is_control_account,
            is_bank_account=account_data.is_bank_account, opening_balance=account_data.opening_balance,
            opening_balance_date=account_data.opening_balance_date, is_active=account_data.is_active,
            created_by_user_id=current_user_id, 
            updated_by_user_id=current_user_id 
        )
        
        try:
            saved_account = await self.account_service.save(account)
            return Result.success(saved_account)
        except Exception as e:
            return Result.failure([f"Failed to save account: {str(e)}"])
    
    async def update_account(self, account_data: AccountUpdateData) -> Result[Account]:
        existing_account = await self.account_service.get_by_id(account_data.id)
        if not existing_account:
            return Result.failure([f"Account with ID {account_data.id} not found."])
        
        validation_result = self.account_validator.validate_update(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        if account_data.code != existing_account.code:
            code_exists = await self.account_service.get_by_code(account_data.code)
            if code_exists and code_exists.id != existing_account.id:
                return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        existing_account.code = account_data.code; existing_account.name = account_data.name
        existing_account.account_type = account_data.account_type; existing_account.sub_type = account_data.sub_type
        existing_account.tax_treatment = account_data.tax_treatment; existing_account.gst_applicable = account_data.gst_applicable
        existing_account.description = account_data.description; existing_account.parent_id = account_data.parent_id
        existing_account.report_group = account_data.report_group; existing_account.is_control_account = account_data.is_control_account
        existing_account.is_bank_account = account_data.is_bank_account; existing_account.opening_balance = account_data.opening_balance
        existing_account.opening_balance_date = account_data.opening_balance_date; existing_account.is_active = account_data.is_active
        existing_account.updated_by_user_id = current_user_id
        
        try:
            updated_account = await self.account_service.save(existing_account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to update account: {str(e)}"])
            
    async def deactivate_account(self, account_id: int, user_id: int) -> Result[Account]:
        account = await self.account_service.get_by_id(account_id)
        if not account:
            return Result.failure([f"Account with ID {account_id} not found."])
        
        if not account.is_active:
             return Result.failure([f"Account '{account.code}' is already inactive."])

        if not hasattr(self.app_core, 'journal_service'): 
            return Result.failure(["Journal service not available for balance check."])

        total_current_balance = await self.app_core.journal_service.get_account_balance(account_id, date.today()) 

        if total_current_balance != Decimal(0):
            return Result.failure([f"Cannot deactivate account '{account.code}' as it has a non-zero balance ({total_current_balance:.2f})."])

        account.is_active = False
        account.updated_by_user_id = user_id 
        
        try:
            updated_account = await self.account_service.save(account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to deactivate account: {str(e)}"])

    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        try:
            tree = await self.account_service.get_account_tree(active_only=active_only)
            return tree 
        except Exception as e:
            print(f"Error getting account tree: {e}") 
            return []

    async def get_accounts_for_selection(self, account_type: Optional[str] = None, active_only: bool = True) -> List[Account]:
        if account_type:
            return await self.account_service.get_by_type(account_type, active_only=active_only)
        elif active_only:
            return await self.account_service.get_all_active()
        else:
            # Assuming get_all() exists on account_service, if not, this path needs adjustment
            if hasattr(self.account_service, 'get_all'):
                 return await self.account_service.get_all()
            else: # Fallback to active if get_all not present for some reason
                 return await self.account_service.get_all_active()

```

# app/accounting/fiscal_period_manager.py
```py
# File: app/accounting/fiscal_period_manager.py
from typing import List, Optional, TYPE_CHECKING # Removed Any, will use specific type
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select # Added for explicit select usage

from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from app.utils.pydantic_models import FiscalYearCreateData 
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from sqlalchemy.ext.asyncio import AsyncSession # For session type hint

class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service 
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service 
        
    async def create_fiscal_year_and_periods(self, fy_data: FiscalYearCreateData) -> Result[FiscalYear]:
        if fy_data.start_date >= fy_data.end_date:
            return Result.failure(["Fiscal year start date must be before end date."])

        existing_by_name = await self.fiscal_year_service.get_by_name(fy_data.year_name)
        if existing_by_name:
            return Result.failure([f"A fiscal year with the name '{fy_data.year_name}' already exists."])

        overlapping_fy = await self.fiscal_year_service.get_by_date_overlap(fy_data.start_date, fy_data.end_date)
        if overlapping_fy:
            return Result.failure([f"The proposed date range overlaps with existing fiscal year '{overlapping_fy.year_name}' ({overlapping_fy.start_date} - {overlapping_fy.end_date})."])

        async with self.app_core.db_manager.session() as session: # type: ignore # session is AsyncSession here
            fy = FiscalYear(
                year_name=fy_data.year_name, 
                start_date=fy_data.start_date, 
                end_date=fy_data.end_date, 
                created_by_user_id=fy_data.user_id, 
                updated_by_user_id=fy_data.user_id,
                is_closed=False 
            )
            session.add(fy)
            await session.flush() 
            await session.refresh(fy) 

            if fy_data.auto_generate_periods and fy_data.auto_generate_periods in ["Month", "Quarter"]:
                # Pass the existing session to the internal method
                period_generation_result = await self._generate_periods_for_year_internal(
                    fy, fy_data.auto_generate_periods, fy_data.user_id, session # Pass session
                )
                if not period_generation_result.is_success:
                    # No need to explicitly rollback here, 'async with session' handles it on exception.
                    # If period_generation_result itself raises an exception that's caught outside,
                    # the session context manager will rollback.
                    # If it returns a failure Result, we need to raise an exception to trigger rollback
                    # or handle it such that the fiscal year is not considered fully created.
                    # For now, let's assume if period generation fails, we raise to rollback.
                    # This means _generate_periods_for_year_internal should raise on critical failure.
                    # Or, the manager can decide to keep the FY and return warnings.
                    # Let's make it so that failure to generate periods makes the whole operation fail.
                    raise Exception(f"Failed to generate periods for '{fy.year_name}': {', '.join(period_generation_result.errors)}")
            
            # If we reach here, commit will happen automatically when 'async with session' exits.
            return Result.success(fy)
        
        # This return Result.failure is less likely to be hit due to `async with` handling exceptions
        return Result.failure(["An unexpected error occurred outside the transaction for fiscal year creation."])


    async def _generate_periods_for_year_internal(self, fiscal_year: FiscalYear, period_type: str, user_id: int, session: "AsyncSession") -> Result[List[FiscalPeriod]]:
        if not fiscal_year or not fiscal_year.id:
            # This should raise an exception to trigger rollback in the calling method
            raise ValueError("Valid FiscalYear object with an ID must be provided for period generation.")
        
        stmt_existing = select(FiscalPeriod).where(
            FiscalPeriod.fiscal_year_id == fiscal_year.id,
            FiscalPeriod.period_type == period_type
        )
        existing_periods_result = await session.execute(stmt_existing)
        if existing_periods_result.scalars().first():
             raise ValueError(f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'.")


        periods: List[FiscalPeriod] = []
        current_start_date = fiscal_year.start_date
        fy_end_date = fiscal_year.end_date
        period_number = 1

        while current_start_date <= fy_end_date:
            current_end_date: date
            period_name: str

            if period_type == "Month":
                current_end_date = current_start_date + relativedelta(months=1) - relativedelta(days=1)
                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"{current_start_date.strftime('%B %Y')}"
            
            elif period_type == "Quarter":
                month_end_of_third_month = current_start_date + relativedelta(months=2, day=1) + relativedelta(months=1) - relativedelta(days=1)
                current_end_date = month_end_of_third_month
                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"Q{period_number} {fiscal_year.year_name}"
            else: 
                raise ValueError(f"Invalid period type '{period_type}' during generation.")

            fp = FiscalPeriod(
                fiscal_year_id=fiscal_year.id, name=period_name,
                start_date=current_start_date, end_date=current_end_date,
                period_type=period_type, status="Open", period_number=period_number,
                is_adjustment=False,
                created_by_user_id=user_id, updated_by_user_id=user_id
            )
            session.add(fp) 
            periods.append(fp)

            if current_end_date >= fy_end_date: break 
            current_start_date = current_end_date + relativedelta(days=1)
            period_number += 1
        
        await session.flush() # Flush within the session passed by the caller
        for p in periods: 
            await session.refresh(p)
            
        return Result.success(periods)

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        # The service's update method will handle the commit with its own session
        updated_period = await self.fiscal_period_service.update(period) 
        return Result.success(updated_period)

    async def reopen_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Open': return Result.failure(["Period is already open."])
        if period.status == 'Archived': return Result.failure(["Cannot reopen an archived period."])
        
        fiscal_year = await self.fiscal_year_service.get_by_id(period.fiscal_year_id)
        if fiscal_year and fiscal_year.is_closed:
            return Result.failure(["Cannot reopen period as its fiscal year is closed."])

        period.status = 'Open'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def get_current_fiscal_period(self, target_date: Optional[date] = None) -> Optional[FiscalPeriod]:
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)

    async def get_all_fiscal_years(self) -> List[FiscalYear]:
        return await self.fiscal_year_service.get_all()

    async def get_fiscal_year_by_id(self, fy_id: int) -> Optional[FiscalYear]:
        return await self.fiscal_year_service.get_by_id(fy_id)

    async def get_periods_for_fiscal_year(self, fiscal_year_id: int) -> List[FiscalPeriod]:
        return await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year_id)

    async def close_fiscal_year(self, fiscal_year_id: int, user_id: int) -> Result[FiscalYear]:
        fy = await self.fiscal_year_service.get_by_id(fiscal_year_id)
        if not fy:
            return Result.failure([f"Fiscal Year ID {fiscal_year_id} not found."])
        if fy.is_closed:
            return Result.failure([f"Fiscal Year '{fy.year_name}' is already closed."])

        periods = await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year_id)
        open_periods = [p for p in periods if p.status == 'Open']
        if open_periods:
            return Result.failure([f"Cannot close fiscal year '{fy.year_name}'. Following periods are still open: {[p.name for p in open_periods]}"])
        
        print(f"Performing year-end closing entries for FY '{fy.year_name}' (conceptual)...")

        fy.is_closed = True
        fy.closed_date = datetime.utcnow() 
        fy.closed_by_user_id = user_id
        fy.updated_by_user_id = user_id 
        
        try:
            updated_fy = await self.fiscal_year_service.save(fy)
            return Result.success(updated_fy)
        except Exception as e:
            return Result.failure([f"Error closing fiscal year: {str(e)}"])

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

# resources/icons/banking.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h3v7H4v-7zm6.5 0h3v7h-3v-7zM2 19h20v3H2v-3zm15-9h3v7h-3v-7zm-5-9L2 6v2h20V6L12 1z"/></svg>

```

# resources/icons/vendors.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M16.5 12c1.38 0 2.5-1.12 2.5-2.5S17.88 7 16.5 7C15.12 7 14 8.12 14 9.5s1.12 2.5 2.5 2.5zM9 11c1.66 0 2.99-1.34 2.99-3S10.66 5 9 5C7.34 5 6 6.34 6 8s1.34 3 3 3zm7.5 3c-1.83 0-5.5.92-5.5 2.75V19h11v-2.25c0-1.83-3.67-2.75-5.5-2.75zM9 13c-2.33 0-7 1.17-7 3.5V19h7v-2.5c0-.85.33-2.34 2.37-3.47C10.5 13.1 9.66 13 9 13z"/></svg>

```

# resources/icons/deactivate.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.59-13L12 10.59 8.41 7 7 8.41 10.59 12 7 15.59 8.41 17 12 13.41 15.59 17 17 15.59 13.41 12 17 8.41z"/>
</svg>

```

# resources/icons/post.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>

```

# resources/icons/collapse_all.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M12 18.17L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17zm0-12.34L15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zM19 11h-2v2h2v-2zm-12 0H5v2h2v-2z"/>
  <path d="M0 0h24v24H0z" fill="none"/>
</svg>

```

# resources/icons/restore.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8H12z"/></svg>

```

# resources/icons/refresh.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
</svg>

```

# resources/icons/exit.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>

```

# resources/icons/about.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-5h2v-2h-2v2zm0-4h2V7h-2v4z"/></svg>

```

# resources/icons/settings.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>

```

# resources/icons/accounting.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h16v2H4v-2zm0 4h16v2H4v-2zm0-8h16v2H4V6zm0 12h10v2H4v-2zM16 18h4v2h-4v-2z"/></svg>

```

# resources/icons/reports.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>

```

# resources/icons/new_company.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>

```

# resources/icons/remove.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 13H5v-2h14v2z"/></svg>

```

# resources/icons/preferences.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>

```

# resources/icons/transactions.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2zM4 18V8h2v10H4zm4 0V8h8v10H8zm12 0h-2V8h2v10z"/>
  <path d="M0 0h24v24H0V0z" fill="none"/>
</svg>

```

# resources/icons/customers.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>

```

# resources/icons/backup.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>

```

# resources/icons/filter.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
</svg>

```

# resources/icons/help.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>

```

# resources/icons/view.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>

```

# resources/icons/add.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>

```

# resources/icons/reverse.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C20.36 11.36 16.79 8 12.5 8z"/></svg>

```

# resources/icons/expand_all.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M12 5.83L15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zm0 12.34L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17zM5 13h2v-2H5v2zm12 0h2v-2h-2v2z"/>
  <path d="M0 0h24v24H0z" fill="none"/>
</svg>

```

# resources/icons/open_company.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z"/></svg>

```

# resources/icons/edit.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
</svg>

```

# resources/icons/dashboard.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect>
</svg>

```

# resources/resources.qrc
```qrc
# File: resources/resources.qrc
# (Commented QRC structure as provided before)
"""
<RCC>
  <qresource prefix="/">
    <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
    <file alias="icons/accounting.svg">icons/accounting.svg</file>
    <file alias="icons/customers.svg">icons/customers.svg</file>
    <file alias="icons/vendors.svg">icons/vendors.svg</file>
    <file alias="icons/banking.svg">icons/banking.svg</file>
    <file alias="icons/reports.svg">icons/reports.svg</file>
    <file alias="icons/settings.svg">icons/settings.svg</file>
    <file alias="icons/new_company.svg">icons/new_company.svg</file>
    <file alias="icons/open_company.svg">icons/open_company.svg</file>
    <file alias="icons/backup.svg">icons/backup.svg</file>
    <file alias="icons/restore.svg">icons/restore.svg</file>
    <file alias="icons/exit.svg">icons/exit.svg</file>
    <file alias="icons/preferences.svg">icons/preferences.svg</file>
    <file alias="icons/help.svg">icons/help.svg</file>
    <file alias="icons/about.svg">icons/about.svg</file>
    <file alias="icons/filter.svg">icons/filter.svg</file>
    <file alias="icons/expand_all.svg">icons/expand_all.svg</file>
    <file alias="icons/collapse_all.svg">icons/collapse_all.svg</file>
    <file alias="icons/refresh.svg">icons/refresh.svg</file>
    <file alias="icons/edit.svg">icons/edit.svg</file>
    <file alias="icons/transactions.svg">icons/transactions.svg</file>
    <file alias="icons/deactivate.svg">icons/deactivate.svg</file>
    <file alias="images/splash.png">images/splash.png</file>
  </qresource>
</RCC>
"""

```

# data/report_templates/balance_sheet_default.json
```json
# File: data/report_templates/balance_sheet_default.json
# (Content as provided before - example structure)
"""
{
  "report_name": "Balance Sheet",
  "sections": [
    {
      "title": "Assets",
      "account_type": "Asset",
      "sub_sections": [
        {"title": "Current Assets", "account_sub_type_pattern": "Current Asset.*|Accounts Receivable|Cash.*"},
        {"title": "Non-Current Assets", "account_sub_type_pattern": "Fixed Asset.*|Non-Current Asset.*"}
      ]
    },
    {
      "title": "Liabilities",
      "account_type": "Liability",
      "sub_sections": [
        {"title": "Current Liabilities", "account_sub_type_pattern": "Current Liability.*|Accounts Payable|GST Payable"},
        {"title": "Non-Current Liabilities", "account_sub_type_pattern": "Non-Current Liability.*|Loan.*"}
      ]
    },
    {
      "title": "Equity",
      "account_type": "Equity"
    }
  ],
  "options": {
    "show_zero_balance": false,
    "comparative_periods": 1
  }
}
"""

```

# data/tax_codes/sg_gst_codes_2023.csv
```csv
# File: data/tax_codes/sg_gst_codes_2023.csv
# (Content as provided before, verified against initial_data.sql SYS-GST-* accounts)
"""Code,Description,TaxType,Rate,IsActive,AffectsAccountCode
SR,Standard-Rated Supplies,GST,7.00,TRUE,SYS-GST-OUTPUT
ZR,Zero-Rated Supplies,GST,0.00,TRUE,
ES,Exempt Supplies,GST,0.00,TRUE,
TX,Taxable Purchases (Standard-Rated),GST,7.00,TRUE,SYS-GST-INPUT
BL,Blocked Input Tax (e.g. Club Subscriptions),GST,7.00,TRUE,
OP,Out-of-Scope Supplies,GST,0.00,TRUE,
"""

```

# data/chart_of_accounts/general_template.csv
```csv
# File: data/chart_of_accounts/general_template.csv
# (Content as provided before, verified with new Account fields)
"""Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode,ReportGroup,IsControlAccount,IsBankAccount,OpeningBalance,OpeningBalanceDate
1000,ASSETS,Asset,,,,,,,,0.00,
1100,Current Assets,Asset,,,,1000,CURRENT_ASSETS,FALSE,FALSE,0.00,
1110,Cash and Bank,Asset,Current Asset,,,1100,CASH_BANK,FALSE,TRUE,0.00,
1111,Main Bank Account SGD,Asset,Cash and Cash Equivalents,Non-Taxable,FALSE,1110,CASH_BANK,FALSE,TRUE,1000.00,2023-01-01
1112,Petty Cash,Asset,Cash and Cash Equivalents,Non-Taxable,FALSE,1110,CASH_BANK,FALSE,FALSE,100.00,2023-01-01
1120,Accounts Receivable,Asset,Accounts Receivable,,,1100,ACCOUNTS_RECEIVABLE,TRUE,FALSE,500.00,2023-01-01
1130,Inventory,Asset,Inventory,,,1100,INVENTORY,TRUE,FALSE,0.00,
1200,Non-Current Assets,Asset,,,,1000,NON_CURRENT_ASSETS,FALSE,FALSE,0.00,
1210,Property, Plant & Equipment,Asset,Fixed Assets,,,1200,PPE,FALSE,FALSE,0.00,
1211,Office Equipment,Asset,Fixed Assets,,,1210,PPE,FALSE,FALSE,5000.00,2023-01-01
1212,Accumulated Depreciation - Office Equipment,Asset,Fixed Assets,,,1210,PPE_ACCUM_DEPR,FALSE,FALSE,-500.00,2023-01-01
2000,LIABILITIES,Liability,,,,,,,,0.00,
2100,Current Liabilities,Liability,,,,2000,CURRENT_LIABILITIES,FALSE,FALSE,0.00,
2110,Accounts Payable,Liability,Accounts Payable,,,2100,ACCOUNTS_PAYABLE,TRUE,FALSE,0.00,
2120,GST Payable,Liability,GST Payable,Taxable,TRUE,2100,TAX_LIABILITIES,FALSE,FALSE,0.00,
2200,Non-Current Liabilities,Liability,,,,2000,NON_CURRENT_LIABILITIES,FALSE,FALSE,0.00,
2210,Bank Loan (Long Term),Liability,Long-term Liability,,,2200,LOANS_PAYABLE,FALSE,FALSE,0.00,
3000,EQUITY,Equity,,,,,,,,0.00,
3100,Owner's Capital,Equity,Owner''s Equity,,,3000,OWNERS_EQUITY,FALSE,FALSE,0.00,
3200,Retained Earnings,Equity,Retained Earnings,,,3000,RETAINED_EARNINGS,FALSE,FALSE,0.00,SYS-RETAINED-EARNINGS
4000,REVENUE,Revenue,,,,,,,,0.00,
4100,Sales Revenue,Revenue,Sales,Taxable,TRUE,4000,OPERATING_REVENUE,FALSE,FALSE,0.00,
4200,Service Revenue,Revenue,Services,Taxable,TRUE,4000,OPERATING_REVENUE,FALSE,FALSE,0.00,
5000,COST OF SALES,Expense,,,,,,,,0.00,
5100,Cost of Goods Sold,Expense,Cost of Sales,Taxable,TRUE,5000,COST_OF_SALES,FALSE,FALSE,0.00,
6000,OPERATING EXPENSES,Expense,,,,,,,,0.00,
6100,Salaries & Wages,Expense,Operating Expenses,Non-Taxable,FALSE,6000,SALARIES,FALSE,FALSE,0.00,
6110,Rent Expense,Expense,Operating Expenses,Taxable,TRUE,6000,RENT,FALSE,FALSE,0.00,
6120,Utilities Expense,Expense,Operating Expenses,Taxable,TRUE,6000,UTILITIES,FALSE,FALSE,0.00,
7000,OTHER INCOME,Revenue,,,,,,,,0.00,
7100,Interest Income,Revenue,Other Income,Taxable,FALSE,7000,INTEREST_INCOME,FALSE,FALSE,0.00,
8000,OTHER EXPENSES,Expense,,,,,,,,0.00,
8100,Bank Charges,Expense,Other Expenses,Non-Taxable,FALSE,8000,BANK_CHARGES,FALSE,FALSE,0.00,
"""

```

# data/chart_of_accounts/retail_template.csv
```csv
# File: data/chart_of_accounts/retail_template.csv
# (Content as provided before, verified with new Account fields)
"""Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode,ReportGroup,IsControlAccount,IsBankAccount,OpeningBalance,OpeningBalanceDate
1135,Inventory - Retail Goods,Asset,Inventory,Non-Taxable,FALSE,1130,INVENTORY_RETAIL,TRUE,FALSE,5000.00,2023-01-01
4110,Sales Returns & Allowances,Revenue,Sales Adjustments,Taxable,TRUE,4000,REVENUE_ADJUSTMENTS,FALSE,FALSE,0.00,
4120,Sales Discounts,Revenue,Sales Adjustments,Taxable,TRUE,4000,REVENUE_ADJUSTMENTS,FALSE,FALSE,0.00,
5110,Purchase Returns & Allowances,Expense,Cost of Sales Adjustments,Taxable,TRUE,5100,COGS_ADJUSTMENTS,FALSE,FALSE,0.00,
5120,Purchase Discounts,Expense,Cost of Sales Adjustments,Taxable,TRUE,5100,COGS_ADJUSTMENTS,FALSE,FALSE,0.00,
6200,Shop Supplies Expense,Expense,Operating Expenses,Taxable,TRUE,6000,SHOP_SUPPLIES,FALSE,FALSE,0.00,
"""

```

# /home/pete/.config/SGBookkeeper/config.ini
```ini
[Database]
username = sgbookkeeper_user
password = SGkeeperPass123
host = localhost
port = 5432
database = sg_bookkeeper
echo_sql = False

```

