# File: app/business_logic/bank_transaction_manager.py
import csv # For CSV parsing
from datetime import date, datetime # Added datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast

from sqlalchemy import select # For duplicate check query

from app.models.business.bank_transaction import BankTransaction
from app.services.business_services import BankTransactionService, BankAccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankTransactionCreateData, BankTransactionSummaryData
)
from app.common.enums import BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession # For type hinting session if passed

class BankTransactionManager:
    def __init__(self,
                 bank_transaction_service: BankTransactionService,
                 bank_account_service: BankAccountService, 
                 app_core: "ApplicationCore"):
        self.bank_transaction_service = bank_transaction_service
        self.bank_account_service = bank_account_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_transaction_data(
        self,
        dto: BankTransactionCreateData,
        existing_transaction_id: Optional[int] = None 
    ) -> List[str]:
        errors: List[str] = []

        bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id)
        if not bank_account:
            errors.append(f"Bank Account with ID {dto.bank_account_id} not found.")
        elif not bank_account.is_active:
            errors.append(f"Bank Account '{bank_account.account_name}' is not active.")
        
        if dto.value_date and dto.value_date < dto.transaction_date:
            errors.append("Value date cannot be before transaction date.")

        return errors

    async def create_manual_bank_transaction(self, dto: BankTransactionCreateData) -> Result[BankTransaction]:
        validation_errors = await self._validate_transaction_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)

        try:
            bank_transaction_orm = BankTransaction(
                bank_account_id=dto.bank_account_id,
                transaction_date=dto.transaction_date,
                value_date=dto.value_date,
                transaction_type=dto.transaction_type.value, 
                description=dto.description,
                reference=dto.reference,
                amount=dto.amount, 
                is_reconciled=False, 
                is_from_statement=False, # Manual entries are not from statements
                raw_statement_data=None,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            
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
        try:
            return await self.bank_transaction_service.get_by_id(transaction_id)
        except Exception as e:
            self.logger.error(f"Error fetching BankTransaction ID {transaction_id} for dialog: {e}", exc_info=True)
            return None

    async def import_bank_statement_csv(
        self, 
        bank_account_id: int, 
        csv_file_path: str, 
        user_id: int,
        column_mapping: Dict[str, Any], # Values can be int (index) or str (header)
        import_options: Dict[str, Any]  # Contains date_format_str, skip_header, etc.
    ) -> Result[Dict[str, int]]:
        
        imported_count = 0
        skipped_duplicates_count = 0
        failed_rows_count = 0
        zero_amount_skipped_count = 0
        total_rows_processed = 0

        # Extract options
        date_format_str = import_options.get("date_format_str", "%d/%m/%Y")
        skip_header = import_options.get("skip_header", True)
        use_single_amount_col = import_options.get("use_single_amount_column", False)
        debit_is_negative = import_options.get("debit_is_negative_in_single_col", False) # Default if single col, debits are usually negative on statements

        bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not bank_account or not bank_account.is_active:
            return Result.failure([f"Bank Account ID {bank_account_id} not found or is inactive."])

        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
                using_header_names = any(isinstance(v, str) for v in column_mapping.values())
                
                reader: Any
                if using_header_names:
                    if not skip_header:
                        # This case might be tricky: if headers are used for mapping but skip_header is false,
                        # it implies the "first data row" is actually the header row.
                        # DictReader inherently uses the first row as headers.
                        # The dialog should ideally enforce that if header names are used, skip_header must be true.
                        # For now, assume DictReader handles it if first line is headers.
                        pass
                    reader = csv.DictReader(csvfile)
                else: # Using indices
                    reader = csv.reader(csvfile)
                    if skip_header:
                        try:
                            next(reader) # Skip the header row if indices are used
                        except StopIteration:
                            return Result.failure(["CSV file is empty or only contains a header."])
                
                async with self.app_core.db_manager.session() as session:
                    start_row_num = 2 if skip_header else 1
                    for row_num, raw_row_data in enumerate(reader, start=start_row_num):
                        total_rows_processed += 1
                        raw_row_dict_for_json: Dict[str, str] = {}

                        try:
                            # --- Helper to extract data from row based on mapping ---
                            def get_field_value(field_key: str) -> Optional[str]:
                                specifier = column_mapping.get(field_key)
                                if specifier is None: return None
                                
                                val: Optional[str] = None
                                if using_header_names and isinstance(raw_row_data, dict):
                                    val = raw_row_data.get(str(specifier))
                                elif not using_header_names and isinstance(raw_row_data, list) and isinstance(specifier, int):
                                    if 0 <= specifier < len(raw_row_data):
                                        val = raw_row_data[specifier]
                                return val.strip() if val else None

                            if using_header_names and isinstance(raw_row_data, dict):
                                raw_row_dict_for_json = {k: str(v) for k,v in raw_row_data.items()}
                            elif isinstance(raw_row_data, list):
                                raw_row_dict_for_json = {f"column_{i}": str(val) for i, val in enumerate(raw_row_data)}
                            else: # Should not happen with csv.reader/DictReader
                                raw_row_dict_for_json = {"error": "Unknown row format"}


                            # --- Extract and validate essential fields ---
                            transaction_date_str = get_field_value("date")
                            description_str = get_field_value("description")

                            if not transaction_date_str or not description_str:
                                self.logger.warning(f"CSV Import (Row {row_num}): Skipping due to missing date or description.")
                                failed_rows_count += 1; continue
                            
                            # --- Parse date fields ---
                            try:
                                parsed_transaction_date = datetime.strptime(transaction_date_str, date_format_str).date()
                            except ValueError:
                                self.logger.warning(f"CSV Import (Row {row_num}): Invalid transaction date format '{transaction_date_str}'. Expected '{date_format_str}'. Skipping.")
                                failed_rows_count += 1; continue
                            
                            value_date_str = get_field_value("value_date")
                            parsed_value_date: Optional[date] = None
                            if value_date_str:
                                try:
                                    parsed_value_date = datetime.strptime(value_date_str, date_format_str).date()
                                except ValueError:
                                    self.logger.warning(f"CSV Import (Row {row_num}): Invalid value date format '{value_date_str}'. Using transaction date as fallback.")
                                    # No: parsed_value_date = parsed_transaction_date # Fallback if desired, or just leave as None

                            # --- Parse amount ---
                            final_bt_amount = Decimal(0)
                            if use_single_amount_col:
                                amount_str = get_field_value("amount")
                                if not amount_str:
                                    self.logger.warning(f"CSV Import (Row {row_num}): Single amount column specified but value is missing. Skipping.")
                                    failed_rows_count += 1; continue
                                try:
                                    parsed_csv_amount = Decimal(amount_str.replace(',', ''))
                                    if debit_is_negative: # Statement: Debit is <0 (outflow), Credit is >0 (inflow)
                                        final_bt_amount = parsed_csv_amount # Direct mapping to our convention
                                    else: # Statement: Debit is >0 (outflow), Credit is <0 (inflow)
                                        final_bt_amount = -parsed_csv_amount # Flip sign
                                except InvalidOperation:
                                    self.logger.warning(f"CSV Import (Row {row_num}): Invalid amount '{amount_str}' in single amount column. Skipping.")
                                    failed_rows_count += 1; continue
                            else: # Separate debit/credit columns
                                debit_str = get_field_value("debit")
                                credit_str = get_field_value("credit")
                                try:
                                    parsed_debit = Decimal(debit_str.replace(',', '')) if debit_str else Decimal(0)
                                    parsed_credit = Decimal(credit_str.replace(',', '')) if credit_str else Decimal(0)
                                    final_bt_amount = parsed_credit - parsed_debit # Credit is inflow (+), Debit is outflow (-)
                                except InvalidOperation:
                                    self.logger.warning(f"CSV Import (Row {row_num}): Invalid debit '{debit_str}' or credit '{credit_str}' amount. Skipping.")
                                    failed_rows_count += 1; continue
                            
                            if abs(final_bt_amount) < Decimal("0.005"): # Effectively zero
                                self.logger.info(f"CSV Import (Row {row_num}): Skipping due to zero net amount after parsing.")
                                zero_amount_skipped_count += 1; continue
                            
                            # --- Optional field ---
                            reference_str = get_field_value("reference")

                            # --- Duplicate Check (basic) ---
                            # Considering bank_account_id, date, amount, description, and is_from_statement
                            stmt_dup = select(BankTransaction).where(
                                BankTransaction.bank_account_id == bank_account_id,
                                BankTransaction.transaction_date == parsed_transaction_date,
                                BankTransaction.amount == final_bt_amount,
                                BankTransaction.description == description_str, # Use parsed description
                                BankTransaction.is_from_statement == True
                            )
                            existing_dup_res = await session.execute(stmt_dup)
                            if existing_dup_res.scalars().first():
                                self.logger.info(f"CSV Import (Row {row_num}): Skipping as likely duplicate of an existing statement transaction.")
                                skipped_duplicates_count += 1; continue

                            # --- Determine Transaction Type ---
                            txn_type_enum = BankTransactionTypeEnum.DEPOSIT if final_bt_amount > 0 else BankTransactionTypeEnum.WITHDRAWAL
                            
                            # --- Create ORM object ---
                            txn_orm = BankTransaction(
                                bank_account_id=bank_account_id,
                                transaction_date=parsed_transaction_date,
                                value_date=parsed_value_date,
                                transaction_type=txn_type_enum.value,
                                description=description_str,
                                reference=reference_str if reference_str else None,
                                amount=final_bt_amount,
                                is_reconciled=False,
                                is_from_statement=True,
                                raw_statement_data=raw_row_dict_for_json, 
                                created_by_user_id=user_id,
                                updated_by_user_id=user_id
                            )
                            session.add(txn_orm)
                            imported_count += 1
                        
                        except Exception as e_row: # Catch any other error for this specific row
                            self.logger.error(f"CSV Import (Row {row_num}): Unexpected error: {e_row}", exc_info=True)
                            failed_rows_count += 1
                    
                    # await session.commit() # This will be handled by the context manager
            
            summary = {
                "total_rows_in_file": total_rows_processed, 
                "imported_count": imported_count,
                "skipped_duplicates_count": skipped_duplicates_count,
                "failed_rows_count": failed_rows_count,
                "zero_amount_skipped_count": zero_amount_skipped_count
            }
            self.logger.info(f"Bank statement import complete for account ID {bank_account_id}: {summary}")
            return Result.success(summary)

        except FileNotFoundError:
            self.logger.error(f"CSV Import: File not found at path: {csv_file_path}")
            return Result.failure([f"CSV file not found: {csv_file_path}"])
        except Exception as e:
            self.logger.error(f"CSV Import: General error during import for account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"General error during CSV import: {str(e)}"])

