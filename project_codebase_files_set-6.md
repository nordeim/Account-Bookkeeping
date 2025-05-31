# app/reporting/financial_statement_generator.py
```py
# File: app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import date, timedelta 
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService 
from app.services.core_services import CompanySettingsService 
from app.services.accounting_services import AccountTypeService, DimensionService # Added DimensionService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService, 
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None,
                 dimension_service: Optional[DimensionService] = None # New dependency
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self.dimension_service = dimension_service # New
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    # ... (_get_account_type_map, _calculate_account_balances_for_report, _calculate_account_period_activity_for_report,
    #      generate_balance_sheet, generate_profit_loss, generate_trial_balance, generate_income_tax_computation,
    #      generate_gst_f5 - unchanged from file set 7)
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
        # Note: Opening balance calculation for GL should also consider dimensions if they apply to OB.
        # For now, assume OB is not dimension-specific for simplicity. A more advanced system
        # might require passing dimension filters to get_account_balance if OB JEs have dimensions.
        opening_balance = await self.journal_service.get_account_balance(account_id, ob_date)

        lines: List[JournalEntryLine] = await self.journal_service.get_posted_lines_for_account_in_range(
            account_id, start_date, end_date, dimension1_id, dimension2_id # Pass dimensions here
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
                "dim1_id": line.dimension1_id, "dim2_id": line.dimension2_id # Include dim IDs in output
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
# app/reporting/report_engine.py
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepInFrame
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm 
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
from decimal import Decimal, InvalidOperation
from datetime import date

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(name='ReportTitle', parent=self.styles['h1'], alignment=TA_CENTER, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='ReportSubTitle', parent=self.styles['h2'], alignment=TA_CENTER, fontSize=12, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['h3'], fontSize=11, spaceBefore=0.2*inch, spaceAfter=0.1*inch, textColor=colors.HexColor("#2F5496")))
        self.styles.add(ParagraphStyle(name='AccountName', parent=self.styles['Normal'], leftIndent=0.2*inch))
        self.styles.add(ParagraphStyle(name='AccountNameBold', parent=self.styles['AccountName'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='Amount', parent=self.styles['Normal'], alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name='AmountBold', parent=self.styles['Amount'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=colors.whitesmoke))
        self.styles.add(ParagraphStyle(name='Footer', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=8))
        self.styles.add(ParagraphStyle(name='NormalRight', parent=self.styles['Normal'], alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name='NormalCenter', parent=self.styles['Normal'], alignment=TA_CENTER))
        self.styles.add(ParagraphStyle(name='GLAccountHeader', parent=self.styles['h3'], fontSize=10, spaceBefore=0.1*inch, spaceAfter=0.05*inch, alignment=TA_LEFT))


    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        title = report_data.get('title', "Financial Report")
        if format_type == "pdf":
            if title == "Balance Sheet":
                return await self._export_balance_sheet_to_pdf(report_data)
            elif title == "Profit & Loss Statement":
                return await self._export_profit_loss_to_pdf(report_data)
            elif title == "Trial Balance": 
                return await self._export_trial_balance_to_pdf(report_data)
            elif title == "General Ledger": 
                return await self._export_general_ledger_to_pdf(report_data)
            else: 
                return self._export_generic_table_to_pdf(report_data) # Fallback for other types
        elif format_type == "excel":
            if title == "Balance Sheet":
                return await self._export_balance_sheet_to_excel(report_data)
            elif title == "Profit & Loss Statement":
                return await self._export_profit_loss_to_excel(report_data)
            elif title == "Trial Balance": 
                return await self._export_trial_balance_to_excel(report_data)
            elif title == "General Ledger": 
                return await self._export_general_ledger_to_excel(report_data)
            else: 
                return self._export_generic_table_to_excel(report_data) # Fallback for other types
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2, show_blank_for_zero: bool = False) -> str:
        if value is None: return "" if show_blank_for_zero else self._format_decimal(Decimal(0), places) # Ensure 0.00 for non-blank zero
        if not isinstance(value, Decimal): 
            try: value = Decimal(str(value))
            except InvalidOperation: return "ERR_DEC" 
        if show_blank_for_zero and value.is_zero(): return ""
        return f"{value:,.{places}f}"

    async def _get_company_name(self) -> str:
        settings = await self.app_core.company_settings_service.get_company_settings()
        return settings.company_name if settings else "Your Company"

    def _add_pdf_header_footer(self, canvas, doc, company_name: str, report_title: str, date_desc: str):
        canvas.saveState()
        page_width = doc.width + doc.leftMargin + doc.rightMargin
        header_y_start = doc.height + doc.topMargin - 0.5*inch
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawCentredString(page_width/2, header_y_start, company_name)
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawCentredString(page_width/2, header_y_start - 0.25*inch, report_title)
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(page_width/2, header_y_start - 0.5*inch, date_desc)
        footer_y = 0.5*inch
        canvas.setFont('Helvetica', 8)
        canvas.drawString(doc.leftMargin, footer_y, f"Generated on: {date.today().strftime('%d %b %Y')}")
        canvas.drawRightString(page_width - doc.rightMargin, footer_y, f"Page {doc.page}")
        canvas.restoreState()

    # --- Balance Sheet Specific PDF ---
    # ... (Method unchanged from previous version)
    async def _export_balance_sheet_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        company_name = await self._get_company_name()
        report_title = report_data.get('title', "Balance Sheet")
        date_desc = report_data.get('report_date_description', "")
        doc = SimpleDocTemplate(buffer, pagesize=A4,rightMargin=0.75*inch, leftMargin=0.75*inch,topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; has_comparative = bool(report_data.get('comparative_date'))
        col_widths = [3.5*inch, 1.5*inch]; 
        if has_comparative: col_widths.append(1.5*inch)
        header_texts = ["Description", "Current Period"]; 
        if has_comparative: header_texts.append("Comparative")
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]
        def build_section_data(section_key: str, title: str):
            data: List[List[Any]] = []; section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""]))
            for acc in section.get('accounts', []):
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']), Paragraph(self._format_decimal(acc['balance']), self.styles['Amount'])]
                if has_comparative:
                    comp_bal_str = ""; 
                    if section.get('comparative_accounts'):
                        comp_acc_list = section['comparative_accounts']; comp_acc_match = next((ca for ca in comp_acc_list if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_bal_str = self._format_decimal(comp_acc_match['balance'])
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)
            total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']), Paragraph(self._format_decimal(section.get('total')), self.styles['AmountBold'])]
            if has_comparative: total_row.append(Paragraph(self._format_decimal(section.get('comparative_total')), self.styles['AmountBold']))
            data.append(total_row); data.append([Spacer(1, 0.1*inch)] * len(col_widths)); return data
        bs_data: List[List[Any]] = [table_header_row]; bs_data.extend(build_section_data('assets', 'Assets')); bs_data.extend(build_section_data('liabilities', 'Liabilities')); bs_data.extend(build_section_data('equity', 'Equity'))
        total_lia_eq_row = [Paragraph("Total Liabilities & Equity", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('total_liabilities_equity')), self.styles['AmountBold'])]
        if has_comparative: total_lia_eq_row.append(Paragraph(self._format_decimal(report_data.get('comparative_total_liabilities_equity')), self.styles['AmountBold']))
        bs_data.append(total_lia_eq_row); bs_table = Table(bs_data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (0, -1), (-1,-1), 1, colors.black), ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),])
        current_row_idx = 1 
        for section_key in ['assets', 'liabilities', 'equity']:
            if section_key in report_data: style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx)); current_row_idx += len(report_data[section_key].get('accounts', [])) + 2 
        bs_table.setStyle(style); story.append(bs_table)
        if report_data.get('is_balanced') is False: story.append(Spacer(1, 0.2*inch)); story.append(Paragraph("Warning: Balance Sheet is out of balance!", ParagraphStyle(name='Warning', parent=self.styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold')))
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    # --- Profit & Loss Specific PDF ---
    # ... (Method unchanged from previous version)
    async def _export_profit_loss_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "Profit & Loss Statement"); date_desc = report_data.get('report_date_description', "")
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; has_comparative = bool(report_data.get('comparative_start'))
        col_widths = [3.5*inch, 1.5*inch]; 
        if has_comparative: col_widths.append(1.5*inch)
        header_texts = ["Description", "Current Period"]; 
        if has_comparative: header_texts.append("Comparative")
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]
        def build_pl_section_data(section_key: str, title: str, is_subtraction: bool = False):
            data: List[List[Any]] = []; section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""]))
            for acc in section.get('accounts', []):
                balance = acc['balance']
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']), Paragraph(self._format_decimal(balance), self.styles['Amount'])]
                if has_comparative:
                    comp_bal_str = ""; 
                    if section.get('comparative_accounts'):
                        comp_acc_list = section['comparative_accounts']; comp_acc_match = next((ca for ca in comp_acc_list if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_bal_str = self._format_decimal(comp_acc_match['balance'])
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)
            total = section.get('total'); total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']), Paragraph(self._format_decimal(total), self.styles['AmountBold'])]
            if has_comparative: comp_total = section.get('comparative_total'); total_row.append(Paragraph(self._format_decimal(comp_total), self.styles['AmountBold']))
            data.append(total_row); data.append([Spacer(1, 0.1*inch)] * len(col_widths)); return data, total, section.get('comparative_total') if has_comparative else None
        pl_data: List[List[Any]] = [table_header_row]
        rev_data, total_revenue, comp_total_revenue = build_pl_section_data('revenue', 'Revenue'); pl_data.extend(rev_data)
        exp_data, total_expenses, comp_total_expenses = build_pl_section_data('expenses', 'Operating Expenses', is_subtraction=True); pl_data.extend(exp_data)
        net_profit = report_data.get('net_profit', Decimal(0)); comp_net_profit = report_data.get('comparative_net_profit')
        net_profit_row = [Paragraph("Net Profit / (Loss)", self.styles['AccountNameBold']), Paragraph(self._format_decimal(net_profit), self.styles['AmountBold'])]
        if has_comparative: net_profit_row.append(Paragraph(self._format_decimal(comp_net_profit), self.styles['AmountBold']))
        pl_data.append(net_profit_row); pl_table = Table(pl_data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (1, -1), (-1,-1), 1, colors.black), ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),])
        current_row_idx = 1
        for section_key in ['revenue', 'expenses']: 
            if section_key in report_data: style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx)); current_row_idx += len(report_data[section_key].get('accounts', [])) + 2
        pl_table.setStyle(style); story.append(pl_table)
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    # --- Trial Balance PDF Export ---
    # ... (Method unchanged from previous version)
    async def _export_trial_balance_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "Trial Balance"); date_desc = report_data.get('report_date_description', f"As of {date.today().strftime('%d %b %Y')}")
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; col_widths = [1.5*inch, 3*inch, 1.25*inch, 1.25*inch]; header_texts = ["Account Code", "Account Name", "Debit", "Credit"]
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]; tb_data: List[List[Any]] = [table_header_row]
        for acc in report_data.get('debit_accounts', []): tb_data.append([Paragraph(acc['code'], self.styles['Normal']), Paragraph(acc['name'], self.styles['Normal']), Paragraph(self._format_decimal(acc['balance']), self.styles['NormalRight']), Paragraph("", self.styles['NormalRight'])])
        for acc in report_data.get('credit_accounts', []): tb_data.append([Paragraph(acc['code'], self.styles['Normal']), Paragraph(acc['name'], self.styles['Normal']), Paragraph("", self.styles['NormalRight']), Paragraph(self._format_decimal(acc['balance']), self.styles['NormalRight'])])
        tb_data.append([Paragraph(""), Paragraph("TOTALS", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('total_debits')), self.styles['AmountBold']), Paragraph(self._format_decimal(report_data.get('total_credits')), self.styles['AmountBold'])])
        tb_table = Table(tb_data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (2, -1), (3, -1), 1, colors.black), ('LINEBELOW', (2, -1), (3, -1), 1, colors.black), ('ALIGN', (2,1), (3,-1), 'RIGHT'),])
        tb_table.setStyle(style); story.append(tb_table)
        if report_data.get('is_balanced') is False: story.append(Spacer(1,0.2*inch)); story.append(Paragraph("Warning: Trial Balance is out of balance!", ParagraphStyle(name='Warning', parent=self.styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold')))
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    # --- General Ledger PDF Export ---
    async def _export_general_ledger_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        company_name = await self._get_company_name()
        report_title = report_data.get('title', "General Ledger")
        # GL report_date_description includes account code and name, so use it directly
        date_desc = report_data.get('report_date_description', "") 

        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                rightMargin=0.5*inch, leftMargin=0.5*inch,
                                topMargin=1.25*inch, bottomMargin=0.75*inch) # Use standard margins for GL header
        story: List[Any] = []

        # Account Specific Header (inside the main story, not page frame)
        story.append(Paragraph(f"Account: {report_data.get('account_code')} - {report_data.get('account_name')}", self.styles['GLAccountHeader']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"Opening Balance: {self._format_decimal(report_data.get('opening_balance'))}", self.styles['AccountNameBold']))
        story.append(Spacer(1, 0.2*inch))

        # Transaction Table
        headers = ["Date", "Entry No.", "JE Description", "Line Description", "Debit", "Credit", "Balance"]
        table_header_row = [Paragraph(h, self.styles['TableHeader']) for h in headers]
        
        gl_data: List[List[Any]] = [table_header_row]
        for txn in report_data.get('transactions', []):
            gl_data.append([
                Paragraph(txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else str(txn['date']), self.styles['NormalCenter']),
                Paragraph(txn['entry_no'], self.styles['Normal']),
                Paragraph(txn.get('je_description','')[:40], self.styles['Normal']), # Truncate for PDF
                Paragraph(txn.get('line_description','')[:40], self.styles['Normal']), # Truncate
                Paragraph(self._format_decimal(txn['debit'], show_blank_for_zero=True), self.styles['NormalRight']),
                Paragraph(self._format_decimal(txn['credit'], show_blank_for_zero=True), self.styles['NormalRight']),
                Paragraph(self._format_decimal(txn['balance']), self.styles['NormalRight'])
            ])
        
        # Column Widths for GL (Landscape A4)
        # Total width available: landscape(A4)[0] - leftMargin - rightMargin = 11.69*inch - 1*inch = 10.69*inch
        col_widths_gl = [0.9*inch, # Date
                         1.0*inch, # Entry No.
                         2.8*inch, # JE Desc
                         2.8*inch, # Line Desc
                         1.0*inch, # Debit
                         1.0*inch, # Credit
                         1.19*inch] # Balance

        gl_table = Table(gl_data, colWidths=col_widths_gl)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,1), (1,-1), 'CENTER'), # Date, Entry No.
            ('ALIGN', (4,1), (6,-1), 'RIGHT'), # Amounts
        ])
        gl_table.setStyle(style)
        story.append(gl_table)
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"Closing Balance: {self._format_decimal(report_data.get('closing_balance'))}", self.styles['AmountBold']))
        
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), 
                         onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc))
        return buffer.getvalue()


    # --- Generic PDF Exporter (Fallback, if ever needed) ---
    def _export_generic_table_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        # This method is now primarily a fallback.
        # Specific GL PDF export will be richer.
        # If GL is called here, it will be very basic.
        self.app_core.logger.warning(f"Using generic PDF export for report: {report_data.get('title')}")
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=0.5*inch, leftMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        story: List[Any] = [Paragraph(report_data.get('title', "Report"), self.styles['h1'])]
        if report_data.get('report_date_description'): story.append(Paragraph(report_data.get('report_date_description'), self.styles['h3']))
        story.append(Spacer(1, 0.2*inch))
        
        # Simplified table creation - assumes flat data structure if this fallback is hit
        data_to_display = report_data.get('data_rows', []) # Expect 'data_rows' if generic
        headers = report_data.get('headers', [])
        if headers and data_to_display:
            table_data: List[List[Any]] = [[Paragraph(str(h), self.styles['TableHeader']) for h in headers]]
            for row_dict in data_to_display:
                table_data.append([Paragraph(str(row_dict.get(h_key, '')), self.styles['Normal']) for h_key in headers]) # Assuming headers are keys
            
            num_cols = len(headers)
            col_widths_generic = [doc.width/num_cols]*num_cols
            table = Table(table_data, colWidths=col_widths_generic)
            table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD"))]))
            story.append(table)
        else: story.append(Paragraph("No data or headers provided for generic export.", self.styles['Normal']))

        doc.build(story)
        return buffer.getvalue()

    # --- Excel Export Methods ---
    # ... (_apply_excel_header_style, _apply_excel_amount_style, _export_balance_sheet_to_excel, _export_profit_loss_to_excel, _export_trial_balance_to_excel - unchanged from previous version)
    def _apply_excel_header_style(self, cell, bold=True, size=12, alignment='center', fill_color: Optional[str]=None):
        cell.font = Font(bold=bold, size=size, color="FFFFFF" if fill_color else "000000")
        if alignment == 'center': cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        elif alignment == 'right': cell.alignment = Alignment(horizontal='right', vertical='center')
        else: cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        if fill_color: cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

    def _apply_excel_amount_style(self, cell, bold=False, underline: Optional[str]=None):
        cell.number_format = '#,##0.00;[Red](#,##0.00);"-"' 
        cell.alignment = Alignment(horizontal='right')
        if bold: cell.font = Font(bold=True)
        if underline: cell.border = Border(bottom=Side(style=underline))
        
    async def _export_balance_sheet_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Balance Sheet"
        company_name = await self._get_company_name(); has_comparative = bool(report_data.get('comparative_date'))
        row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False); row_num += 2
        headers = ["Description", "Current Period"]; 
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col>0 else 'left', fill_color="4F81BD")
        row_num +=1
        def write_section(section_key: str, title: str):
            nonlocal row_num; section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496"); row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'] if acc.get('balance') is not None else 0)))
                if has_comparative:
                    comp_val = None
                    if section.get('comparative_accounts'):
                        comp_acc_match = next((ca for ca in section['comparative_accounts'] if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_val = float(comp_acc_match['balance'])
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val if comp_val is not None else "-"))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True, underline="thin")
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True, underline="thin")
            row_num += 2
        write_section('assets', 'Assets'); write_section('liabilities', 'Liabilities'); write_section('equity', 'Equity')
        ws.cell(row=row_num, column=1, value="Total Liabilities & Equity").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('total_liabilities_equity',0))), bold=True, underline="double")
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_total_liabilities_equity',0))), bold=True, underline="double")
        row_num +=1
        if report_data.get('is_balanced') is False: ws.cell(row=row_num, column=1, value="Warning: Balance Sheet out of balance!").font = Font(color="FF0000", bold=True)
        for i, col_letter in enumerate(['A','B','C'][:len(headers)]): ws.column_dimensions[col_letter].width = 45 if i==0 else 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    async def _export_profit_loss_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Profit and Loss"
        company_name = await self._get_company_name(); has_comparative = bool(report_data.get('comparative_start'))
        row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False); row_num += 2
        headers = ["Description", "Current Period"]; 
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col>0 else 'left', fill_color="4F81BD")
        row_num +=1
        def write_pl_section(section_key: str, title: str):
            nonlocal row_num; section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496"); row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'] if acc.get('balance') is not None else 0)))
                if has_comparative:
                    comp_val = None
                    if section.get('comparative_accounts'):
                        comp_acc_match = next((ca for ca in section['comparative_accounts'] if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_val = float(comp_acc_match['balance'])
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val if comp_val is not None else "-"))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True, underline="thin")
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True, underline="thin")
            row_num +=1
            return section.get('total', Decimal(0)), section.get('comparative_total') if has_comparative else Decimal(0)
        total_revenue, comp_total_revenue = write_pl_section('revenue', 'Revenue')
        row_num +=1 
        total_expenses, comp_total_expenses = write_pl_section('expenses', 'Operating Expenses')
        row_num +=1 
        ws.cell(row=row_num, column=1, value="Net Profit / (Loss)").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('net_profit',0))), bold=True, underline="double")
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_net_profit',0))), bold=True, underline="double")
        for i, col_letter in enumerate(['A','B','C'][:len(headers)]): ws.column_dimensions[col_letter].width = 45 if i==0 else 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()
    
    async def _export_trial_balance_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        # ... (Method unchanged from previous version)
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Trial Balance"; company_name = await self._get_company_name(); row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False, alignment='center'); row_num += 2
        headers = ["Account Code", "Account Name", "Debit", "Credit"]
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD", alignment='center' if col > 1 else 'left')
        row_num += 1
        for acc in report_data.get('debit_accounts', []):
            ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name'])
            self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(acc['balance'] if acc.get('balance') is not None else 0))); ws.cell(row=row_num, column=4, value=None); row_num += 1
        for acc in report_data.get('credit_accounts', []):
            ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name'])
            ws.cell(row=row_num, column=3, value=None); self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(acc['balance'] if acc.get('balance') is not None else 0))); row_num += 1
        row_num +=1; ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True); ws.cell(row=row_num, column=2).alignment = Alignment(horizontal='right')
        self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits', 0))), bold=True, underline="thin")
        self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits', 0))), bold=True, underline="thin")
        if report_data.get('is_balanced', True) is False: row_num +=2; ws.cell(row=row_num, column=1, value="Warning: Trial Balance is out of balance!").font = Font(color="FF0000", bold=True)
        ws.column_dimensions[get_column_letter(1)].width = 15; ws.column_dimensions[get_column_letter(2)].width = 45; ws.column_dimensions[get_column_letter(3)].width = 20; ws.column_dimensions[get_column_letter(4)].width = 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    # --- General Ledger Excel Export ---
    async def _export_general_ledger_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"GL-{report_data.get('account_code', 'Account')}"[:30]
        company_name = await self._get_company_name()

        row_num = 1
        # Report Headers
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14, alignment='center')
        row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12, alignment='center')
        row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False, alignment='center')
        row_num += 2

        # Column Headers
        headers = ["Date", "Entry No.", "JE Description", "Line Description", "Debit", "Credit", "Balance"]
        for col, header_text in enumerate(headers, 1):
            self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD", alignment='center' if col > 3 else 'left')
        row_num += 1
        
        # Opening Balance
        ws.cell(row=row_num, column=4, value="Opening Balance").font = Font(bold=True) # Column D for 'Line Description' aligns with values
        ws.cell(row=row_num, column=4).alignment = Alignment(horizontal='right')
        self._apply_excel_amount_style(ws.cell(row=row_num, column=7, value=float(report_data.get('opening_balance',0))), bold=True)
        row_num += 1

        # Transaction Rows
        for txn in report_data.get('transactions', []):
            ws.cell(row=row_num, column=1, value=txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else txn['date'])
            ws.cell(row=row_num, column=1).alignment = Alignment(horizontal='center')
            ws.cell(row=row_num, column=2, value=txn['entry_no'])
            ws.cell(row=row_num, column=3, value=txn.get('je_description',''))
            ws.cell(row=row_num, column=4, value=txn.get('line_description',''))
            self._apply_excel_amount_style(ws.cell(row=row_num, column=5, value=float(txn['debit'] if txn['debit'] else 0)))
            self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(txn['credit'] if txn['credit'] else 0)))
            self._apply_excel_amount_style(ws.cell(row=row_num, column=7, value=float(txn['balance'])))
            row_num += 1
        
        # Closing Balance
        ws.cell(row=row_num, column=4, value="Closing Balance").font = Font(bold=True)
        ws.cell(row=row_num, column=4).alignment = Alignment(horizontal='right')
        self._apply_excel_amount_style(ws.cell(row=row_num, column=7, value=float(report_data.get('closing_balance',0))), bold=True, underline="thin") # Single underline for CB

        # Column Widths
        ws.column_dimensions[get_column_letter(1)].width = 12  # Date
        ws.column_dimensions[get_column_letter(2)].width = 15  # Entry No
        ws.column_dimensions[get_column_letter(3)].width = 40  # JE Desc
        ws.column_dimensions[get_column_letter(4)].width = 40  # Line Desc
        for i in [5,6,7]: ws.column_dimensions[get_column_letter(i)].width = 18 # Amounts

        excel_bytes_io = BytesIO()
        wb.save(excel_bytes_io)
        return excel_bytes_io.getvalue()

    # --- Generic Excel Exporter (Fallback) ---
    def _export_generic_table_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        # This is now truly a fallback for any other report types
        self.app_core.logger.warning(f"Using generic Excel export for report: {report_data.get('title')}")
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = report_data.get('title', "Report")[:30] # type: ignore
        row_num = 1
        ws.cell(row=row_num, column=1, value=report_data.get('title')).font = Font(bold=True, size=14); row_num += 1 # type: ignore
        if report_data.get('report_date_description'): ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')).font = Font(italic=True); row_num += 1 # type: ignore
        row_num += 1
        
        headers = report_data.get('headers', [])
        data_rows = report_data.get('data_rows', []) # Expects a list of dicts or lists

        if headers:
            for col, header_text in enumerate(headers,1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD")
            row_num +=1
        
        if data_rows:
            for data_item in data_rows:
                if isinstance(data_item, dict):
                    for col, header_text in enumerate(headers, 1):
                        ws.cell(row=row_num, column=col, value=data_item.get(header_text, data_item.get(header_text.lower().replace(' ','_'))))
                elif isinstance(data_item, list):
                     for col, cell_val in enumerate(data_item, 1):
                        ws.cell(row=row_num, column=col, value=cell_val)
                row_num +=1
        
        for col_idx_generic in range(1, len(headers) + 1): 
            ws.column_dimensions[get_column_letter(col_idx_generic)].width = 20

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()


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

# app/business_logic/vendor_manager.py
```py
# app/business_logic/vendor_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.vendor import Vendor
from app.services.business_services import VendorService
from app.services.account_service import AccountService # Corrected import
from app.services.accounting_services import CurrencyService # Correct import
from app.utils.result import Result
from app.utils.pydantic_models import VendorCreateData, VendorUpdateData, VendorSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class VendorManager:
    def __init__(self, 
                 vendor_service: VendorService, 
                 account_service: AccountService, 
                 currency_service: CurrencyService, 
                 app_core: "ApplicationCore"):
        self.vendor_service = vendor_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger 

    async def get_vendor_for_dialog(self, vendor_id: int) -> Optional[Vendor]:
        """ Fetches a full vendor ORM object for dialog population. """
        try:
            return await self.vendor_service.get_by_id(vendor_id)
        except Exception as e:
            self.logger.error(f"Error fetching vendor ID {vendor_id} for dialog: {e}", exc_info=True)
            return None

    async def get_vendors_for_listing(self, 
                                       active_only: bool = True,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[VendorSummaryData]]:
        """ Fetches a list of vendor summaries for table display. """
        try:
            summaries: List[VendorSummaryData] = await self.vendor_service.get_all_summary(
                active_only=active_only,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching vendor listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve vendor list: {str(e)}"])

    async def _validate_vendor_data(self, dto: VendorCreateData | VendorUpdateData, existing_vendor_id: Optional[int] = None) -> List[str]:
        """ Common validation logic for creating and updating vendors. """
        errors: List[str] = []

        if dto.vendor_code:
            existing_by_code = await self.vendor_service.get_by_code(dto.vendor_code)
            if existing_by_code and (existing_vendor_id is None or existing_by_code.id != existing_vendor_id):
                errors.append(f"Vendor code '{dto.vendor_code}' already exists.")
        else: 
            errors.append("Vendor code is required.") 
            
        if dto.name is None or not dto.name.strip(): 
            errors.append("Vendor name is required.")

        if dto.payables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.payables_account_id)
            if not acc:
                errors.append(f"Payables account ID '{dto.payables_account_id}' not found.")
            elif acc.account_type != 'Liability': 
                errors.append(f"Account '{acc.code} - {acc.name}' is not a Liability account and cannot be used as payables account.")
            elif not acc.is_active:
                 errors.append(f"Payables account '{acc.code} - {acc.name}' is not active.")

        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: 
             errors.append("Currency code is required.")
        return errors

    async def create_vendor(self, dto: VendorCreateData) -> Result[Vendor]:
        validation_errors = await self._validate_vendor_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            vendor_orm = Vendor(
                vendor_code=dto.vendor_code, name=dto.name, legal_name=dto.legal_name,
                uen_no=dto.uen_no, gst_registered=dto.gst_registered, gst_no=dto.gst_no,
                withholding_tax_applicable=dto.withholding_tax_applicable,
                withholding_tax_rate=dto.withholding_tax_rate,
                contact_person=dto.contact_person, email=str(dto.email) if dto.email else None, phone=dto.phone,
                address_line1=dto.address_line1, address_line2=dto.address_line2,
                postal_code=dto.postal_code, city=dto.city, country=dto.country,
                payment_terms=dto.payment_terms, currency_code=dto.currency_code, 
                is_active=dto.is_active, vendor_since=dto.vendor_since, notes=dto.notes,
                bank_account_name=dto.bank_account_name, bank_account_number=dto.bank_account_number,
                bank_name=dto.bank_name, bank_branch=dto.bank_branch, bank_swift_code=dto.bank_swift_code,
                payables_account_id=dto.payables_account_id,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_vendor = await self.vendor_service.save(vendor_orm)
            return Result.success(saved_vendor)
        except Exception as e:
            self.logger.error(f"Error creating vendor '{dto.vendor_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the vendor: {str(e)}"])

    async def update_vendor(self, vendor_id: int, dto: VendorUpdateData) -> Result[Vendor]:
        existing_vendor = await self.vendor_service.get_by_id(vendor_id)
        if not existing_vendor:
            return Result.failure([f"Vendor with ID {vendor_id} not found."])

        validation_errors = await self._validate_vendor_data(dto, existing_vendor_id=vendor_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_vendor, key):
                    if key == 'email' and value is not None: 
                        setattr(existing_vendor, key, str(value))
                    else:
                        setattr(existing_vendor, key, value)
            
            existing_vendor.updated_by_user_id = dto.user_id
            
            updated_vendor = await self.vendor_service.save(existing_vendor)
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error updating vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the vendor: {str(e)}"])

    async def toggle_vendor_active_status(self, vendor_id: int, user_id: int) -> Result[Vendor]:
        vendor = await self.vendor_service.get_by_id(vendor_id)
        if not vendor:
            return Result.failure([f"Vendor with ID {vendor_id} not found."])
        
        vendor_name_for_log = vendor.name 
        
        vendor.is_active = not vendor.is_active
        vendor.updated_by_user_id = user_id

        try:
            updated_vendor = await self.vendor_service.save(vendor)
            action = "activated" if updated_vendor.is_active else "deactivated"
            self.logger.info(f"Vendor '{vendor_name_for_log}' (ID: {vendor_id}) {action} by user ID {user_id}.")
            return Result.success(updated_vendor)
        except Exception as e:
            self.logger.error(f"Error toggling active status for vendor ID {vendor_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for vendor: {str(e)}"])


