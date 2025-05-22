# File: app/reporting/financial_statement_generator.py
# (Updated based on previous refactoring for new models, ensure ApplicationCore type hint)
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService
from app.services.core_services import CompanySettingsService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear # Import for type hint

class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService,
                 tax_code_service: Optional[TaxCodeService] = None, # Made optional for non-GST reports
                 company_settings_service: Optional[CompanySettingsService] = None # Made optional
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        result_list = []
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date)
            display_balance = balance_value # Raw mathematical balance (Debit positive)
            
            # Sign convention for display (Assets/Expenses positive if debit, L/E/R positive if credit)
            if account.account_type in ['Liability', 'Equity', 'Revenue']:
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
            if account.account_type in ['Revenue']: # For P&L, Revenue (credit activity) shown positive
                display_activity = -activity_value
            # Expenses (debit activity) already positive

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
        expenses_orm = [a for a in accounts if a.account_type == 'Expense'] # Includes COGS if COGS is type 'Expense'
        
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
        # Using the accounting.trial_balance view from reference schema is ideal for performance.
        # If implementing in Python:
        accounts = await self.account_service.get_all_active()
        debit_accounts_list, credit_accounts_list = [], [] # Renamed to avoid conflict
        total_debits_val, total_credits_val = Decimal(0), Decimal(0) # Renamed

        account_types_map = {at.category: at for at in await self.app_core.account_type_service.get_all()} # type: ignore # Assuming AccountTypeService

        for account in accounts:
            # get_account_balance returns mathematical balance (Debit-Credit+OB)
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue

            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            
            # Determine if account is naturally debit or credit balance
            # Using account_type (which should map to AccountType.category)
            acc_type_details = account_types_map.get(account.account_type)
            is_debit_nature = acc_type_details.is_debit_balance if acc_type_details else (account.account_type in ['Asset', 'Expense'])

            if is_debit_nature: # Asset, Expense
                if raw_balance >= Decimal(0): # Normal debit balance
                    debit_accounts_list.append(account_data)
                    total_debits_val += raw_balance
                else: # Abnormal credit balance for a debit-nature account
                    account_data['balance'] = abs(raw_balance) # Show positive on credit side
                    credit_accounts_list.append(account_data)
                    total_credits_val += abs(raw_balance)
            else: # Liability, Equity, Revenue
                if raw_balance <= Decimal(0): # Normal credit balance (mathematically negative or zero)
                    credit_accounts_list.append(account_data)
                    total_credits_val += abs(raw_balance)
                else: # Abnormal debit balance for a credit-nature account
                    account_data['balance'] = raw_balance # Show positive on debit side
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

    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: # Renamed year to avoid conflict
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value)
        if not fiscal_year_obj:
            raise ValueError(f"Fiscal year definition for {year_int_value} not found.")

        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date)
        net_profit = pl_data['net_profit']
        
        adjustments = []
        tax_effect = Decimal(0)
        
        # tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')
        # Assuming 'Tax Adjustment' is a specific value in Account.tax_treatment
        # or a specific account sub_type.
        # Using a placeholder for now.
        all_accounts = await self.account_service.get_all_active()
        tax_adj_accounts = [acc for acc in all_accounts if acc.tax_treatment == 'Tax Adjustment']


        for account in tax_adj_accounts:
            # This is period activity for adjustment accounts
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            
            adjustments.append({
                'id': account.id, 'code': account.code, 'name': account.name, 
                'amount': activity, 
                # is_addition depends on if it increases or decreases profit for tax
                # Expense accounts (debit nature): positive activity adds back to profit.
                # Revenue accounts (credit nature): negative activity (credit) that's non-taxable subtracts from profit.
                'is_addition': activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0) # Simplified logic
            })
            tax_effect += activity # This assumes positive effect increases taxable income
            
        taxable_income = net_profit + tax_effect
        
        return {
            'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', # YA is usually year after income year
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
                if not line.tax_code or not line.account: continue # line.account should be loaded
                
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                
                # Amount is net amount for supplies/purchases.
                # Tax amount is directly from JE line.
                line_net_amount = (line.debit_amount or line.credit_amount) # Should be one or other
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
                    # Box 5 includes GST-exclusive value of standard-rated purchases + import value + MES purchases.
                    # Assuming 'TX' covers standard-rated local purchases.
                    if tax_code_info.code == 'TX': 
                        report_data['taxable_purchases'] += line_net_amount
                        report_data['input_tax'] += tax_on_line
                    # Add logic for other input tax types (e.g., 'IM' for imports, 'ME' for MES if separate codes)
                
                # Box 8: Adjustments (e.g. Bad Debt Relief, input tax on MES goods removed)
                # This would typically come from specific JE lines coded to GST adjustment accounts or specific tax codes.
                # For now, assuming gst_return model's tax_adjustments field would be populated from such JEs.
                # The query here doesn't explicitly identify these adjustment lines.
                # A more robust way is needed, e.g. special tax codes for adjustments.

        report_data['total_supplies'] = (
            report_data['standard_rated_supplies'] + 
            report_data['zero_rated_supplies'] + 
            report_data['exempt_supplies']
        )
        
        # Fetch pre-saved GST return if it exists, to get tax_adjustments (Box 8)
        # This method is for generating data for a report, not submitting a return.
        # If there's a saved GSTReturn for this period, its tax_adjustments can be used.
        # This part is a bit circular if this method is used *to prepare* the GSTReturn.
        # For now, let's assume tax_adjustments is 0 unless specific logic added.
        # report_data['tax_adjustments'] = ... 

        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        
        return report_data
