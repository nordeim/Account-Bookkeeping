# File: app/business_logic/bank_transaction_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union
from decimal import Decimal
from datetime import date

from app.models.business.bank_transaction import BankTransaction
from app.services.business_services import BankTransactionService, BankAccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankTransactionCreateData, BankTransactionSummaryData
)
from app.common.enums import BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class BankTransactionManager:
    def __init__(self,
                 bank_transaction_service: BankTransactionService,
                 bank_account_service: BankAccountService, # To validate bank account
                 app_core: "ApplicationCore"):
        self.bank_transaction_service = bank_transaction_service
        self.bank_account_service = bank_account_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_transaction_data(
        self,
        dto: BankTransactionCreateData,
        existing_transaction_id: Optional[int] = None # For future update validation
    ) -> List[str]:
        errors: List[str] = []

        bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id)
        if not bank_account:
            errors.append(f"Bank Account with ID {dto.bank_account_id} not found.")
        elif not bank_account.is_active:
            errors.append(f"Bank Account '{bank_account.account_name}' is not active.")
        
        # Pydantic DTO already validates amount sign vs type.
        # Additional business rules can go here.
        # For example, for 'Transfer' type, a corresponding transaction might be expected.
        # Or limits on certain transaction types.

        if dto.value_date and dto.value_date < dto.transaction_date:
            errors.append("Value date cannot be before transaction date.")

        return errors

    async def create_manual_bank_transaction(self, dto: BankTransactionCreateData) -> Result[BankTransaction]:
        validation_errors = await self._validate_transaction_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            # Ensure amount has correct sign based on type (Pydantic validator should handle this, but double-check here if needed)
            # For this basic entry, we rely on the UI/DTO to provide the correctly signed amount.
            
            bank_transaction_orm = BankTransaction(
                bank_account_id=dto.bank_account_id,
                transaction_date=dto.transaction_date,
                value_date=dto.value_date,
                transaction_type=dto.transaction_type.value, # Store enum value
                description=dto.description,
                reference=dto.reference,
                amount=dto.amount, # Assumed to be signed correctly from DTO
                is_reconciled=False, # Manual entries are initially unreconciled
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
                # journal_entry_id will be None for now
            )
            
            # The database trigger `update_bank_account_balance_trigger_func`
            # is expected to handle updating BankAccount.current_balance.
            saved_transaction = await self.bank_transaction_service.save(bank_transaction_orm)
            
            self.logger.info(f"Manual bank transaction ID {saved_transaction.id} created for bank account ID {dto.bank_account_id}.")
            return Result.success(saved_transaction)
        except Exception as e:
            self.logger.error(f"Error creating manual bank transaction: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])

    async def get_transactions_for_bank_account(
        self,
        bank_account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[BankTransactionTypeEnum] = None,
        is_reconciled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[BankTransactionSummaryData]]:
        try:
            summaries = await self.bank_transaction_service.get_all_for_bank_account(
                bank_account_id=bank_account_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                is_reconciled=is_reconciled,
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching bank transactions for account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve bank transaction list: {str(e)}"])

    async def get_bank_transaction_for_dialog(self, transaction_id: int) -> Optional[BankTransaction]:
        # For viewing/editing a specific transaction
        try:
            return await self.bank_transaction_service.get_by_id(transaction_id)
        except Exception as e:
            self.logger.error(f"Error fetching BankTransaction ID {transaction_id} for dialog: {e}", exc_info=True)
            return None