```

# app/business_logic/__init__.py
```py
# File: app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager
from .product_manager import ProductManager
from .sales_invoice_manager import SalesInvoiceManager
from .purchase_invoice_manager import PurchaseInvoiceManager 

__all__ = [
    "CustomerManager",
    "VendorManager",
    "ProductManager",
    "SalesInvoiceManager",
    "PurchaseInvoiceManager", 
]

```

# app/business_logic/sales_invoice_manager.py
```py
# File: app/business_logic/sales_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime 

from sqlalchemy import text # Added for text()
from sqlalchemy.orm import selectinload 

from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.journal_entry import JournalEntry 
from app.models.business.inventory_movement import InventoryMovement # New import

from app.services.business_services import SalesInvoiceService, CustomerService, ProductService, InventoryMovementService # Added InventoryMovementService
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
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum, InventoryMovementTypeEnum # Added InventoryMovementTypeEnum

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
                 app_core: "ApplicationCore",
                 inventory_movement_service: InventoryMovementService): # New dependency
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
        self.inventory_movement_service = inventory_movement_service # New dependency

    # ... (_validate_and_prepare_invoice_data, create_draft_invoice, update_draft_invoice, get_invoice_for_dialog - unchanged from file set 7) ...
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
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active: line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
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
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.inventory_account), # For COGS inventory account
                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.purchase_account), # For COGS expense account
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
                default_cogs_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultCOGS", "5100") # New default

                # Main Financial JE for Sales
                fin_je_lines_data: List[JournalEntryLineData] = []
                fin_je_lines_data.append(JournalEntryLineData( account_id=ar_account.id, debit_amount=invoice_to_post.total_amount, credit_amount=Decimal(0), description=f"A/R for Inv {invoice_to_post.invoice_no}", currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate))
                for line in invoice_to_post.lines:
                    sales_gl_id = line.product.sales_account.id if line.product and line.product.sales_account and line.product.sales_account.is_active else (await self.account_service.get_by_code(default_sales_acc_code)).id # type: ignore
                    if not sales_gl_id: return Result.failure([f"Could not determine Sales Revenue account for line: {line.description}"])
                    fin_je_lines_data.append(JournalEntryLineData( account_id=sales_gl_id, debit_amount=Decimal(0), credit_amount=line.line_subtotal, description=f"Sale: {line.description[:100]} (Inv {invoice_to_post.invoice_no})", currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate))
                    if line.tax_amount and line.tax_amount != Decimal(0) and line.tax_code:
                        gst_gl_id = (line.tax_code_obj.affects_account.id if line.tax_code_obj and line.tax_code_obj.affects_account and line.tax_code_obj.affects_account.is_active else (await self.account_service.get_by_code(default_gst_output_acc_code)).id) if default_gst_output_acc_code else None # type: ignore
                        if not gst_gl_id: return Result.failure([f"Could not determine GST Output account for tax on line: {line.description}"])
                        fin_je_lines_data.append(JournalEntryLineData( account_id=gst_gl_id, debit_amount=Decimal(0), credit_amount=line.tax_amount, description=f"GST Output ({line.tax_code}) for Inv {invoice_to_post.invoice_no}", currency_code=invoice_to_post.currency_code, exchange_rate=invoice_to_post.exchange_rate))
                
                fin_je_dto = JournalEntryData( journal_type=JournalTypeEnum.SALES.value, entry_date=invoice_to_post.invoice_date, description=f"Sales Invoice {invoice_to_post.invoice_no} to {invoice_to_post.customer.name}", source_type="SalesInvoice", source_id=invoice_to_post.id, user_id=user_id, lines=fin_je_lines_data)
                create_fin_je_result = await self.app_core.journal_entry_manager.create_journal_entry(fin_je_dto, session=session)
                if not create_fin_je_result.is_success or not create_fin_je_result.value: return Result.failure(["Failed to create financial JE for SI."] + create_fin_je_result.errors)
                created_fin_je: JournalEntry = create_fin_je_result.value
                post_fin_je_result = await self.app_core.journal_entry_manager.post_journal_entry(created_fin_je.id, user_id, session=session)
                if not post_fin_je_result.is_success: return Result.failure([f"Financial JE (ID: {created_fin_je.id}) created but failed to post."] + post_fin_je_result.errors)

                # Inventory Movements and COGS JE
                cogs_je_lines_data: List[JournalEntryLineData] = []
                for line in invoice_to_post.lines:
                    if line.product and ProductTypeEnum(line.product.product_type) == ProductTypeEnum.INVENTORY:
                        # Fetch WAC using raw SQL against the view (within current session)
                        wac_query = text("SELECT average_cost FROM business.inventory_summary WHERE product_id = :pid")
                        wac_result = await session.execute(wac_query, {"pid": line.product_id})
                        current_wac = wac_result.scalar_one_or_none()
                        if current_wac is None: current_wac = line.product.purchase_price or Decimal(0) # Fallback
                        
                        cogs_amount_for_line = (line.quantity * current_wac).quantize(Decimal("0.01"), ROUND_HALF_UP)

                        inv_movement = InventoryMovement(
                            product_id=line.product_id, movement_date=invoice_to_post.invoice_date,
                            movement_type=InventoryMovementTypeEnum.SALE.value, quantity=-line.quantity, # Negative for outflow
                            unit_cost=current_wac, total_cost=cogs_amount_for_line,
                            reference_type='SalesInvoiceLine', reference_id=line.id, created_by_user_id=user_id
                        )
                        await self.inventory_movement_service.save(inv_movement, session=session)

                        cogs_acc_id = line.product.purchase_account_id if line.product.purchase_account and line.product.purchase_account.is_active else (await self.account_service.get_by_code(default_cogs_acc_code)).id # type: ignore
                        inv_asset_acc_id = line.product.inventory_account_id if line.product.inventory_account and line.product.inventory_account.is_active else None
                        if not cogs_acc_id or not inv_asset_acc_id: return Result.failure(["COGS or Inventory Asset account setup issue for product."])
                        
                        cogs_je_lines_data.append(JournalEntryLineData(account_id=cogs_acc_id, debit_amount=cogs_amount_for_line, credit_amount=Decimal(0), description=f"COGS: {line.description[:50]}"))
                        cogs_je_lines_data.append(JournalEntryLineData(account_id=inv_asset_acc_id, debit_amount=Decimal(0), credit_amount=cogs_amount_for_line, description=f"Inventory Sold: {line.description[:50]}"))

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

