# File: tests/unit/tax/test_tax_calculator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.tax.tax_calculator import TaxCalculator
from app.services.tax_service import TaxCodeService # Interface for mocking
from app.models.accounting.tax_code import TaxCode as TaxCodeModel # ORM Model for mock return
from app.utils.pydantic_models import TaxCalculationResultData

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_tax_code_service() -> AsyncMock:
    """Fixture to create a mock TaxCodeService."""
    service = AsyncMock(spec=TaxCodeService)
    return service

@pytest.fixture
def tax_calculator(mock_tax_code_service: AsyncMock) -> TaxCalculator:
    """Fixture to create a TaxCalculator instance with a mocked service."""
    return TaxCalculator(tax_code_service=mock_tax_code_service)

async def test_calculate_line_tax_no_tax_code(tax_calculator: TaxCalculator):
    """Test tax calculation when no tax code is provided."""
    amount = Decimal("100.00")
    result = await tax_calculator.calculate_line_tax(amount, None, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id is None

async def test_calculate_line_tax_zero_amount(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test tax calculation when the input amount is zero."""
    tax_code_str = "SR"
    # Mock get_tax_code even for zero amount, as it might still be called
    mock_tax_code_service.get_tax_code.return_value = TaxCodeModel(
        id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101
    )
    result = await tax_calculator.calculate_line_tax(Decimal("0.00"), tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == Decimal("0.00")
    # tax_account_id might be populated if tax_code_info is fetched, even for 0 tax.
    # The current TaxCalculator logic returns tax_code_info.affects_account_id if tax_code_info is found.
    assert result.tax_account_id == 101 

async def test_calculate_line_tax_gst_standard_rate(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test GST calculation with a standard rate."""
    amount = Decimal("100.00")
    tax_code_str = "SR"
    mock_tax_code_info = TaxCodeModel(
        id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("9.00") # 100.00 * 9%
    assert result.taxable_amount == amount
    assert result.tax_account_id == 101
    mock_tax_code_service.get_tax_code.assert_called_once_with(tax_code_str)

async def test_calculate_line_tax_gst_zero_rate(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test GST calculation with a zero rate."""
    amount = Decimal("200.00")
    tax_code_str = "ZR"
    mock_tax_code_info = TaxCodeModel(
        id=2, code="ZR", description="Zero Rate", tax_type="GST", rate=Decimal("0.00"), affects_account_id=102
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id == 102

async def test_calculate_line_tax_non_gst_type(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test tax calculation when tax code is not GST (should be handled by different logic or result in zero GST)."""
    amount = Decimal("100.00")
    tax_code_str = "WHT15"
    mock_tax_code_info = TaxCodeModel(
        id=3, code="WHT15", description="Withholding Tax 15%", tax_type="Withholding Tax", rate=Decimal("15.00"), affects_account_id=103
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    # Assuming calculate_line_tax focuses on GST if called by sales/purchase context, 
    # or routes to _calculate_withholding_tax.
    # The current implementation of calculate_line_tax explicitly calls _calculate_gst or _calculate_withholding_tax.
    # Let's test the WHT path specifically for a purchase-like transaction type.
    result_wht = await tax_calculator.calculate_line_tax(amount, tax_code_str, "Purchase Payment")

    assert result_wht.tax_amount == Decimal("15.00") # 100.00 * 15%
    assert result_wht.taxable_amount == amount
    assert result_wht.tax_account_id == 103

    # Test that it returns zero GST for a Sales transaction type with a WHT code
    result_sales_with_wht_code = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    assert result_sales_with_wht_code.tax_amount == Decimal("0.00") # WHT not applicable directly on sales invoice line via this mechanism
    assert result_sales_with_wht_code.taxable_amount == amount
    assert result_sales_with_wht_code.tax_account_id == 103 # affects_account_id is still returned

async def test_calculate_line_tax_unknown_tax_code(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test tax calculation when the tax code is not found."""
    amount = Decimal("100.00")
    tax_code_str = "UNKNOWN"
    mock_tax_code_service.get_tax_code.return_value = None # Simulate tax code not found
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id is None

async def test_calculate_line_tax_rounding(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test rounding of tax amounts."""
    amount = Decimal("99.99")
    tax_code_str = "SR"
    mock_tax_code_info = TaxCodeModel(
        id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    # 99.99 * 0.09 = 8.9991, should round to 9.00
    assert result.tax_amount == Decimal("9.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id == 101

# Example for testing calculate_transaction_taxes (more complex setup)
@pytest.fixture
def sample_transaction_data_gst() -> MagicMock:
    # Using MagicMock for transaction_data because TransactionTaxData is a Pydantic model
    # and we are focusing on the TaxCalculator's interaction with it.
    # Alternatively, create actual TransactionTaxData instances.
    mock_data = MagicMock()
    mock_data.transaction_type = "SalesInvoice"
    mock_data.lines = [
        MagicMock(amount=Decimal("100.00"), tax_code="SR", account_id=1, index=0),
        MagicMock(amount=Decimal("50.00"), tax_code="ZR", account_id=2, index=1),
        MagicMock(amount=Decimal("25.00"), tax_code=None, account_id=3, index=2),
    ]
    return mock_data

async def test_calculate_transaction_taxes_gst(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock, sample_transaction_data_gst: MagicMock):
    """Test calculation for a whole transaction with multiple lines."""
    
    # Setup mock return values for get_tax_code for each tax code used
    def get_tax_code_side_effect(code_str):
        if code_str == "SR":
            return TaxCodeModel(id=1, code="SR", description="Std", tax_type="GST", rate=Decimal("9.00"), affects_account_id=201)
        elif code_str == "ZR":
            return TaxCodeModel(id=2, code="ZR", description="Zero", tax_type="GST", rate=Decimal("0.00"), affects_account_id=202)
        return None
    mock_tax_code_service.get_tax_code.side_effect = get_tax_code_side_effect

    results = await tax_calculator.calculate_transaction_taxes(sample_transaction_data_gst)
    
    assert len(results) == 3
    
    # Line 0: SR
    assert results[0]['line_index'] == 0
    assert results[0]['tax_amount'] == Decimal("9.00") # 100 * 9%
    assert results[0]['taxable_amount'] == Decimal("100.00")
    assert results[0]['tax_account_id'] == 201
    
    # Line 1: ZR
    assert results[1]['line_index'] == 1
    assert results[1]['tax_amount'] == Decimal("0.00")
    assert results[1]['taxable_amount'] == Decimal("50.00")
    assert results[1]['tax_account_id'] == 202
    
    # Line 2: No tax code
    assert results[2]['line_index'] == 2
    assert results[2]['tax_amount'] == Decimal("0.00")
    assert results[2]['taxable_amount'] == Decimal("25.00")
    assert results[2]['tax_account_id'] is None
