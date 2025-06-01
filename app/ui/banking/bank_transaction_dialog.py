# File: app/ui/banking/bank_transaction_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QDateEdit, QComboBox, QTextEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import BankTransactionCreateData, BankAccountSummaryData
from app.models.business.bank_transaction import BankTransaction
from app.common.enums import BankTransactionTypeEnum
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankTransactionDialog(QDialog):
    bank_transaction_saved = Signal(int) # Emits bank_transaction ID

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 preselected_bank_account_id: Optional[int] = None,
                 parent: Optional["QWidget"] = None): # transaction_id for editing later
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.preselected_bank_account_id = preselected_bank_account_id
        # self.transaction_id = transaction_id # For future edit mode
        
        self._bank_accounts_cache: List[Dict[str, Any]] = []

        self.setWindowTitle("New Manual Bank Transaction") # For now, only new
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        # If self.transaction_id, load existing transaction data

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.bank_account_combo = QComboBox()
        self.bank_account_combo.setMinimumWidth(250)
        form_layout.addRow("Bank Account*:", self.bank_account_combo)

        self.transaction_date_edit = QDateEdit(QDate.currentDate())
        self.transaction_date_edit.setCalendarPopup(True); self.transaction_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Transaction Date*:", self.transaction_date_edit)
        
        self.value_date_edit = QDateEdit(QDate.currentDate())
        self.value_date_edit.setCalendarPopup(True); self.value_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Value Date:", self.value_date_edit)

        self.transaction_type_combo = QComboBox()
        for type_enum in BankTransactionTypeEnum:
            self.transaction_type_combo.addItem(type_enum.value, type_enum)
        form_layout.addRow("Transaction Type*:", self.transaction_type_combo)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description of the transaction")
        form_layout.addRow("Description*:", self.description_edit)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("e.g., Check no., transfer ID")
        form_layout.addRow("Reference:", self.reference_edit)

        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setDecimals(2); self.amount_edit.setRange(0.01, 999999999.99) # Magnitude only
        self.amount_edit.setGroupSeparatorShown(True); self.amount_edit.setPrefix("$ ") # Placeholder, update with currency
        form_layout.addRow("Amount (Magnitude)*:", self.amount_edit)
        
        # Note: GL Contra Account selection could be added here for immediate JE posting.
        # For basic entry, this is deferred.

        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_transaction)
        self.button_box.rejected.connect(self.reject)
        self.bank_account_combo.currentIndexChanged.connect(self._update_amount_prefix)
        self.transaction_type_combo.currentDataChanged.connect(self._on_transaction_type_changed)


    @Slot()
    def _update_amount_prefix(self):
        bank_account_id = self.bank_account_combo.currentData()
        if bank_account_id and bank_account_id != 0:
            selected_ba = next((ba for ba in self._bank_accounts_cache if ba.get("id") == bank_account_id), None)
            if selected_ba and selected_ba.get("currency_code"):
                self.amount_edit.setPrefix(f"{selected_ba.get('currency_code')} ")
                return
        self.amount_edit.setPrefix("$ ") # Default/fallback

    @Slot(BankTransactionTypeEnum)
    def _on_transaction_type_changed(self, txn_type: Optional[BankTransactionTypeEnum]):
        # Could provide hints or change UI based on type, e.g., suggest positive/negative
        # For now, mainly for internal logic when saving.
        pass

    async def _load_combo_data(self):
        try:
            if self.app_core.bank_account_manager:
                result = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(active_only=True, page_size=-1) # Get all active
                if result.is_success and result.value:
                    self._bank_accounts_cache = [ba.model_dump() for ba in result.value]
            
            bank_accounts_json = json.dumps(self._bank_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, bank_accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for BankTransactionDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load bank accounts: {str(e)}")

    @Slot(str)
    def _populate_combos_slot(self, bank_accounts_json: str):
        try:
            bank_accounts_data = json.loads(bank_accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing bank accounts JSON for BankTransactionDialog: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing bank account data."); return

        self.bank_account_combo.clear()
        self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        for ba in bank_accounts_data:
            self.bank_account_combo.addItem(f"{ba['account_name']} ({ba['bank_name']} - {ba['account_number'][-4:] if ba['account_number'] else 'N/A'})", ba['id'])
        
        if self.preselected_bank_account_id:
            idx = self.bank_account_combo.findData(self.preselected_bank_account_id)
            if idx != -1:
                self.bank_account_combo.setCurrentIndex(idx)
        elif self.bank_account_combo.count() > 1: # More than just "-- Select..."
             self.bank_account_combo.setCurrentIndex(1) # Default to first actual account
        
        self._update_amount_prefix()


    @Slot()
    def on_save_transaction(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        bank_account_id_data = self.bank_account_combo.currentData()
        if not bank_account_id_data or bank_account_id_data == 0:
            QMessageBox.warning(self, "Validation Error", "Bank Account must be selected.")
            return
        
        bank_account_id = int(bank_account_id_data)
        transaction_date_py = self.transaction_date_edit.date().toPython()
        value_date_py = self.value_date_edit.date().toPython()
        
        selected_type_enum = self.transaction_type_combo.currentData()
        if not isinstance(selected_type_enum, BankTransactionTypeEnum):
            QMessageBox.warning(self, "Validation Error", "Invalid transaction type selected.")
            return

        description_str = self.description_edit.text().strip()
        if not description_str:
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        
        reference_str = self.reference_edit.text().strip() or None
        amount_magnitude = Decimal(str(self.amount_edit.value()))

        # Determine signed amount based on transaction type
        signed_amount: Decimal
        if selected_type_enum in [BankTransactionTypeEnum.DEPOSIT, BankTransactionTypeEnum.INTEREST]:
            signed_amount = amount_magnitude # Positive
        elif selected_type_enum in [BankTransactionTypeEnum.WITHDRAWAL, BankTransactionTypeEnum.FEE]:
            signed_amount = -amount_magnitude # Negative
        elif selected_type_enum == BankTransactionTypeEnum.TRANSFER:
            # For transfers, amount could be positive or negative depending on direction.
            # This basic dialog might need a "Transfer In/Out" distinction or more UI.
            # For now, assume positive for "Transfer In" and user adjusts if it's "Transfer Out".
            # Better: a separate "Transfer" dialog or more type options.
            # For "Basic Entry", let's assume transfers handled by specific UIs later or this is generic.
            # For now, let user decide sign by making a choice.
            # A simple approach for this dialog: make Transfers require user to specify sign
            # implicitly by selecting "Deposit" or "Withdrawal" type for the transfer leg.
            # Or prompt user:
            reply = QMessageBox.question(self, "Transfer Direction", 
                                         "Is this transfer an INFLOW (money in) or OUTFLOW (money out) for this bank account?",
                                         "Inflow", "Outflow")
            if reply == 0: # Inflow
                signed_amount = amount_magnitude
            else: # Outflow
                signed_amount = -amount_magnitude
        else: # Adjustment
            signed_amount = amount_magnitude # Allow positive or negative based on user's intent for adjustment

        try:
            dto = BankTransactionCreateData(
                bank_account_id=bank_account_id,
                transaction_date=transaction_date_py,
                value_date=value_date_py,
                transaction_type=selected_type_enum,
                description=description_str,
                reference=reference_str,
                amount=signed_amount,
                user_id=self.current_user_id
            )
        except ValueError as pydantic_error: # Catches Pydantic DTO validation errors
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
             return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
        )

    async def _perform_save(self, dto: BankTransactionCreateData):
        if not self.app_core.bank_transaction_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Bank Transaction Manager not available."))
            return

        result: Result[BankTransaction]
        result = await self.app_core.bank_transaction_manager.create_manual_bank_transaction(dto)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str, f"Bank Transaction created successfully (ID: {result.value.id})."))
            self.bank_transaction_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to save bank transaction:\n{', '.join(result.errors)}"))