# app/business_logic/purchase_invoice_manager.py
```py
# File: app/business_logic/purchase_invoice_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

from sqlalchemy.orm import selectinload 

from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.journal_entry import JournalEntry 
from app.models.business.inventory_movement import InventoryMovement # New import

from app.services.business_services import PurchaseInvoiceService, VendorService, ProductService, InventoryMovementService # Added InventoryMovementService
from app.services.core_services import SequenceService, ConfigurationService
from app.services.tax_service import TaxCodeService
from app.services.account_service import AccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceSummaryData,
    PurchaseInvoiceLineBaseData, TaxCalculationResultData,
    JournalEntryData, JournalEntryLineData 
)
from app.tax.tax_calculator import TaxCalculator
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum, InventoryMovementTypeEnum # Added InventoryMovementTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class PurchaseInvoiceManager:
    def __init__(self,
                 purchase_invoice_service: PurchaseInvoiceService,
                 vendor_service: VendorService,
                 product_service: ProductService,
                 tax_code_service: TaxCodeService,
                 tax_calculator: TaxCalculator,
                 sequence_service: SequenceService, 
                 account_service: AccountService,
                 configuration_service: ConfigurationService,
                 app_core: "ApplicationCore",
                 inventory_movement_service: InventoryMovementService): # New dependency
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
        self.inventory_movement_service = inventory_movement_service # New dependency
        
    # ... (_validate_and_prepare_pi_data, create_draft_purchase_invoice, update_draft_purchase_invoice - unchanged from file set 7)
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
            product: Optional[Product] = None
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
                    tc_check = await self.tax_code_service.get_tax_code(line_dto.tax_code)
                    if not tc_check or not tc_check.is_active: line_errors_current_line.append(f"Tax code '{line_dto.tax_code}' used on line {i+1} is invalid or inactive.")
            
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
                    elif line.product and line.product.purchase_account: # For Service, Non-Inventory, or Inventory if inventory_acc not set
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
                        line_tax_code_obj = line.tax_code_obj 
                        if line_tax_code_obj and line_tax_code_obj.affects_account:
                            if line_tax_code_obj.affects_account.is_active: gst_gl_id_for_line = line_tax_code_obj.affects_account.id
                            else: self.logger.warning(f"Tax code '{line.tax_code}' affects account '{line_tax_code_obj.affects_account.code}' is inactive. Falling back.")
                        
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

                # Create InventoryMovements
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

# app/business_logic/product_manager.py
```py
# app/business_logic/product_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.product import Product
from app.services.business_services import ProductService
from app.services.account_service import AccountService
from app.services.tax_service import TaxCodeService # For validating tax_code
from app.utils.result import Result
from app.utils.pydantic_models import ProductCreateData, ProductUpdateData, ProductSummaryData
from app.common.enums import ProductTypeEnum # For product_type comparison

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class ProductManager:
    def __init__(self, 
                 product_service: ProductService, 
                 account_service: AccountService, 
                 tax_code_service: TaxCodeService,
                 app_core: "ApplicationCore"):
        self.product_service = product_service
        self.account_service = account_service
        self.tax_code_service = tax_code_service
        self.app_core = app_core
        self.logger = app_core.logger 

    async def get_product_for_dialog(self, product_id: int) -> Optional[Product]:
        """ Fetches a full product/service ORM object for dialog population. """
        try:
            return await self.product_service.get_by_id(product_id)
        except Exception as e:
            self.logger.error(f"Error fetching product ID {product_id} for dialog: {e}", exc_info=True)
            return None

    async def get_products_for_listing(self, 
                                       active_only: bool = True,
                                       product_type_filter: Optional[ProductTypeEnum] = None,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[ProductSummaryData]]:
        """ Fetches a list of product/service summaries for table display. """
        try:
            summaries: List[ProductSummaryData] = await self.product_service.get_all_summary(
                active_only=active_only,
                product_type_filter=product_type_filter,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching product listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve product list: {str(e)}"])

    async def _validate_product_data(self, dto: ProductCreateData | ProductUpdateData, existing_product_id: Optional[int] = None) -> List[str]:
        """ Common validation logic for creating and updating products/services. """
        errors: List[str] = []

        # Validate product_code uniqueness
        if dto.product_code:
            existing_by_code = await self.product_service.get_by_code(dto.product_code)
            if existing_by_code and (existing_product_id is None or existing_by_code.id != existing_product_id):
                errors.append(f"Product code '{dto.product_code}' already exists.")
        else:
             errors.append("Product code is required.") # Pydantic should catch this with min_length

        if not dto.name or not dto.name.strip():
            errors.append("Product name is required.") # Pydantic should catch this

        # Validate GL Accounts
        account_ids_to_check = {
            "Sales Account": (dto.sales_account_id, ['Revenue']),
            "Purchase Account": (dto.purchase_account_id, ['Expense', 'Asset']), # COGS or Asset for purchases
        }
        if dto.product_type == ProductTypeEnum.INVENTORY:
            account_ids_to_check["Inventory Account"] = (dto.inventory_account_id, ['Asset'])
        
        for acc_label, (acc_id, valid_types) in account_ids_to_check.items():
            if acc_id is not None:
                acc = await self.account_service.get_by_id(acc_id)
                if not acc:
                    errors.append(f"{acc_label} ID '{acc_id}' not found.")
                elif not acc.is_active:
                    errors.append(f"{acc_label} '{acc.code} - {acc.name}' is not active.")
                elif acc.account_type not in valid_types:
                    errors.append(f"{acc_label} '{acc.code} - {acc.name}' is not a valid type (Expected: {', '.join(valid_types)}).")

        # Validate Tax Code (string code)
        if dto.tax_code is not None:
            tax_code_obj = await self.tax_code_service.get_tax_code(dto.tax_code)
            if not tax_code_obj:
                errors.append(f"Tax code '{dto.tax_code}' not found.")
            elif not tax_code_obj.is_active:
                errors.append(f"Tax code '{dto.tax_code}' is not active.")

        # Pydantic DTO root_validator already checks inventory_account_id and stock levels based on product_type
        return errors

    async def create_product(self, dto: ProductCreateData) -> Result[Product]:
        validation_errors = await self._validate_product_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            product_orm = Product(
                product_code=dto.product_code, name=dto.name, description=dto.description,
                product_type=dto.product_type.value, # Store enum value
                category=dto.category, unit_of_measure=dto.unit_of_measure, barcode=dto.barcode,
                sales_price=dto.sales_price, purchase_price=dto.purchase_price,
                sales_account_id=dto.sales_account_id, purchase_account_id=dto.purchase_account_id,
                inventory_account_id=dto.inventory_account_id,
                tax_code=dto.tax_code, is_active=dto.is_active,
                min_stock_level=dto.min_stock_level, reorder_point=dto.reorder_point,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_product = await self.product_service.save(product_orm)
            return Result.success(saved_product)
        except Exception as e:
            self.logger.error(f"Error creating product '{dto.product_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the product/service: {str(e)}"])

    async def update_product(self, product_id: int, dto: ProductUpdateData) -> Result[Product]:
        existing_product = await self.product_service.get_by_id(product_id)
        if not existing_product:
            return Result.failure([f"Product/Service with ID {product_id} not found."])

        validation_errors = await self._validate_product_data(dto, existing_product_id=product_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            # Use model_dump to get only provided fields for update
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_product, key):
                    if key == "product_type" and isinstance(value, ProductTypeEnum): # Handle enum
                        setattr(existing_product, key, value.value)
                    else:
                        setattr(existing_product, key, value)
            
            existing_product.updated_by_user_id = dto.user_id
            
            updated_product = await self.product_service.save(existing_product)
            return Result.success(updated_product)
        except Exception as e:
            self.logger.error(f"Error updating product ID {product_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the product/service: {str(e)}"])

    async def toggle_product_active_status(self, product_id: int, user_id: int) -> Result[Product]:
        product = await self.product_service.get_by_id(product_id)
        if not product:
            return Result.failure([f"Product/Service with ID {product_id} not found."])
        
        # Future validation: check if product is used in open sales/purchase orders, or has stock.
        # For now, simple toggle.
        
        product_name_for_log = product.name # Capture before potential changes for logging
        
        product.is_active = not product.is_active
        product.updated_by_user_id = user_id

        try:
            updated_product = await self.product_service.save(product)
            action = "activated" if updated_product.is_active else "deactivated"
            self.logger.info(f"Product/Service '{product_name_for_log}' (ID: {product_id}) {action} by user ID {user_id}.")
            return Result.success(updated_product)
        except Exception as e:
            self.logger.error(f"Error toggling active status for product ID {product_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for product/service: {str(e)}"])


