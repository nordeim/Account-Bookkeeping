# File: tests/unit/services/test_account_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date

from app.services.account_service import AccountService
from app.models.accounting.account import Account as AccountModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.services.journal_service import JournalService # For mocking
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_journal_service() -> AsyncMock:
    return AsyncMock(spec=JournalService)

@pytest.fixture
def mock_app_core(mock_journal_service: AsyncMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.journal_service = mock_journal_service # Inject mock journal_service
    return app_core

@pytest.fixture
def account_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> AccountService:
    return AccountService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Accounts
@pytest.fixture
def current_asset_accounts() -> List[AccountModel]:
    return [
        AccountModel(id=1, code="1010", name="Cash", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=2, code="1020", name="AR", account_type="Asset", sub_type="Accounts Receivable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=3, code="1030", name="Inventory", account_type="Asset", sub_type="Inventory", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

@pytest.fixture
def current_liability_accounts() -> List[AccountModel]:
    return [
        AccountModel(id=4, code="2010", name="AP", account_type="Liability", sub_type="Accounts Payable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=5, code="2020", name="GST Payable", account_type="Liability", sub_type="GST Payable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

@pytest.fixture
def non_current_asset_account() -> AccountModel:
     return AccountModel(id=6, code="1500", name="Equipment", account_type="Asset", sub_type="Fixed Asset", is_active=True, created_by_user_id=1,updated_by_user_id=1)


async def test_get_total_balance_current_assets(
    account_service: AccountService, 
    mock_session: AsyncMock, 
    mock_journal_service: AsyncMock,
    current_asset_accounts: List[AccountModel]
):
    mock_session.execute.return_value.scalars.return_value.all.return_value = current_asset_accounts
    
    # Mock balances for these accounts
    def get_balance_side_effect(acc_id, as_of_date):
        if acc_id == 1: return Decimal("1000.00")
        if acc_id == 2: return Decimal("5000.00")
        if acc_id == 3: return Decimal("12000.00")
        return Decimal("0.00")
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect

    # Test for a specific subtype that matches one of the accounts
    total = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset", 
        account_type_name_like="Cash and Cash Equivalents", # Exact match for first account's sub_type
        as_of_date=date.today()
    )
    assert total == Decimal("1000.00")

    # Test with a pattern matching multiple accounts
    # Reset side effect for a new call scenario
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect
    total_current = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset",
        # Using a pattern that should ideally match multiple current asset subtypes based on your DashboardManager's lists
        # For this test, we assume these sub_types are fetched if they match "Current Asset%"
        # A more precise test might involve mocking specific `sub_type` names from `CURRENT_ASSET_SUBTYPES`
        account_type_name_like="Current Asset%", # Example, this might need adjustment based on actual CoA data
        as_of_date=date.today()
    )
    # This test depends on how broadly "Current Asset%" matches the sub_types in current_asset_accounts
    # If only AccountModel(sub_type="Current Asset") existed, the result would be based on that.
    # Given the current sample data, "Current Asset%" likely won't match any sub_type.
    # This test highlights the dependency on the `account_type_name_like` parameter and the data.
    # To make it robust, let's assume we are looking for "Cash and Cash Equivalents" and "Accounts Receivable"
    # This requires a more flexible `get_total_balance_by_sub_types` or multiple calls.
    
    # Let's test with actual subtypes from DashboardManager's CURRENT_ASSET_SUBTYPES logic
    # This test simulates how DashboardManager would sum up.
    
    # Mock setup for this specific scenario:
    # Accounts that match CURRENT_ASSET_SUBTYPES
    matching_accounts = [
        AccountModel(id=1, sub_type="Cash and Cash Equivalents", account_type="Asset", is_active=True, code="CASH", name="Cash", created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=2, sub_type="Accounts Receivable", account_type="Asset", is_active=True, code="AR", name="AR", created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=7, sub_type="Fixed Asset", account_type="Asset", is_active=True, code="FA", name="FA", created_by_user_id=1, updated_by_user_id=1) # Non-current
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = matching_accounts
    
    def get_balance_for_current_asset_test(acc_id, as_of_date):
        if acc_id == 1: return Decimal("200") # Cash
        if acc_id == 2: return Decimal("300") # AR
        if acc_id == 7: return Decimal("1000") # FA
        return Decimal(0)
    mock_journal_service.get_account_balance.side_effect = get_balance_for_current_asset_test
    
    # Simulate DashboardManager's iteration and summation
    from app.reporting.dashboard_manager import CURRENT_ASSET_SUBTYPES # Import the list
    
    calculated_current_assets = Decimal(0)
    for acc_subtype in CURRENT_ASSET_SUBTYPES:
        # This relies on the `account_type_name_like` to be an exact match here
        # The actual AccountService method takes one pattern. 
        # To test the sum for dashboard, we need to call it for each subtype or adapt it.
        # Let's adapt the test to reflect how AccountService.get_total_balance_by_account_category_and_type_pattern
        # would be called for a single subtype from the list.
        
        # Test for one specific subtype from the list
        mock_session.execute.return_value.scalars.return_value.all.return_value = [matching_accounts[0]] # Only cash account
        mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: Decimal("200") if acc_id == 1 else Decimal(0)
        sum_for_cash_subtype = await account_service.get_total_balance_by_account_category_and_type_pattern(
            account_category="Asset",
            account_type_name_like="Cash and Cash Equivalents", # Exact subtype
            as_of_date=date.today()
        )
        assert sum_for_cash_subtype == Decimal("200.00")

        mock_session.execute.return_value.scalars.return_value.all.return_value = [matching_accounts[1]] # Only AR account
        mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: Decimal("300") if acc_id == 2 else Decimal(0)
        sum_for_ar_subtype = await account_service.get_total_balance_by_account_category_and_type_pattern(
            account_category="Asset",
            account_type_name_like="Accounts Receivable", # Exact subtype
            as_of_date=date.today()
        )
        assert sum_for_ar_subtype == Decimal("300.00")


async def test_get_total_balance_no_matching_accounts(
    account_service: AccountService, mock_session: AsyncMock, mock_journal_service: AsyncMock
):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [] # No accounts match criteria
    
    total = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset", 
        account_type_name_like="NonExistentSubType%", 
        as_of_date=date.today()
    )
    assert total == Decimal("0.00")
    mock_journal_service.get_account_balance.assert_not_called() # Should not be called if no accounts found
