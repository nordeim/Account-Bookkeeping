# File: app/tax/tax_calculator.py
# (Content previously generated and reviewed, uses Decimal for amounts)
from decimal import Decimal
from typing import List, Optional, Any

from app.services.tax_service import TaxCodeService # Path might change if service moved
from app.utils.pydantic_models import TaxCalculationResultData, TransactionTaxData, TransactionLineTaxData
from app.models.accounting.tax_code import TaxCode # For tax_code_info type hint

class TaxCalculator:
    """Tax calculation engine for Singapore taxes"""
    
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
        
        tax_code_info: Optional[TaxCode] = await self.tax_code_service.get_tax_code(tax_code_str) # type: ignore
        if not tax_code_info:
            return result 
        
        if tax_code_info.tax_type == 'GST':
            return await self._calculate_gst(amount, tax_code_info, transaction_type)
        elif tax_code_info.tax_type == 'Withholding Tax':
            return await self._calculate_withholding_tax(amount, tax_code_info, transaction_type)
        return result
    
    async def _calculate_gst(self, amount: Decimal, tax_code_info: TaxCode, transaction_type: str) -> TaxCalculationResultData:
        tax_rate = Decimal(str(tax_code_info.rate))
        
        # Assumption: 'amount' is NET for calculation.
        # If transaction_type implied 'amount' is GROSS, logic would change:
        # is_tax_inclusive = transaction_type in ['Sales Invoice', 'Sales Receipt'] # Example
        # if is_tax_inclusive:
        #     net_amount = amount / (1 + tax_rate / Decimal(100))
        #     tax_amount = amount - net_amount
        # else:
        #     net_amount = amount
        #     tax_amount = net_amount * tax_rate / Decimal(100)
        
        net_amount = amount # Current assumption
        tax_amount = net_amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=net_amount
        )
    
    async def _calculate_withholding_tax(self, amount: Decimal, tax_code_info: TaxCode, transaction_type: str) -> TaxCalculationResultData:
        applicable_transaction_types = ['Purchase Payment', 'Expense Payment'] # Example
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