```

# app/business_logic/customer_manager.py
```py
# app/business_logic/customer_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal

from app.models.business.customer import Customer
from app.services.business_services import CustomerService
from app.services.account_service import AccountService # Corrected import
from app.services.accounting_services import CurrencyService # Correct import
from app.utils.result import Result
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, CustomerSummaryData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerManager:
    def __init__(self, 
                 customer_service: CustomerService, 
                 account_service: AccountService, 
                 currency_service: CurrencyService, 
                 app_core: "ApplicationCore"):
        self.customer_service = customer_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_customer_for_dialog(self, customer_id: int) -> Optional[Customer]:
        """ Fetches a full customer ORM object for dialog population. """
        try:
            return await self.customer_service.get_by_id(customer_id)
        except Exception as e:
            self.logger.error(f"Error fetching customer ID {customer_id} for dialog: {e}", exc_info=True)
            return None

    async def get_customers_for_listing(self, 
                                       active_only: bool = True,
                                       search_term: Optional[str] = None,
                                       page: int = 1,
                                       page_size: int = 50
                                      ) -> Result[List[CustomerSummaryData]]:
        """ Fetches a list of customer summaries for table display. """
        try:
            # Pydantic DTOs are now directly returned by the service
            summaries: List[CustomerSummaryData] = await self.customer_service.get_all_summary(
                active_only=active_only,
                search_term=search_term,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching customer listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve customer list: {str(e)}"])

    async def _validate_customer_data(self, dto: CustomerCreateData | CustomerUpdateData, existing_customer_id: Optional[int] = None) -> List[str]:
        errors: List[str] = []

        if dto.customer_code:
            existing_by_code = await self.customer_service.get_by_code(dto.customer_code)
            if existing_by_code and (existing_customer_id is None or existing_by_code.id != existing_customer_id):
                errors.append(f"Customer code '{dto.customer_code}' already exists.")
        else: # Should be caught by Pydantic if min_length=1
            errors.append("Customer code is required.") 
            
        if dto.name is None or not dto.name.strip(): # Should be caught by Pydantic if min_length=1
            errors.append("Customer name is required.")

        if dto.receivables_account_id is not None:
            acc = await self.account_service.get_by_id(dto.receivables_account_id)
            if not acc:
                errors.append(f"Receivables account ID '{dto.receivables_account_id}' not found.")
            elif acc.account_type != 'Asset': 
                errors.append(f"Account '{acc.code} - {acc.name}' is not an Asset account and cannot be used as receivables account.")
            elif not acc.is_active:
                 errors.append(f"Receivables account '{acc.code} - {acc.name}' is not active.")
            # Ideally, also check if it's specifically marked as an Accounts Receivable control account via a flag or sub_type

        if dto.currency_code:
            curr = await self.currency_service.get_by_id(dto.currency_code) 
            if not curr:
                errors.append(f"Currency code '{dto.currency_code}' not found.")
            elif not curr.is_active:
                 errors.append(f"Currency '{dto.currency_code}' is not active.")
        else: # Should be caught by Pydantic if required
             errors.append("Currency code is required.")


        # Pydantic DTO's own root_validator handles gst_no if gst_registered
        # No need to repeat here unless more complex cross-field logic is added.
        return errors

    async def create_customer(self, dto: CustomerCreateData) -> Result[Customer]:
        validation_errors = await self._validate_customer_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            customer_orm = Customer(
                customer_code=dto.customer_code, name=dto.name, legal_name=dto.legal_name,
                uen_no=dto.uen_no, gst_registered=dto.gst_registered, gst_no=dto.gst_no,
                contact_person=dto.contact_person, email=str(dto.email) if dto.email else None, phone=dto.phone,
                address_line1=dto.address_line1, address_line2=dto.address_line2,
                postal_code=dto.postal_code, city=dto.city, country=dto.country,
                credit_terms=dto.credit_terms, credit_limit=dto.credit_limit,
                currency_code=dto.currency_code, is_active=dto.is_active,
                customer_since=dto.customer_since, notes=dto.notes,
                receivables_account_id=dto.receivables_account_id,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_customer = await self.customer_service.save(customer_orm)
            return Result.success(saved_customer)
        except Exception as e:
            self.logger.error(f"Error creating customer '{dto.customer_code}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while creating the customer: {str(e)}"])

    async def update_customer(self, customer_id: int, dto: CustomerUpdateData) -> Result[Customer]:
        existing_customer = await self.customer_service.get_by_id(customer_id)
        if not existing_customer:
            return Result.failure([f"Customer with ID {customer_id} not found."])

        validation_errors = await self._validate_customer_data(dto, existing_customer_id=customer_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            # Update fields from DTO
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_customer, key):
                    # Special handling for EmailStr which might be an object
                    if key == 'email' and value is not None:
                        setattr(existing_customer, key, str(value))
                    else:
                        setattr(existing_customer, key, value)
            
            existing_customer.updated_by_user_id = dto.user_id
            
            updated_customer = await self.customer_service.save(existing_customer)
            return Result.success(updated_customer)
        except Exception as e:
            self.logger.error(f"Error updating customer ID {customer_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred while updating the customer: {str(e)}"])

    async def toggle_customer_active_status(self, customer_id: int, user_id: int) -> Result[Customer]:
        customer = await self.customer_service.get_by_id(customer_id)
        if not customer:
            return Result.failure([f"Customer with ID {customer_id} not found."])
        
        customer.is_active = not customer.is_active
        customer.updated_by_user_id = user_id

        try:
            updated_customer = await self.customer_service.save(customer)
            action = "activated" if updated_customer.is_active else "deactivated"
            self.logger.info(f"Customer '{updated_customer.name}' (ID: {customer_id}) {action} by user ID {user_id}.")
            return Result.success(updated_customer)
        except Exception as e:
            self.logger.error(f"Error toggling active status for customer ID {customer_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status for customer: {str(e)}"])

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
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload


from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

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

    # ... (create_journal_entry, update_journal_entry, post_journal_entry, reverse_journal_entry, 
    #      _calculate_next_generation_date, generate_recurring_entries, get_journal_entry_for_dialog - unchanged from previous file set 2)
    async def create_journal_entry(self, entry_data: JournalEntryData, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _create_je_logic(current_session: AsyncSession):
            fiscal_period_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fiscal_period_res = await current_session.execute(fiscal_period_stmt); fiscal_period = fiscal_period_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for entry date {entry_data.entry_date} or period not open."])
            entry_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry")
            if not entry_no_str: return Result.failure(["Failed to generate journal entry number."])
            current_user_id = entry_data.user_id
            journal_entry_orm = JournalEntry(entry_no=entry_no_str, journal_type=entry_data.journal_type, entry_date=entry_data.entry_date, fiscal_period_id=fiscal_period.id, description=entry_data.description, reference=entry_data.reference, is_recurring=entry_data.is_recurring, recurring_pattern_id=entry_data.recurring_pattern_id, is_posted=False, source_type=entry_data.source_type, source_id=entry_data.source_id, created_by_user_id=current_user_id, updated_by_user_id=current_user_id)
            for i, line_dto in enumerate(entry_data.lines, 1):
                account_stmt = select(Account).where(Account.id == line_dto.account_id); account_res = await current_session.execute(account_stmt); account = account_res.scalars().first()
                if not account or not account.is_active: return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
                line_orm = JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id)
                journal_entry_orm.lines.append(line_orm)
            current_session.add(journal_entry_orm); await current_session.flush(); await current_session.refresh(journal_entry_orm)
            if journal_entry_orm.lines: await current_session.refresh(journal_entry_orm, attribute_names=['lines'])
            return Result.success(journal_entry_orm)
        if session: return await _create_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: return await _create_je_logic(new_session) # type: ignore
            except Exception as e: self.app_core.logger.error(f"Error creating JE with new session: {e}", exc_info=True); return Result.failure([f"Failed to save JE: {str(e)}"]) # type: ignore

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            existing_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not existing_entry: return Result.failure([f"JE ID {entry_id} not found for update."])
            if existing_entry.is_posted: return Result.failure([f"Cannot update posted JE: {existing_entry.entry_no}."])
            fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fp_res = await session.execute(fp_stmt); fiscal_period = fp_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for new entry date {entry_data.entry_date} or period not open."])
            current_user_id = entry_data.user_id
            existing_entry.journal_type = entry_data.journal_type; existing_entry.entry_date = entry_data.entry_date
            existing_entry.fiscal_period_id = fiscal_period.id; existing_entry.description = entry_data.description
            existing_entry.reference = entry_data.reference; existing_entry.is_recurring = entry_data.is_recurring
            existing_entry.recurring_pattern_id = entry_data.recurring_pattern_id
            existing_entry.source_type = entry_data.source_type; existing_entry.source_id = entry_data.source_id
            existing_entry.updated_by_user_id = current_user_id
            for line in list(existing_entry.lines): await session.delete(line)
            existing_entry.lines.clear(); await session.flush() 
            new_lines_orm: List[JournalEntryLine] = []
            for i, line_dto in enumerate(entry_data.lines, 1):
                acc_stmt = select(Account).where(Account.id == line_dto.account_id); acc_res = await session.execute(acc_stmt); account = acc_res.scalars().first()
                if not account or not account.is_active: raise ValueError(f"Invalid or inactive account ID {line_dto.account_id} on line {i} during update.")
                new_lines_orm.append(JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id))
            existing_entry.lines.extend(new_lines_orm); session.add(existing_entry) 
            try:
                await session.flush(); await session.refresh(existing_entry)
                if existing_entry.lines: await session.refresh(existing_entry, attribute_names=['lines'])
                return Result.success(existing_entry)
            except Exception as e: self.app_core.logger.error(f"Error updating JE ID {entry_id}: {e}", exc_info=True); return Result.failure([f"Failed to update JE: {str(e)}"]) # type: ignore

    async def post_journal_entry(self, entry_id: int, user_id: int, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _post_je_logic(current_session: AsyncSession):
            entry = await current_session.get(JournalEntry, entry_id)
            if not entry: return Result.failure([f"JE ID {entry_id} not found."])
            if entry.is_posted: return Result.failure([f"JE '{entry.entry_no}' is already posted."])
            fiscal_period = await current_session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': return Result.failure([f"Cannot post. Fiscal period not open. Status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            entry.is_posted = True; entry.updated_by_user_id = user_id
            current_session.add(entry); await current_session.flush(); await current_session.refresh(entry)
            return Result.success(entry)
        if session: return await _post_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: return await _post_je_logic(new_session) # type: ignore
            except Exception as e: self.app_core.logger.error(f"Error posting JE ID {entry_id} with new session: {e}", exc_info=True); return Result.failure([f"Failed to post JE: {str(e)}"]) # type: ignore

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not original_entry: return Result.failure([f"JE ID {entry_id} not found for reversal."])
            if not original_entry.is_posted: return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None: return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])
            reversal_fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= reversal_date, FiscalPeriod.end_date >= reversal_date, FiscalPeriod.status == 'Open')
            reversal_fp_res = await session.execute(reversal_fp_stmt); reversal_fiscal_period = reversal_fp_res.scalars().first()
            if not reversal_fiscal_period: return Result.failure([f"No open fiscal period for reversal date {reversal_date} or period not open."])
            reversal_entry_no = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry")
            if not reversal_entry_no: return Result.failure(["Failed to generate reversal entry number."])
            reversal_lines_dto: List[JournalEntryLineData] = []
            for orig_line in original_entry.lines:
                reversal_lines_dto.append(JournalEntryLineData(account_id=orig_line.account_id, description=f"Reversal: {orig_line.description or ''}", debit_amount=orig_line.credit_amount, credit_amount=orig_line.debit_amount, currency_code=orig_line.currency_code, exchange_rate=orig_line.exchange_rate, tax_code=orig_line.tax_code, tax_amount=-orig_line.tax_amount if orig_line.tax_amount is not None else Decimal(0), dimension1_id=orig_line.dimension1_id, dimension2_id=orig_line.dimension2_id))
            reversal_je_data = JournalEntryData(journal_type=original_entry.journal_type, entry_date=reversal_date, description=description or f"Reversal of entry {original_entry.entry_no}", reference=f"REV:{original_entry.entry_no}", is_posted=False, source_type="JournalEntryReversalSource", source_id=original_entry.id, user_id=user_id, lines=reversal_lines_dto)
            create_reversal_result = await self.create_journal_entry(reversal_je_data, session=session)
            if not create_reversal_result.is_success or not create_reversal_result.value: return Result.failure(["Failed to create reversal JE."] + create_reversal_result.errors)
            reversal_je_orm = create_reversal_result.value
            original_entry.is_reversed = True; original_entry.reversing_entry_id = reversal_je_orm.id
            original_entry.updated_by_user_id = user_id; session.add(original_entry)
            try:
                await session.flush(); await session.refresh(reversal_je_orm)
                if reversal_je_orm.lines: await session.refresh(reversal_je_orm, attribute_names=['lines'])
                return Result.success(reversal_je_orm)
            except Exception as e: self.app_core.logger.error(f"Error reversing JE ID {entry_id} (flush/commit stage): {e}", exc_info=True); return Result.failure([f"Failed to finalize reversal: {str(e)}"]) # type: ignore

    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        next_date = last_date
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                try:
                    next_date = next_date.replace(day=day_of_month)
                except ValueError: 
                    next_date = next_date + relativedelta(day=31) 
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month:
                try:
                    next_date = next_date.replace(day=day_of_month, month=last_date.month)
                except ValueError:
                    next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)
        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            if day_of_week is not None: 
                 current_weekday = next_date.weekday() 
                 days_to_add = (day_of_week - current_weekday + 7) % 7
                 next_date += timedelta(days=days_to_add)
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
            raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date

    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date); generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.template_journal_entry: self.app_core.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping."); generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."])); continue
            entry_date_for_new_je = pattern.next_generation_date; 
            if not entry_date_for_new_je : continue 
            template_entry = pattern.template_journal_entry
            new_je_lines_data = [JournalEntryLineData(account_id=line.account_id, description=line.description, debit_amount=line.debit_amount, credit_amount=line.credit_amount, currency_code=line.currency_code, exchange_rate=line.exchange_rate, tax_code=line.tax_code, tax_amount=line.tax_amount, dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id) for line in template_entry.lines]
            new_je_data = JournalEntryData(journal_type=template_entry.journal_type, entry_date=entry_date_for_new_je, description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})", reference=template_entry.reference, user_id=user_id, lines=new_je_lines_data, recurring_pattern_id=pattern.id, source_type="RecurringPattern", source_id=pattern.id)
            create_result = await self.create_journal_entry(new_je_data); generated_results.append(create_result)
            if create_result.is_success:
                async with self.app_core.db_manager.session() as session: # type: ignore
                    pattern_to_update = await session.get(RecurringPattern, pattern.id)
                    if pattern_to_update:
                        pattern_to_update.last_generated_date = entry_date_for_new_je
                        try:
                            next_gen = self._calculate_next_generation_date(pattern_to_update.last_generated_date, pattern_to_update.frequency, pattern_to_update.interval_value, pattern_to_update.day_of_month, pattern_to_update.day_of_week)
                            if pattern_to_update.end_date and next_gen > pattern_to_update.end_date: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False 
                            else: pattern_to_update.next_generation_date = next_gen
                        except NotImplementedError: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False; self.app_core.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        pattern_to_update.updated_by_user_id = user_id; session.add(pattern_to_update); await session.commit()
                    else: self.app_core.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") # type: ignore
        return generated_results

    async def get_journal_entry_for_dialog(self, entry_id: int) -> Optional[JournalEntry]:
        return await self.journal_service.get_by_id(entry_id)

    async def get_journal_entries_for_listing(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]:
        filters = filters or {}
        try:
            summary_data = await self.journal_service.get_all_summary(
                start_date_filter=filters.get("start_date"),
                end_date_filter=filters.get("end_date"),
                status_filter=filters.get("status"),
                entry_no_filter=filters.get("entry_no"),
                description_filter=filters.get("description"),
                journal_type_filter=filters.get("journal_type") 
            )
            return Result.success(summary_data)
        except Exception as e:
            self.app_core.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True) 
            return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])

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

