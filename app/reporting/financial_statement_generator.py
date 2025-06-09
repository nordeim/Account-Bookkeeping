# File: app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import date, timedelta 
from decimal import Decimal

from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.account_service import AccountService
    from app.services.journal_service import JournalService
    from app.services.fiscal_period_service import FiscalPeriodService
    from app.services.tax_service import TaxCodeService
    from app.services.core_services import CompanySettingsService, ConfigurationService
    from app.services.accounting_services import AccountTypeService, DimensionService


class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: "AccountService", 
                 journal_service: "JournalService", 
                 fiscal_period_service: "FiscalPeriodService", 
                 account_type_service: "AccountTypeService", 
                 tax_code_service: Optional["TaxCodeService"] = None, 
                 company_settings_service: Optional["CompanySettingsService"] = None,
                 dimension_service: Optional["DimensionService"] = None,
                 configuration_service: Optional["ConfigurationService"] = None
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self.dimension_service = dimension_service 
        self.configuration_service = configuration_service
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

    async def generate_income_tax_computation(self, fiscal_year: FiscalYear) -> Dict[str, Any]:
        if not self.configuration_service:
            raise RuntimeError("ConfigurationService not available for tax computation.")
            
        start_date, end_date = fiscal_year.start_date, fiscal_year.end_date
        
        pl_data = await self.generate_profit_loss(start_date, end_date)
        net_profit_before_tax = pl_data.get('net_profit', Decimal(0))

        add_back_adjustments: List[Dict[str, Any]] = []
        less_adjustments: List[Dict[str, Any]] = []
        total_add_back = Decimal(0)
        total_less = Decimal(0)

        non_deductible_accounts = await self.account_service.get_accounts_by_tax_treatment('Non-Deductible')
        for account in non_deductible_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if activity != Decimal(0):
                add_back_adjustments.append({'name': f"{account.code} - {account.name}", 'amount': activity})
                total_add_back += activity

        non_taxable_accounts = await self.account_service.get_accounts_by_tax_treatment('Non-Taxable Income')
        for account in non_taxable_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if activity != Decimal(0):
                # Revenue has negative balance, so activity is negative. We subtract a negative -> add.
                # To show it as a subtraction, we use the absolute value.
                less_adjustments.append({'name': f"{account.code} - {account.name}", 'amount': abs(activity)})
                total_less += abs(activity)
        
        chargeable_income = net_profit_before_tax + total_add_back - total_less
        
        tax_rate_str = await self.configuration_service.get_config_value("CorpTaxRate_Default", "17.0")
        tax_rate = Decimal(tax_rate_str if tax_rate_str else "17.0")
        
        # Note: This is a simplified calculation. Real tax computation involves capital allowances, PTE, etc.
        estimated_tax = chargeable_income * (tax_rate / Decimal(100))
        if estimated_tax < 0:
            estimated_tax = Decimal(0)

        return {
            'title': 'Income Tax Computation',
            'report_date_description': f"For Financial Year Ended {fiscal_year.end_date.strftime('%d %b %Y')}",
            'fiscal_year_name': fiscal_year.year_name,
            'net_profit_before_tax': net_profit_before_tax,
            'add_back_adjustments': add_back_adjustments,
            'total_add_back': total_add_back,
            'less_adjustments': less_adjustments,
            'total_less': total_less,
            'chargeable_income': chargeable_income,
            'tax_rate': tax_rate,
            'estimated_tax': estimated_tax
        }

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
