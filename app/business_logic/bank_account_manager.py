# File: app/business_logic/bank_account_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union
from decimal import Decimal

from app.models.business.bank_account import BankAccount
# REMOVED: from app.services.business_services import BankAccountService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.accounting_services import CurrencyService
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankAccountCreateData, BankAccountUpdateData, BankAccountSummaryData
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.business_services import BankAccountService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.accounting_services import CurrencyService # ADDED


class BankAccountManager:
    def __init__(self,
                 bank_account_service: "BankAccountService",
                 account_service: "AccountService",
                 currency_service: "CurrencyService",
                 app_core: "ApplicationCore"):
        self.bank_account_service = bank_account_service
        self.account_service = account_service
        self.currency_service = currency_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_bank_account_for_dialog(self, bank_account_id: int) -> Optional[BankAccount]:
        try:
            return await self.bank_account_service.get_by_id(bank_account_id)
        except Exception as e:
            self.logger.error(f"Error fetching BankAccount ID {bank_account_id} for dialog: {e}", exc_info=True)
            return None

    async def get_bank_accounts_for_listing(
        self,
        active_only: bool = True,
        currency_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[BankAccountSummaryData]]:
        try:
            summaries = await self.bank_account_service.get_all_summary(
                active_only=active_only,
                currency_code=currency_code,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching bank account listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve bank account list: {str(e)}"])

    async def _validate_bank_account_data(
        self,
        dto: Union[BankAccountCreateData, BankAccountUpdateData],
        existing_bank_account_id: Optional[int] = None
    ) -> List[str]:
        errors: List[str] = []
        
        gl_account = await self.account_service.get_by_id(dto.gl_account_id)
        if not gl_account:
            errors.append(f"GL Account ID '{dto.gl_account_id}' not found.")
        else:
            if not gl_account.is_active:
                errors.append(f"GL Account '{gl_account.code} - {gl_account.name}' is not active.")
            if gl_account.account_type != 'Asset':
                errors.append(f"GL Account '{gl_account.code}' must be an Asset type account.")
            if not gl_account.is_bank_account: 
                errors.append(f"GL Account '{gl_account.code}' is not flagged as a bank account. Please update the Chart of Accounts.")

        currency = await self.currency_service.get_by_id(dto.currency_code)
        if not currency:
            errors.append(f"Currency Code '{dto.currency_code}' not found.")
        elif not currency.is_active:
            errors.append(f"Currency '{dto.currency_code}' is not active.")
            
        existing_by_acc_no = await self.bank_account_service.get_by_account_number(dto.account_number)
        if existing_by_acc_no and \
           (existing_bank_account_id is None or existing_by_acc_no.id != existing_bank_account_id):
            errors.append(f"Bank account number '{dto.account_number}' already exists.")

        return errors

    async def create_bank_account(self, dto: BankAccountCreateData) -> Result[BankAccount]:
        validation_errors = await self._validate_bank_account_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            bank_account_orm = BankAccount(
                account_name=dto.account_name,
                account_number=dto.account_number,
                bank_name=dto.bank_name,
                bank_branch=dto.bank_branch,
                bank_swift_code=dto.bank_swift_code,
                currency_code=dto.currency_code,
                opening_balance=dto.opening_balance,
                opening_balance_date=dto.opening_balance_date,
                gl_account_id=dto.gl_account_id,
                is_active=dto.is_active,
                description=dto.description,
                current_balance=dto.opening_balance, 
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_bank_account = await self.bank_account_service.save(bank_account_orm)
            self.logger.info(f"Bank account '{saved_bank_account.account_name}' created successfully.")
            return Result.success(saved_bank_account)
        except Exception as e:
            self.logger.error(f"Error creating bank account '{dto.account_name}': {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def update_bank_account(self, bank_account_id: int, dto: BankAccountUpdateData) -> Result[BankAccount]:
        existing_bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not existing_bank_account:
            return Result.failure([f"Bank Account with ID {bank_account_id} not found."])

        validation_errors = await self._validate_bank_account_data(dto, existing_bank_account_id=bank_account_id)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            update_data_dict = dto.model_dump(exclude={'id', 'user_id'}, exclude_unset=True)
            for key, value in update_data_dict.items():
                if hasattr(existing_bank_account, key):
                    setattr(existing_bank_account, key, value)
            
            existing_bank_account.updated_by_user_id = dto.user_id
            
            updated_bank_account = await self.bank_account_service.save(existing_bank_account)
            self.logger.info(f"Bank account '{updated_bank_account.account_name}' (ID: {bank_account_id}) updated.")
            return Result.success(updated_bank_account)
        except Exception as e:
            self.logger.error(f"Error updating bank account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def toggle_bank_account_active_status(self, bank_account_id: int, user_id: int) -> Result[BankAccount]:
        bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not bank_account:
            return Result.failure([f"Bank Account with ID {bank_account_id} not found."])
        
        if bank_account.current_balance != Decimal(0) and bank_account.is_active:
            self.logger.warning(f"Deactivating bank account ID {bank_account_id} ('{bank_account.account_name}') which has a non-zero balance of {bank_account.current_balance}.")

        bank_account.is_active = not bank_account.is_active
        bank_account.updated_by_user_id = user_id

        try:
            updated_bank_account = await self.bank_account_service.save(bank_account)
            action = "activated" if updated_bank_account.is_active else "deactivated"
            self.logger.info(f"Bank Account '{updated_bank_account.account_name}' (ID: {bank_account_id}) {action} by user ID {user_id}.")
            return Result.success(updated_bank_account)
        except Exception as e:
            self.logger.error(f"Error toggling active status for bank account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to toggle active status: {str(e)}"])