# scripts/initial_data.sql
```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.2 - Added Configuration Keys for Default Accounts)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Insert default roles
-- ----------------------------------------------------------------------------
INSERT INTO core.roles (name, description) VALUES
('Administrator', 'Full system access'),
('Accountant', 'Access to accounting functions'),
('Bookkeeper', 'Basic transaction entry and reporting'),
('Manager', 'Access to reports and dashboards'),
('Viewer', 'Read-only access to data')
ON CONFLICT (name) DO UPDATE SET 
    description = EXCLUDED.description, 
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default permissions
-- ----------------------------------------------------------------------------
INSERT INTO core.permissions (code, description, module) VALUES
-- Core permissions
('SYSTEM_SETTINGS', 'Manage system settings', 'System'),
('USER_MANAGE', 'Manage users', 'System'),
('ROLE_MANAGE', 'Manage roles and permissions', 'System'),
('DATA_BACKUP', 'Backup and restore data', 'System'),
('DATA_IMPORT', 'Import data', 'System'),
('DATA_EXPORT', 'Export data', 'System'),
-- Accounting permissions
('ACCOUNT_VIEW', 'View chart of accounts', 'Accounting'),
('ACCOUNT_CREATE', 'Create accounts', 'Accounting'),
('ACCOUNT_EDIT', 'Edit accounts', 'Accounting'),
('ACCOUNT_DELETE', 'Delete/deactivate accounts', 'Accounting'),
('JOURNAL_VIEW', 'View journal entries', 'Accounting'),
('JOURNAL_CREATE', 'Create journal entries', 'Accounting'),
('JOURNAL_EDIT', 'Edit draft journal entries', 'Accounting'),
('JOURNAL_POST', 'Post journal entries', 'Accounting'),
('JOURNAL_REVERSE', 'Reverse posted journal entries', 'Accounting'),
('PERIOD_MANAGE', 'Manage fiscal periods', 'Accounting'),
('YEAR_CLOSE', 'Close fiscal years', 'Accounting'),
-- Business permissions
('CUSTOMER_VIEW', 'View customers', 'Business'),
('CUSTOMER_CREATE', 'Create customers', 'Business'),
('CUSTOMER_EDIT', 'Edit customers', 'Business'),
('CUSTOMER_DELETE', 'Delete customers', 'Business'),
('VENDOR_VIEW', 'View vendors', 'Business'),
('VENDOR_CREATE', 'Create vendors', 'Business'),
('VENDOR_EDIT', 'Edit vendors', 'Business'),
('VENDOR_DELETE', 'Delete vendors', 'Business'),
('PRODUCT_VIEW', 'View products', 'Business'),
('PRODUCT_CREATE', 'Create products', 'Business'),
('PRODUCT_EDIT', 'Edit products', 'Business'),
('PRODUCT_DELETE', 'Delete products', 'Business'),
-- Transaction permissions
('INVOICE_VIEW', 'View invoices', 'Transactions'),
('INVOICE_CREATE', 'Create invoices', 'Transactions'),
('INVOICE_EDIT', 'Edit invoices', 'Transactions'),
('INVOICE_DELETE', 'Delete invoices', 'Transactions'),
('INVOICE_APPROVE', 'Approve invoices', 'Transactions'),
('PAYMENT_VIEW', 'View payments', 'Transactions'),
('PAYMENT_CREATE', 'Create payments', 'Transactions'),
('PAYMENT_EDIT', 'Edit payments', 'Transactions'),
('PAYMENT_DELETE', 'Delete payments', 'Transactions'),
('PAYMENT_APPROVE', 'Approve payments', 'Transactions'),
-- Banking permissions
('BANK_VIEW', 'View bank accounts', 'Banking'),
('BANK_CREATE', 'Create bank accounts', 'Banking'),
('BANK_EDIT', 'Edit bank accounts', 'Banking'),
('BANK_DELETE', 'Delete bank accounts', 'Banking'),
('BANK_RECONCILE', 'Reconcile bank accounts', 'Banking'),
('BANK_STATEMENT', 'Import bank statements', 'Banking'),
-- Tax permissions
('TAX_VIEW', 'View tax settings', 'Tax'),
('TAX_EDIT', 'Edit tax settings', 'Tax'),
('GST_PREPARE', 'Prepare GST returns', 'Tax'),
('GST_SUBMIT', 'Mark GST returns as submitted', 'Tax'),
('TAX_REPORT', 'Generate tax reports', 'Tax'),
-- Reporting permissions
('REPORT_FINANCIAL', 'Access financial reports', 'Reporting'),
('REPORT_TAX', 'Access tax reports', 'Reporting'),
('REPORT_MANAGEMENT', 'Access management reports', 'Reporting'),
('REPORT_CUSTOM', 'Create custom reports', 'Reporting'),
('REPORT_EXPORT', 'Export reports', 'Reporting')
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description,
    module = EXCLUDED.module;

-- ----------------------------------------------------------------------------
-- Insert System Init User (ID 1) - MUST BE CREATED EARLY
-- ----------------------------------------------------------------------------
INSERT INTO core.users (id, username, password_hash, email, full_name, is_active, require_password_change)
VALUES (1, 'system_init_user', crypt('system_init_secure_password_!PLACEHOLDER!', gen_salt('bf')), 'system_init@sgbookkeeper.com', 'System Initializer', FALSE, FALSE) 
ON CONFLICT (id) DO UPDATE SET 
    username = EXCLUDED.username, 
    password_hash = EXCLUDED.password_hash, 
    email = EXCLUDED.email, 
    full_name = EXCLUDED.full_name, 
    is_active = EXCLUDED.is_active,
    require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

-- Synchronize the sequence for core.users.id after inserting user with ID 1
-- This ensures the next user (e.g., 'admin') gets a correct auto-generated ID
SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);

-- ----------------------------------------------------------------------------
-- Insert default currencies (SGD must be first for company_settings FK if it's the base)
-- ----------------------------------------------------------------------------
INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('SGD', 'Singapore Dollar', '$', TRUE, 2, 1, 1)
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, 
    decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), 
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('USD', 'US Dollar', '$', TRUE, 2, 1, 1),
('EUR', 'Euro', '€', TRUE, 2, 1, 1),
('GBP', 'British Pound', '£', TRUE, 2, 1, 1),
('AUD', 'Australian Dollar', '$', TRUE, 2, 1, 1),
('JPY', 'Japanese Yen', '¥', TRUE, 0, 1, 1),
('CNY', 'Chinese Yuan', '¥', TRUE, 2, 1, 1),
('MYR', 'Malaysian Ringgit', 'RM', TRUE, 2, 1, 1),
('IDR', 'Indonesian Rupiah', 'Rp', TRUE, 0, 1, 1)
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, 
    decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), 
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert Default Company Settings (ID = 1)
-- This MUST come AFTER core.users ID 1 is created and base currency (SGD) is defined.
-- ----------------------------------------------------------------------------
INSERT INTO core.company_settings (
    id, company_name, legal_name, uen_no, gst_registration_no, gst_registered, 
    address_line1, postal_code, city, country, 
    fiscal_year_start_month, fiscal_year_start_day, base_currency, tax_id_label, date_format, 
    updated_by 
) VALUES (
    1, 
    'My Demo Company Pte. Ltd.', 
    'My Demo Company Private Limited',
    '202400001Z', 
    'M90000001Z', 
    TRUE,
    '1 Marina Boulevard', 
    '018989',
    'Singapore',
    'Singapore',
    1, 
    1, 
    'SGD',
    'UEN',
    'dd/MM/yyyy',
    1 
)
ON CONFLICT (id) DO UPDATE SET
    company_name = EXCLUDED.company_name, legal_name = EXCLUDED.legal_name, uen_no = EXCLUDED.uen_no,
    gst_registration_no = EXCLUDED.gst_registration_no, gst_registered = EXCLUDED.gst_registered,
    address_line1 = EXCLUDED.address_line1, postal_code = EXCLUDED.postal_code, city = EXCLUDED.city, country = EXCLUDED.country,
    fiscal_year_start_month = EXCLUDED.fiscal_year_start_month, fiscal_year_start_day = EXCLUDED.fiscal_year_start_day,
    base_currency = EXCLUDED.base_currency, tax_id_label = EXCLUDED.tax_id_label, date_format = EXCLUDED.date_format,
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default document sequences
-- ----------------------------------------------------------------------------
INSERT INTO core.sequences (sequence_name, prefix, next_value, format_template) VALUES
('journal_entry', 'JE', 1, '{PREFIX}{VALUE:06}'), ('sales_invoice', 'INV', 1, '{PREFIX}{VALUE:06}'),
('purchase_invoice', 'PUR', 1, '{PREFIX}{VALUE:06}'), ('payment', 'PAY', 1, '{PREFIX}{VALUE:06}'),
('receipt', 'REC', 1, '{PREFIX}{VALUE:06}'), ('customer', 'CUS', 1, '{PREFIX}{VALUE:04}'),
('vendor', 'VEN', 1, '{PREFIX}{VALUE:04}'), ('product', 'PRD', 1, '{PREFIX}{VALUE:04}'),
('wht_certificate', 'WHT', 1, '{PREFIX}{VALUE:06}')
ON CONFLICT (sequence_name) DO UPDATE SET
    prefix = EXCLUDED.prefix, next_value = GREATEST(core.sequences.next_value, EXCLUDED.next_value), 
    format_template = EXCLUDED.format_template, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default configuration values (NEW SECTION from previous fix)
-- These account codes MUST exist from chart_of_accounts CSV or be system accounts
-- ----------------------------------------------------------------------------
INSERT INTO core.configuration (config_key, config_value, description, updated_by) VALUES
('SysAcc_DefaultAR', '1120', 'Default Accounts Receivable account code', 1),
('SysAcc_DefaultSalesRevenue', '4100', 'Default Sales Revenue account code', 1),
('SysAcc_DefaultGSTOutput', 'SYS-GST-OUTPUT', 'Default GST Output Tax account code', 1),
('SysAcc_DefaultAP', '2110', 'Default Accounts Payable account code', 1),
('SysAcc_DefaultPurchaseExpense', '5100', 'Default Purchase/COGS account code', 1),
('SysAcc_DefaultGSTInput', 'SYS-GST-INPUT', 'Default GST Input Tax account code', 1)
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    updated_by = EXCLUDED.updated_by,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert account types
-- ----------------------------------------------------------------------------
INSERT INTO accounting.account_types (name, category, is_debit_balance, report_type, display_order, description) VALUES
('Current Asset', 'Asset', TRUE, 'Balance Sheet', 10, 'Assets expected to be converted to cash within one year'),
('Fixed Asset', 'Asset', TRUE, 'Balance Sheet', 20, 'Long-term tangible assets'),
('Other Asset', 'Asset', TRUE, 'Balance Sheet', 30, 'Assets that don''t fit in other categories'),
('Current Liability', 'Liability', FALSE, 'Balance Sheet', 40, 'Obligations due within one year'),
('Long-term Liability', 'Liability', FALSE, 'Balance Sheet', 50, 'Obligations due beyond one year'),
('Equity', 'Equity', FALSE, 'Balance Sheet', 60, 'Owner''s equity and retained earnings'),
('Revenue', 'Revenue', FALSE, 'Income Statement', 70, 'Income from business operations'),
('Cost of Sales', 'Expense', TRUE, 'Income Statement', 80, 'Direct costs of goods sold'),
('Expense', 'Expense', TRUE, 'Income Statement', 90, 'General business expenses'),
('Other Income', 'Revenue', FALSE, 'Income Statement', 100, 'Income from non-core activities'),
('Other Expense', 'Expense', TRUE, 'Income Statement', 110, 'Expenses from non-core activities')
ON CONFLICT (name) DO UPDATE SET
    category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type,
    display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;

-- Ensure key GL accounts from default CoA exist if not already inserted by CSV import via app (NEW SECTION from previous fix)
-- These are referenced by the core.configuration defaults
INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account) VALUES
('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE),
('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE),
('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE),
('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE)
ON CONFLICT (code) DO NOTHING; -- Do nothing if they already exist (e.g. from CSV)

-- ----------------------------------------------------------------------------
-- Insert default tax codes related accounts
-- ----------------------------------------------------------------------------
INSERT INTO accounting.accounts (code, name, account_type, created_by, updated_by, is_active) VALUES
('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 1, 1, TRUE),
('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 1, 1, TRUE)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name, account_type = EXCLUDED.account_type, updated_by = EXCLUDED.updated_by, 
    is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default tax codes (GST updated to 9%)
-- ----------------------------------------------------------------------------
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'SR', 'Standard Rate (9%)', 'GST', 9.00, TRUE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-OUTPUT'
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate,
    is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, 
    affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ZR', 'Zero Rate', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ES', 'Exempt Supply', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('OP', 'Out of Scope', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'TX', 'Taxable Purchase (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-INPUT'
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate,
    is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, 
    affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('BL', 'Blocked Input Tax (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, rate = EXCLUDED.rate, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('NR', 'Non-Resident Services', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ND', 'Non-Deductible', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('CA', 'Capital Allowance', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- Create an active 'admin' user for application login
INSERT INTO core.users (username, password_hash, email, full_name, is_active, require_password_change)
VALUES ('admin', crypt('password', gen_salt('bf')), 'admin@sgbookkeeper.com', 'Administrator', TRUE, TRUE)
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

-- Assign 'Administrator' role to 'admin' user
WITH admin_user_id_cte AS (SELECT id FROM core.users WHERE username = 'admin'),
     admin_role_id_cte AS (SELECT id FROM core.roles WHERE name = 'Administrator')
INSERT INTO core.user_roles (user_id, role_id, created_at)
SELECT admin_user_id_cte.id, admin_role_id_cte.id, CURRENT_TIMESTAMP FROM admin_user_id_cte, admin_role_id_cte
WHERE admin_user_id_cte.id IS NOT NULL AND admin_role_id_cte.id IS NOT NULL
ON CONFLICT (user_id, role_id) DO NOTHING;

-- For all permissions, grant them to the 'Administrator' role
INSERT INTO core.role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, CURRENT_TIMESTAMP
FROM core.roles r, core.permissions p
WHERE r.name = 'Administrator'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT; 
-- End of initial data

```

# scripts/db_init.py
```py
# File: scripts/db_init.py
import asyncio
import asyncpg # type: ignore
import argparse
import getpass
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_SQL_PATH = SCRIPT_DIR / 'schema.sql'
INITIAL_DATA_SQL_PATH = SCRIPT_DIR / 'initial_data.sql'

async def create_database(args):
    """Create PostgreSQL database and initialize schema using reference SQL files."""
    conn_admin = None 
    db_conn = None 
    try:
        conn_params_admin = { 
            "user": args.user,
            "password": args.password,
            "host": args.host,
            "port": args.port,
        }
        conn_admin = await asyncpg.connect(**conn_params_admin, database='postgres') 
    except Exception as e:
        print(f"Error connecting to PostgreSQL server (postgres DB): {type(e).__name__} - {str(e)}", file=sys.stderr)
        return False
    
    try:
        exists = await conn_admin.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Terminating connections to '{args.dbname}'...")
                await conn_admin.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{args.dbname}' AND pid <> pg_backend_pid();
                """)
                print(f"Dropping existing database '{args.dbname}'...")
                await conn_admin.execute(f"DROP DATABASE IF EXISTS \"{args.dbname}\"") 
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                await conn_admin.close()
                return False 
        
        print(f"Creating database '{args.dbname}'...")
        await conn_admin.execute(f"CREATE DATABASE \"{args.dbname}\"") 
        
        await conn_admin.close() 
        conn_admin = None 
        
        conn_params_db = {**conn_params_admin, "database": args.dbname}
        db_conn = await asyncpg.connect(**conn_params_db) 
        
        if not SCHEMA_SQL_PATH.exists():
            print(f"Error: schema.sql not found at {SCHEMA_SQL_PATH}", file=sys.stderr)
            return False
            
        print(f"Initializing database schema from {SCHEMA_SQL_PATH}...")
        with open(SCHEMA_SQL_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        await db_conn.execute(schema_sql)
        print("Schema execution completed.")
        
        if not INITIAL_DATA_SQL_PATH.exists():
            print(f"Warning: initial_data.sql not found at {INITIAL_DATA_SQL_PATH}. Skipping initial data.", file=sys.stderr)
        else:
            print(f"Loading initial data from {INITIAL_DATA_SQL_PATH}...")
            with open(INITIAL_DATA_SQL_PATH, 'r', encoding='utf-8') as f:
                data_sql = f.read()
            await db_conn.execute(data_sql)
            print("Initial data loading completed.")

        print(f"Setting default search_path for database '{args.dbname}'...")
        await db_conn.execute(f"""
            ALTER DATABASE "{args.dbname}" 
            SET search_path TO core, accounting, business, audit, public;
        """)
        print("Default search_path set.")
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error during database creation/initialization: {type(e).__name__} - {str(e)}", file=sys.stderr)
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
            print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr) # type: ignore
        if hasattr(e, 'detail') and e.detail: # type: ignore
             print(f"  DETAIL: {e.detail}", file=sys.stderr) # type: ignore
        if hasattr(e, 'query') and e.query: # type: ignore
            print(f"  Query context: {e.query[:200]}...", file=sys.stderr) # type: ignore
        return False
    
    finally:
        if conn_admin and not conn_admin.is_closed():
            await conn_admin.close()
        if db_conn and not db_conn.is_closed():
            await db_conn.close()

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize SG Bookkeeper database from reference SQL files.')
    parser.add_argument('--host', default=os.getenv('PGHOST', 'localhost'), help='PostgreSQL server host (Env: PGHOST)')
    parser.add_argument('--port', type=int, default=os.getenv('PGPORT', 5432), help='PostgreSQL server port (Env: PGPORT)')
    parser.add_argument('--user', default=os.getenv('PGUSER', 'postgres'), help='PostgreSQL username (Env: PGUSER)')
    parser.add_argument('--password', help='PostgreSQL password (Env: PGPASSWORD, or prompts if empty)')
    parser.add_argument('--dbname', default=os.getenv('PGDATABASE', 'sg_bookkeeper'), help='Database name (Env: PGDATABASE)')
    parser.add_argument('--drop-existing', action='store_true', help='Drop database if it already exists')
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not args.password:
        pgpassword_env = os.getenv('PGPASSWORD')
        if pgpassword_env:
            args.password = pgpassword_env
        else:
            try:
                args.password = getpass.getpass(f"Password for PostgreSQL user '{args.user}' on host '{args.host}': ")
            except (EOFError, KeyboardInterrupt): 
                print("\nPassword prompt cancelled or non-interactive environment. Exiting.", file=sys.stderr)
                sys.exit(1)
            except Exception as e: 
                print(f"Could not read password securely: {e}. Try setting PGPASSWORD environment variable or using --password.", file=sys.stderr)
                sys.exit(1)

    try:
        success = asyncio.run(create_database(args))
    except KeyboardInterrupt:
        print("\nDatabase initialization cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred in main: {type(e).__name__} - {str(e)}", file=sys.stderr)
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
             print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr) # type: ignore
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

```

# scripts/schema.sql
```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema - Version 1.0.1 (Reordered FKs)
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application.
-- Changes from 1.0.0:
--  - All CREATE TABLE statements are grouped first.
--  - All ALTER TABLE ADD CONSTRAINT FOREIGN KEY statements are grouped at the end.
--  - Full table definitions restored.
-- ============================================================================

-- ============================================================================
-- INITIAL SETUP
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS accounting;
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS audit;

SET search_path TO core, accounting, business, audit, public;

-- ============================================================================
-- CORE SCHEMA TABLES
-- ============================================================================
CREATE TABLE core.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE, -- Added UNIQUE constraint from reference logic
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_attempt TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    require_password_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Comments for core.users (omitted here for brevity, assume they are as per reference)

CREATE TABLE core.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    module VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.role_permissions (
    role_id INTEGER NOT NULL, -- FK added later
    permission_id INTEGER NOT NULL, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE core.user_roles (
    user_id INTEGER NOT NULL, -- FK added later
    role_id INTEGER NOT NULL, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE core.company_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20),
    gst_registration_no VARCHAR(20),
    gst_registered BOOLEAN DEFAULT FALSE,
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    postal_code VARCHAR(20),
    city VARCHAR(50) DEFAULT 'Singapore',
    country VARCHAR(50) DEFAULT 'Singapore',
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(100),
    logo BYTEA,
    fiscal_year_start_month INTEGER DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    fiscal_year_start_day INTEGER DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
    base_currency VARCHAR(3) DEFAULT 'SGD', -- FK added later
    tax_id_label VARCHAR(50) DEFAULT 'UEN',
    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- FK added later
);

CREATE TABLE core.configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT,
    description VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- FK added later
);

CREATE TABLE core.sequences (
    id SERIAL PRIMARY KEY,
    sequence_name VARCHAR(50) NOT NULL UNIQUE,
    prefix VARCHAR(10),
    suffix VARCHAR(10),
    next_value INTEGER NOT NULL DEFAULT 1,
    increment_by INTEGER NOT NULL DEFAULT 1,
    min_value INTEGER NOT NULL DEFAULT 1,
    max_value INTEGER NOT NULL DEFAULT 2147483647,
    cycle BOOLEAN DEFAULT FALSE,
    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACCOUNTING SCHEMA TABLES
-- ============================================================================
CREATE TABLE accounting.account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    is_debit_balance BOOLEAN NOT NULL,
    report_type VARCHAR(30) NOT NULL,
    display_order INTEGER NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounting.accounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    sub_type VARCHAR(30),
    tax_treatment VARCHAR(20),
    gst_applicable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    parent_id INTEGER, -- FK to self, added later
    report_group VARCHAR(50),
    is_control_account BOOLEAN DEFAULT FALSE,
    is_bank_account BOOLEAN DEFAULT FALSE,
    opening_balance NUMERIC(15,2) DEFAULT 0,
    opening_balance_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);
CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);

CREATE TABLE accounting.fiscal_years (
    id SERIAL PRIMARY KEY,
    year_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_date TIMESTAMP WITH TIME ZONE,
    closed_by INTEGER, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL, -- FK added later
    CONSTRAINT fy_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
);

CREATE TABLE accounting.fiscal_periods (
    id SERIAL PRIMARY KEY,
    fiscal_year_id INTEGER NOT NULL, -- FK added later
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    period_number INTEGER NOT NULL,
    is_adjustment BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL, -- FK added later
    CONSTRAINT fp_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
);
CREATE INDEX idx_fiscal_periods_dates ON accounting.fiscal_periods(start_date, end_date);
CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);

CREATE TABLE accounting.currencies (
    code CHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    decimal_places INTEGER DEFAULT 2,
    format_string VARCHAR(20) DEFAULT '#,##0.00',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- FK added later
    updated_by INTEGER -- FK added later
);

CREATE TABLE accounting.exchange_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL, -- FK added later
    to_currency CHAR(3) NOT NULL, -- FK added later
    rate_date DATE NOT NULL,
    exchange_rate NUMERIC(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- FK added later
    updated_by INTEGER, -- FK added later
    CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
);
CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);

CREATE TABLE accounting.journal_entries (
    id SERIAL PRIMARY KEY,
    entry_no VARCHAR(20) NOT NULL UNIQUE,
    journal_type VARCHAR(20) NOT NULL,
    entry_date DATE NOT NULL,
    fiscal_period_id INTEGER NOT NULL, -- FK added later
    description VARCHAR(500),
    reference VARCHAR(100),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern_id INTEGER, -- FK added later
    is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE,
    reversing_entry_id INTEGER, -- FK to self, added later
    source_type VARCHAR(50),
    source_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);
CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
CREATE INDEX idx_journal_entries_source ON accounting.journal_entries(source_type, source_id);
CREATE INDEX idx_journal_entries_posted ON accounting.journal_entries(is_posted);

CREATE TABLE accounting.journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL, -- FK added later
    line_number INTEGER NOT NULL,
    account_id INTEGER NOT NULL, -- FK added later
    description VARCHAR(200),
    debit_amount NUMERIC(15,2) DEFAULT 0,
    credit_amount NUMERIC(15,2) DEFAULT 0,
    currency_code CHAR(3) DEFAULT 'SGD', -- FK added later
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    tax_code VARCHAR(20), -- FK added later
    tax_amount NUMERIC(15,2) DEFAULT 0,
    dimension1_id INTEGER, -- FK added later
    dimension2_id INTEGER, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT jel_check_debit_credit CHECK ((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0) OR (debit_amount = 0 AND credit_amount = 0))
);
CREATE INDEX idx_journal_entry_lines_entry ON accounting.journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_entry_lines_account ON accounting.journal_entry_lines(account_id);

CREATE TABLE accounting.recurring_patterns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_entry_id INTEGER NOT NULL, -- FK added later
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')),
    interval_value INTEGER NOT NULL DEFAULT 1,
    start_date DATE NOT NULL,
    end_date DATE,
    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    last_generated_date DATE,
    next_generation_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.dimensions (
    id SERIAL PRIMARY KEY,
    dimension_type VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER, -- FK to self, added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL, -- FK added later
    UNIQUE (dimension_type, code)
);

CREATE TABLE accounting.budgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    fiscal_year_id INTEGER NOT NULL, -- FK added later
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.budget_details (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL, -- FK added later
    account_id INTEGER NOT NULL, -- FK added later
    fiscal_period_id INTEGER NOT NULL, -- FK added later
    amount NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER, -- FK added later
    dimension2_id INTEGER, -- FK added later
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);
CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (budget_id, account_id, fiscal_period_id, COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0));

CREATE TABLE accounting.tax_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    description VARCHAR(100) NOT NULL,
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
    rate NUMERIC(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    affects_account_id INTEGER, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.gst_returns (
    id SERIAL PRIMARY KEY,
    return_period VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    filing_due_date DATE NOT NULL,
    standard_rated_supplies NUMERIC(15,2) DEFAULT 0,
    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,
    exempt_supplies NUMERIC(15,2) DEFAULT 0,
    total_supplies NUMERIC(15,2) DEFAULT 0,
    taxable_purchases NUMERIC(15,2) DEFAULT 0,
    output_tax NUMERIC(15,2) DEFAULT 0,
    input_tax NUMERIC(15,2) DEFAULT 0,
    tax_adjustments NUMERIC(15,2) DEFAULT 0,
    tax_payable NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')),
    submission_date DATE,
    submission_reference VARCHAR(50),
    journal_entry_id INTEGER, -- FK added later
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.withholding_tax_certificates (
    id SERIAL PRIMARY KEY,
    certificate_no VARCHAR(20) NOT NULL UNIQUE,
    vendor_id INTEGER NOT NULL, -- FK added later
    tax_type VARCHAR(50) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL,
    payment_date DATE NOT NULL,
    amount_before_tax NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) NOT NULL,
    payment_reference VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')),
    issue_date DATE,
    journal_entry_id INTEGER, -- FK added later
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

-- ============================================================================
-- BUSINESS SCHEMA TABLES
-- ============================================================================
CREATE TABLE business.customers (
    id SERIAL PRIMARY KEY, customer_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, gst_no VARCHAR(20), contact_person VARCHAR(100), email VARCHAR(100), phone VARCHAR(20), address_line1 VARCHAR(100), address_line2 VARCHAR(100), postal_code VARCHAR(20), city VARCHAR(50), country VARCHAR(50) DEFAULT 'Singapore', credit_terms INTEGER DEFAULT 30, credit_limit NUMERIC(15,2), currency_code CHAR(3) DEFAULT 'SGD', is_active BOOLEAN DEFAULT TRUE, customer_since DATE, notes TEXT, receivables_account_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_customers_name ON business.customers(name); CREATE INDEX idx_customers_is_active ON business.customers(is_active);

CREATE TABLE business.vendors (
    id SERIAL PRIMARY KEY, vendor_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, gst_no VARCHAR(20), withholding_tax_applicable BOOLEAN DEFAULT FALSE, withholding_tax_rate NUMERIC(5,2), contact_person VARCHAR(100), email VARCHAR(100), phone VARCHAR(20), address_line1 VARCHAR(100), address_line2 VARCHAR(100), postal_code VARCHAR(20), city VARCHAR(50), country VARCHAR(50) DEFAULT 'Singapore', payment_terms INTEGER DEFAULT 30, currency_code CHAR(3) DEFAULT 'SGD', is_active BOOLEAN DEFAULT TRUE, vendor_since DATE, notes TEXT, bank_account_name VARCHAR(100), bank_account_number VARCHAR(50), bank_name VARCHAR(100), bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), payables_account_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_vendors_name ON business.vendors(name); CREATE INDEX idx_vendors_is_active ON business.vendors(is_active);

CREATE TABLE business.products (
    id SERIAL PRIMARY KEY, product_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, description TEXT, product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('Inventory', 'Service', 'Non-Inventory')), category VARCHAR(50), unit_of_measure VARCHAR(20), barcode VARCHAR(50), sales_price NUMERIC(15,2), purchase_price NUMERIC(15,2), sales_account_id INTEGER, purchase_account_id INTEGER, inventory_account_id INTEGER, tax_code VARCHAR(20), is_active BOOLEAN DEFAULT TRUE, min_stock_level NUMERIC(15,2), reorder_point NUMERIC(15,2), created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_products_name ON business.products(name); CREATE INDEX idx_products_is_active ON business.products(is_active); CREATE INDEX idx_products_type ON business.products(product_type);

CREATE TABLE business.inventory_movements (
    id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL, movement_date DATE NOT NULL, movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('Purchase', 'Sale', 'Adjustment', 'Transfer', 'Return', 'Opening')), quantity NUMERIC(15,2) NOT NULL, unit_cost NUMERIC(15,4), total_cost NUMERIC(15,2), reference_type VARCHAR(50), reference_id INTEGER, notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL);
CREATE INDEX idx_inventory_movements_product ON business.inventory_movements(product_id, movement_date); CREATE INDEX idx_inventory_movements_reference ON business.inventory_movements(reference_type, reference_id);

CREATE TABLE business.sales_invoices (
    id SERIAL PRIMARY KEY, invoice_no VARCHAR(20) NOT NULL UNIQUE, customer_id INTEGER NOT NULL, invoice_date DATE NOT NULL, due_date DATE NOT NULL, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, subtotal NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0, total_amount NUMERIC(15,2) NOT NULL, amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided')), notes TEXT, terms_and_conditions TEXT, journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_sales_invoices_customer ON business.sales_invoices(customer_id); CREATE INDEX idx_sales_invoices_dates ON business.sales_invoices(invoice_date, due_date); CREATE INDEX idx_sales_invoices_status ON business.sales_invoices(status);

CREATE TABLE business.sales_invoice_lines (
    id SERIAL PRIMARY KEY, invoice_id INTEGER NOT NULL, line_number INTEGER NOT NULL, product_id INTEGER, description VARCHAR(200) NOT NULL, quantity NUMERIC(15,2) NOT NULL, unit_price NUMERIC(15,2) NOT NULL, discount_percent NUMERIC(5,2) DEFAULT 0, discount_amount NUMERIC(15,2) DEFAULT 0, line_subtotal NUMERIC(15,2) NOT NULL, tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, line_total NUMERIC(15,2) NOT NULL, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_sales_invoice_lines_invoice ON business.sales_invoice_lines(invoice_id); CREATE INDEX idx_sales_invoice_lines_product ON business.sales_invoice_lines(product_id);

CREATE TABLE business.purchase_invoices (
    id SERIAL PRIMARY KEY, invoice_no VARCHAR(20) NOT NULL UNIQUE, vendor_id INTEGER NOT NULL, vendor_invoice_no VARCHAR(50), invoice_date DATE NOT NULL, due_date DATE NOT NULL, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, subtotal NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0, total_amount NUMERIC(15,2) NOT NULL, amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Partially Paid', 'Paid', 'Overdue', 'Disputed', 'Voided')), notes TEXT, journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_purchase_invoices_vendor ON business.purchase_invoices(vendor_id); CREATE INDEX idx_purchase_invoices_dates ON business.purchase_invoices(invoice_date, due_date); CREATE INDEX idx_purchase_invoices_status ON business.purchase_invoices(status);

CREATE TABLE business.purchase_invoice_lines (
    id SERIAL PRIMARY KEY, invoice_id INTEGER NOT NULL, line_number INTEGER NOT NULL, product_id INTEGER, description VARCHAR(200) NOT NULL, quantity NUMERIC(15,2) NOT NULL, unit_price NUMERIC(15,2) NOT NULL, discount_percent NUMERIC(5,2) DEFAULT 0, discount_amount NUMERIC(15,2) DEFAULT 0, line_subtotal NUMERIC(15,2) NOT NULL, tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, line_total NUMERIC(15,2) NOT NULL, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_purchase_invoice_lines_invoice ON business.purchase_invoice_lines(invoice_id); CREATE INDEX idx_purchase_invoice_lines_product ON business.purchase_invoice_lines(product_id);

CREATE TABLE business.bank_accounts (
    id SERIAL PRIMARY KEY, account_name VARCHAR(100) NOT NULL, account_number VARCHAR(50) NOT NULL, bank_name VARCHAR(100) NOT NULL, bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), currency_code CHAR(3) NOT NULL, opening_balance NUMERIC(15,2) DEFAULT 0, current_balance NUMERIC(15,2) DEFAULT 0, last_reconciled_date DATE, gl_account_id INTEGER NOT NULL, is_active BOOLEAN DEFAULT TRUE, description TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);

CREATE TABLE business.bank_transactions (
    id SERIAL PRIMARY KEY, bank_account_id INTEGER NOT NULL, transaction_date DATE NOT NULL, value_date DATE, transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), description VARCHAR(200) NOT NULL, reference VARCHAR(100), amount NUMERIC(15,2) NOT NULL, is_reconciled BOOLEAN DEFAULT FALSE, reconciled_date DATE, statement_date DATE, statement_id VARCHAR(50), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);

CREATE TABLE business.payments (
    id SERIAL PRIMARY KEY, payment_no VARCHAR(20) NOT NULL UNIQUE, payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')), payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')), payment_date DATE NOT NULL, entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')), entity_id INTEGER NOT NULL, bank_account_id INTEGER, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, amount NUMERIC(15,2) NOT NULL, reference VARCHAR(100), description TEXT, cheque_no VARCHAR(50), status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_payments_date ON business.payments(payment_date); CREATE INDEX idx_payments_entity ON business.payments(entity_type, entity_id); CREATE INDEX idx_payments_status ON business.payments(status);

CREATE TABLE business.payment_allocations (
    id SERIAL PRIMARY KEY, payment_id INTEGER NOT NULL, document_type VARCHAR(20) NOT NULL CHECK (document_type IN ('Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Debit Note', 'Other')), document_id INTEGER NOT NULL, amount NUMERIC(15,2) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL);
CREATE INDEX idx_payment_allocations_payment ON business.payment_allocations(payment_id); CREATE INDEX idx_payment_allocations_document ON business.payment_allocations(document_type, document_id);

-- ============================================================================
-- AUDIT SCHEMA TABLES
-- ============================================================================
CREATE TABLE audit.audit_log (
    id SERIAL PRIMARY KEY, user_id INTEGER, action VARCHAR(50) NOT NULL, entity_type VARCHAR(50) NOT NULL, entity_id INTEGER, entity_name VARCHAR(200), changes JSONB, ip_address VARCHAR(45), user_agent VARCHAR(255), timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_audit_log_user ON audit.audit_log(user_id); CREATE INDEX idx_audit_log_entity ON audit.audit_log(entity_type, entity_id); CREATE INDEX idx_audit_log_timestamp ON audit.audit_log(timestamp);

CREATE TABLE audit.data_change_history (
    id SERIAL PRIMARY KEY, table_name VARCHAR(100) NOT NULL, record_id INTEGER NOT NULL, field_name VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('Insert', 'Update', 'Delete')), changed_by INTEGER, changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_data_change_history_table_record ON audit.data_change_history(table_name, record_id); CREATE INDEX idx_data_change_history_changed_at ON audit.data_change_history(changed_at);

-- ============================================================================
-- ADDING FOREIGN KEY CONSTRAINTS (Grouped at the end)
-- ============================================================================

-- Core Schema FKs
ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE;
ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE;
ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_base_currency FOREIGN KEY (base_currency) REFERENCES accounting.currencies(code);
ALTER TABLE core.configuration ADD CONSTRAINT fk_cfg_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

-- Accounting Schema FKs
ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_parent FOREIGN KEY (parent_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.fiscal_years ADD CONSTRAINT fk_fy_closed_by FOREIGN KEY (closed_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_years ADD CONSTRAINT fk_fy_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_years ADD CONSTRAINT fk_fy_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.fiscal_periods ADD CONSTRAINT fk_fp_fiscal_year FOREIGN KEY (fiscal_year_id) REFERENCES accounting.fiscal_years(id);
ALTER TABLE accounting.fiscal_periods ADD CONSTRAINT fk_fp_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_periods ADD CONSTRAINT fk_fp_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.currencies ADD CONSTRAINT fk_curr_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.currencies ADD CONSTRAINT fk_curr_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_from_curr FOREIGN KEY (from_currency) REFERENCES accounting.currencies(code);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_to_curr FOREIGN KEY (to_currency) REFERENCES accounting.currencies(code);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_fiscal_period FOREIGN KEY (fiscal_period_id) REFERENCES accounting.fiscal_periods(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_reversing_entry FOREIGN KEY (reversing_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
-- Deferred FK for recurring_patterns cycle:
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_recurring_pattern FOREIGN KEY (recurring_pattern_id) REFERENCES accounting.recurring_patterns(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id) ON DELETE CASCADE;
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_account FOREIGN KEY (account_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);

ALTER TABLE accounting.recurring_patterns ADD CONSTRAINT fk_rp_template_entry FOREIGN KEY (template_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.recurring_patterns ADD CONSTRAINT fk_rp_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.recurring_patterns ADD CONSTRAINT fk_rp_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.dimensions ADD CONSTRAINT fk_dim_parent FOREIGN KEY (parent_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.dimensions ADD CONSTRAINT fk_dim_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.dimensions ADD CONSTRAINT fk_dim_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.budgets ADD CONSTRAINT fk_bud_fiscal_year FOREIGN KEY (fiscal_year_id) REFERENCES accounting.fiscal_years(id);
ALTER TABLE accounting.budgets ADD CONSTRAINT fk_bud_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.budgets ADD CONSTRAINT fk_bud_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_budget FOREIGN KEY (budget_id) REFERENCES accounting.budgets(id) ON DELETE CASCADE;
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_account FOREIGN KEY (account_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_fiscal_period FOREIGN KEY (fiscal_period_id) REFERENCES accounting.fiscal_periods(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.tax_codes ADD CONSTRAINT fk_tc_affects_account FOREIGN KEY (affects_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.tax_codes ADD CONSTRAINT fk_tc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.tax_codes ADD CONSTRAINT fk_tc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.gst_returns ADD CONSTRAINT fk_gstr_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.gst_returns ADD CONSTRAINT fk_gstr_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.gst_returns ADD CONSTRAINT fk_gstr_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_vendor FOREIGN KEY (vendor_id) REFERENCES business.vendors(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

-- Business Schema FKs
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_receivables_acc FOREIGN KEY (receivables_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_payables_acc FOREIGN KEY (payables_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.products ADD CONSTRAINT fk_prod_sales_acc FOREIGN KEY (sales_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_purchase_acc FOREIGN KEY (purchase_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_inventory_acc FOREIGN KEY (inventory_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.inventory_movements ADD CONSTRAINT fk_im_product FOREIGN KEY (product_id) REFERENCES business.products(id);
ALTER TABLE business.inventory_movements ADD CONSTRAINT fk_im_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);

ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_customer FOREIGN KEY (customer_id) REFERENCES business.customers(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_invoice FOREIGN KEY (invoice_id) REFERENCES business.sales_invoices(id) ON DELETE CASCADE;
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_product FOREIGN KEY (product_id) REFERENCES business.products(id);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);

ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_vendor FOREIGN KEY (vendor_id) REFERENCES business.vendors(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_invoice FOREIGN KEY (invoice_id) REFERENCES business.purchase_invoices(id) ON DELETE CASCADE;
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_product FOREIGN KEY (product_id) REFERENCES business.products(id);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);

ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_gl_account FOREIGN KEY (gl_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.payments ADD CONSTRAINT fk_pay_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
-- Note: entity_id in payments refers to customers.id or vendors.id; requires application logic or triggers to enforce based on entity_type.

ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_payment FOREIGN KEY (payment_id) REFERENCES business.payments(id) ON DELETE CASCADE;
ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);

-- Audit Schema FKs
ALTER TABLE audit.audit_log ADD CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES core.users(id);
ALTER TABLE audit.data_change_history ADD CONSTRAINT fk_dch_changed_by FOREIGN KEY (changed_by) REFERENCES core.users(id);

-- ============================================================================
-- VIEWS
-- ============================================================================
CREATE OR REPLACE VIEW accounting.account_balances AS
SELECT 
    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.parent_id,
    COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance,
    COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0) AS total_debits_activity,
    COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0) AS total_credits_activity,
    MAX(je.entry_date) AS last_activity_date
FROM accounting.accounts a
LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id
LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE
GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;

CREATE OR REPLACE VIEW accounting.trial_balance AS
SELECT 
    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.sub_type,
    CASE WHEN a.account_type IN ('Asset', 'Expense') THEN CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END ELSE CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END END AS debit_balance,
    CASE WHEN a.account_type IN ('Asset', 'Expense') THEN CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END ELSE CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END END AS credit_balance
FROM accounting.accounts a
JOIN accounting.account_balances ab ON a.id = ab.account_id
WHERE a.is_active = TRUE AND ab.balance != 0;

CREATE OR REPLACE VIEW business.customer_balances AS
SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name,
    COALESCE(SUM(si.total_amount - si.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN si.due_date < CURRENT_DATE AND si.status NOT IN ('Paid', 'Voided') THEN si.total_amount - si.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN si.status = 'Draft' THEN si.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(si.due_date), NULL) AS latest_due_date
FROM business.customers c LEFT JOIN business.sales_invoices si ON c.id = si.customer_id AND si.status NOT IN ('Paid', 'Voided')
GROUP BY c.id, c.customer_code, c.name;

CREATE OR REPLACE VIEW business.vendor_balances AS
SELECT v.id AS vendor_id, v.vendor_code, v.name AS vendor_name,
    COALESCE(SUM(pi.total_amount - pi.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN pi.due_date < CURRENT_DATE AND pi.status NOT IN ('Paid', 'Voided') THEN pi.total_amount - pi.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN pi.status = 'Draft' THEN pi.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(pi.due_date), NULL) AS latest_due_date
FROM business.vendors v LEFT JOIN business.purchase_invoices pi ON v.id = pi.vendor_id AND pi.status NOT IN ('Paid', 'Voided')
GROUP BY v.id, v.vendor_code, v.name;

CREATE OR REPLACE VIEW business.inventory_summary AS
SELECT 
    p.id AS product_id, p.product_code, p.name AS product_name, p.product_type, p.category, p.unit_of_measure,
    COALESCE(SUM(im.quantity), 0) AS current_quantity,
    CASE WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity) ELSE p.purchase_price END AS average_cost,
    COALESCE(SUM(im.total_cost), 0) AS inventory_value,
    p.sales_price AS current_sales_price, p.min_stock_level, p.reorder_point,
    CASE WHEN p.min_stock_level IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.min_stock_level THEN TRUE ELSE FALSE END AS below_minimum,
    CASE WHEN p.reorder_point IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.reorder_point THEN TRUE ELSE FALSE END AS reorder_needed
FROM business.products p LEFT JOIN business.inventory_movements im ON p.id = im.product_id
WHERE p.product_type = 'Inventory' AND p.is_active = TRUE
GROUP BY p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================
CREATE OR REPLACE FUNCTION core.get_next_sequence_value(p_sequence_name VARCHAR)
RETURNS VARCHAR AS $$
DECLARE v_sequence RECORD; v_next_value INTEGER; v_result VARCHAR;
BEGIN
    SELECT * INTO v_sequence FROM core.sequences WHERE sequence_name = p_sequence_name FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Sequence % not found', p_sequence_name; END IF;
    v_next_value := v_sequence.next_value;
    UPDATE core.sequences SET next_value = next_value + increment_by, updated_at = CURRENT_TIMESTAMP WHERE sequence_name = p_sequence_name;
    v_result := v_sequence.format_template;
    v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, ''));
    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0'));
    v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, ''));
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting.generate_journal_entry(p_journal_type VARCHAR, p_entry_date DATE, p_description VARCHAR, p_reference VARCHAR, p_source_type VARCHAR, p_source_id INTEGER, p_lines JSONB, p_user_id INTEGER)
RETURNS INTEGER AS $$ 
DECLARE v_fiscal_period_id INTEGER; v_entry_no VARCHAR; v_journal_id INTEGER; v_line JSONB; v_line_number INTEGER := 1; v_total_debits NUMERIC(15,2) := 0; v_total_credits NUMERIC(15,2) := 0;
BEGIN
    SELECT id INTO v_fiscal_period_id FROM accounting.fiscal_periods WHERE p_entry_date BETWEEN start_date AND end_date AND status = 'Open';
    IF v_fiscal_period_id IS NULL THEN RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date; END IF;
    v_entry_no := core.get_next_sequence_value('journal_entry');
    INSERT INTO accounting.journal_entries (entry_no, journal_type, entry_date, fiscal_period_id, description, reference, is_posted, source_type, source_id, created_by, updated_by) VALUES (v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description, p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id) RETURNING id INTO v_journal_id;
    FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines) LOOP
        INSERT INTO accounting.journal_entry_lines (journal_entry_id, line_number, account_id, description, debit_amount, credit_amount, currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id) 
        VALUES (v_journal_id, v_line_number, (v_line->>'account_id')::INTEGER, v_line->>'description', COALESCE((v_line->>'debit_amount')::NUMERIC, 0), COALESCE((v_line->>'credit_amount')::NUMERIC, 0), COALESCE(v_line->>'currency_code', 'SGD'), COALESCE((v_line->>'exchange_rate')::NUMERIC, 1), v_line->>'tax_code', COALESCE((v_line->>'tax_amount')::NUMERIC, 0), NULLIF(TRIM(v_line->>'dimension1_id'), '')::INTEGER, NULLIF(TRIM(v_line->>'dimension2_id'), '')::INTEGER);
        v_line_number := v_line_number + 1; v_total_debits := v_total_debits + COALESCE((v_line->>'debit_amount')::NUMERIC, 0); v_total_credits := v_total_credits + COALESCE((v_line->>'credit_amount')::NUMERIC, 0);
    END LOOP;
    IF round(v_total_debits, 2) != round(v_total_credits, 2) THEN RAISE EXCEPTION 'Journal entry is not balanced. Debits: %, Credits: %', v_total_debits, v_total_credits; END IF;
    RETURN v_journal_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting.post_journal_entry(p_journal_id INTEGER, p_user_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE v_fiscal_period_status VARCHAR; v_is_already_posted BOOLEAN;
BEGIN
    SELECT is_posted INTO v_is_already_posted FROM accounting.journal_entries WHERE id = p_journal_id;
    IF v_is_already_posted THEN RAISE EXCEPTION 'Journal entry % is already posted', p_journal_id; END IF;
    SELECT fp.status INTO v_fiscal_period_status FROM accounting.journal_entries je JOIN accounting.fiscal_periods fp ON je.fiscal_period_id = fp.id WHERE je.id = p_journal_id;
    IF v_fiscal_period_status != 'Open' THEN RAISE EXCEPTION 'Cannot post to a closed or archived fiscal period'; END IF;
    UPDATE accounting.journal_entries SET is_posted = TRUE, updated_at = CURRENT_TIMESTAMP, updated_by = p_user_id WHERE id = p_journal_id;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting.calculate_account_balance(p_account_id INTEGER, p_as_of_date DATE)
RETURNS NUMERIC AS $$
DECLARE v_balance NUMERIC(15,2) := 0; v_opening_balance NUMERIC(15,2); v_account_opening_balance_date DATE; 
BEGIN
    SELECT acc.opening_balance, acc.opening_balance_date INTO v_opening_balance, v_account_opening_balance_date FROM accounting.accounts acc WHERE acc.id = p_account_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Account with ID % not found', p_account_id; END IF;
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) INTO v_balance FROM accounting.journal_entry_lines jel JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id WHERE jel.account_id = p_account_id AND je.is_posted = TRUE AND je.entry_date <= p_as_of_date AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date);
    v_balance := v_balance + COALESCE(v_opening_balance, 0);
    RETURN v_balance;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION core.update_timestamp_trigger_func()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION audit.log_data_change_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB; v_new_data JSONB; v_change_type VARCHAR(20); v_user_id INTEGER; v_entity_id INTEGER; v_entity_name VARCHAR(200); temp_val TEXT; current_field_name_from_json TEXT;
BEGIN
    BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        END IF;
    END IF;
    IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF;
    IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF;
    BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END;
    BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END;
    ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val;
    EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END;
    INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP);
    IF TG_OP = 'UPDATE' THEN
        FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP
            IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN
                INSERT INTO audit.data_change_history (table_name,record_id,field_name,old_value,new_value,change_type,changed_by,changed_at) VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,NEW.id,current_field_name_from_json,v_old_data->>current_field_name_from_json,v_new_data->>current_field_name_from_json,'Update',v_user_id,CURRENT_TIMESTAMP);
            END IF;
        END LOOP;
    END IF;
    RETURN NULL; 
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- APPLYING TRIGGERS
-- ============================================================================
DO $$ DECLARE r RECORD; BEGIN FOR r IN SELECT table_schema, table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit') GROUP BY table_schema, table_name LOOP EXECUTE format('DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',r.table_schema,r.table_name,r.table_schema,r.table_name); END LOOP; END; $$;
DO $$ DECLARE tables_to_audit TEXT[] := ARRAY['accounting.accounts','accounting.journal_entries','accounting.fiscal_periods','accounting.fiscal_years','business.customers','business.vendors','business.products','business.sales_invoices','business.purchase_invoices','business.payments','accounting.tax_codes','accounting.gst_returns','core.users','core.roles','core.company_settings']; table_fullname TEXT; schema_name TEXT; table_name_var TEXT; BEGIN FOREACH table_fullname IN ARRAY tables_to_audit LOOP SELECT split_part(table_fullname,'.',1) INTO schema_name; SELECT split_part(table_fullname,'.',2) INTO table_name_var; EXECUTE format('DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',schema_name,table_name_var,schema_name,table_name_var); END LOOP; END; $$;

-- End of script

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

# resources/icons/product.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm-1 14H5c-.55 0-1-.45-1-1V7c0-.55.45-1 1-1h14c.55 0 1 .45 1 1v10c0 .55-.45 1-1 1z"/>
  <path d="M8 10h2v2H8zm0 4h2v2H8zm4-4h2v2h-2zm0 4h2v2h-2z"/>
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
<!DOCTYPE RCC><RCC version="1.0"> 
<qresource prefix="/">
    <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
    <file alias="icons/accounting.svg">icons/accounting.svg</file>
    <file alias="icons/customers.svg">icons/customers.svg</file>
    <file alias="icons/vendors.svg">icons/vendors.svg</file>
    <file alias="icons/product.svg">icons/product.svg</file> <!-- New Icon -->
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
    <file alias="icons/add.svg">icons/add.svg</file>
    <file alias="icons/remove.svg">icons/remove.svg</file>
    <file alias="icons/view.svg">icons/view.svg</file>
    <file alias="icons/post.svg">icons/post.svg</file>
    <file alias="icons/reverse.svg">icons/reverse.svg</file>
    <file alias="images/splash.png">images/splash.png</file>
</qresource>
</RCC>

```

# tests/integration/__init__.py
```py

```

# tests/integration/test_example_integration.py
```py

```

# tests/__init__.py
```py

```

# tests/ui/__init__.py
```py

```

# tests/ui/test_example_ui.py
```py

```

# tests/conftest.py
```py

```

# tests/unit/__init__.py
```py

```

# tests/unit/test_example_unit.py
```py

```

