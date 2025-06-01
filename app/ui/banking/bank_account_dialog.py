# File: app/ui/banking/bank_account_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, 
    QDoubleSpinBox # For opening_balance
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import BankAccountCreateData, BankAccountUpdateData
from app.models.business.bank_account import BankAccount
from app.models.accounting.account import Account # For Account DTO/ORM
from app.models.accounting.currency import Currency # For Currency DTO/ORM
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankAccountDialog(QDialog):
    bank_account_saved = Signal(int) # Emits bank_account ID

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 bank_account_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.bank_account_id = bank_account_id
        self.loaded_bank_account_orm: Optional[BankAccount] = None # Store loaded ORM

        self._currencies_cache: List[Dict[str, Any]] = [] # Store as dicts for combo
        self._gl_accounts_cache: List[Dict[str, Any]] = [] # Store as dicts for combo
        
        self.setWindowTitle("Edit Bank Account" if self.bank_account_id else "Add New Bank Account")
        self.setMinimumWidth(550)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        if self.bank_account_id:
            QTimer.singleShot(100, lambda: schedule_task_from_qt(self._load_existing_bank_account_details()))
        else: # New account
             self._on_opening_balance_changed(self.opening_balance_edit.value()) # Initial state for OB date

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.account_name_edit = QLineEdit(); form_layout.addRow("Account Name*:", self.account_name_edit)
        self.bank_name_edit = QLineEdit(); form_layout.addRow("Bank Name*:", self.bank_name_edit)
        self.account_number_edit = QLineEdit(); form_layout.addRow("Account Number*:", self.account_number_edit)
        self.bank_branch_edit = QLineEdit(); form_layout.addRow("Bank Branch:", self.bank_branch_edit)
        self.bank_swift_code_edit = QLineEdit(); form_layout.addRow("SWIFT Code:", self.bank_swift_code_edit)
        
        self.currency_combo = QComboBox(); self.currency_combo.setMinimumWidth(150)
        form_layout.addRow("Currency*:", self.currency_combo)
        
        self.gl_account_combo = QComboBox(); self.gl_account_combo.setMinimumWidth(250)
        form_layout.addRow("GL Link (Asset Account)*:", self.gl_account_combo)

        self.opening_balance_edit = QDoubleSpinBox()
        self.opening_balance_edit.setDecimals(2); self.opening_balance_edit.setRange(-999999999.99, 999999999.99)
        self.opening_balance_edit.setGroupSeparatorShown(True); self.opening_balance_edit.setValue(0.00)
        form_layout.addRow("Opening Balance:", self.opening_balance_edit)

        self.opening_balance_date_edit = QDateEdit(QDate.currentDate())
        self.opening_balance_date_edit.setCalendarPopup(True); self.opening_balance_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.opening_balance_date_edit.setEnabled(False) # Enabled if OB is non-zero
        form_layout.addRow("OB Date:", self.opening_balance_date_edit)
        
        self.description_edit = QTextEdit(); self.description_edit.setFixedHeight(60)
        form_layout.addRow("Description:", self.description_edit)

        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True)
        form_layout.addRow(self.is_active_check)
        
        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_bank_account)
        self.button_box.rejected.connect(self.reject)
        self.opening_balance_edit.valueChanged.connect(self._on_opening_balance_changed)

    @Slot(float)
    def _on_opening_balance_changed(self, value: float):
        self.opening_balance_date_edit.setEnabled(abs(value) > 0.005) # Enable if non-zero

    async def _load_combo_data(self):
        try:
            if self.app_core.currency_manager:
                active_currencies = await self.app_core.currency_manager.get_all_active_currencies()
                self._currencies_cache = [{"code": c.code, "name": c.name} for c in active_currencies]
            
            if self.app_core.chart_of_accounts_manager:
                # Fetch active Asset accounts flagged as bank accounts
                asset_accounts = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(
                    account_type="Asset", active_only=True
                )
                # Further filter for those that are `is_bank_account=True`
                self._gl_accounts_cache = [
                    {"id": acc.id, "code": acc.code, "name": acc.name} 
                    for acc in asset_accounts if acc.is_bank_account
                ]
            
            currencies_json = json.dumps(self._currencies_cache, default=json_converter)
            gl_accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, currencies_json), Q_ARG(str, gl_accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for BankAccountDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str)
    def _populate_combos_slot(self, currencies_json: str, gl_accounts_json: str):
        try:
            currencies_data = json.loads(currencies_json, object_hook=json_date_hook)
            gl_accounts_data = json.loads(gl_accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing combo JSON data for BankAccountDialog: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing dropdown data."); return

        self.currency_combo.clear()
        for curr in currencies_data: self.currency_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        if self.currency_combo.count() > 0: self.currency_combo.setCurrentIndex(0) # Default to first

        self.gl_account_combo.clear()
        self.gl_account_combo.addItem("-- Select GL Account --", 0) # Represents None
        for acc in gl_accounts_data: self.gl_account_combo.addItem(f"{acc['code']} - {acc['name']}", acc['id'])
        
        # If editing and ORM data is already loaded, apply it to combos
        if self.loaded_bank_account_orm:
            self._populate_fields_from_orm_after_combos(self.loaded_bank_account_orm)

    async def _load_existing_bank_account_details(self):
        if not self.bank_account_id or not self.app_core.bank_account_manager: return
        
        self.loaded_bank_account_orm = await self.app_core.bank_account_manager.get_bank_account_for_dialog(self.bank_account_id)
        if self.loaded_bank_account_orm:
            # Serialize data for thread-safe UI update
            account_dict = {col.name: getattr(self.loaded_bank_account_orm, col.name) 
                            for col in BankAccount.__table__.columns 
                            if hasattr(self.loaded_bank_account_orm, col.name)}
            account_json_str = json.dumps(account_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, account_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Bank Account ID {self.bank_account_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, account_json_str: str):
        try:
            data = json.loads(account_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse bank account data for editing."); return
        self._populate_fields_from_dict(data)

    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.account_name_edit.setText(data.get("account_name", ""))
        self.account_number_edit.setText(data.get("account_number", ""))
        self.bank_name_edit.setText(data.get("bank_name", ""))
        self.bank_branch_edit.setText(data.get("bank_branch", "") or "")
        self.bank_swift_code_edit.setText(data.get("bank_swift_code", "") or "")
        
        ob_val = data.get("opening_balance")
        self.opening_balance_edit.setValue(float(Decimal(str(ob_val))) if ob_val is not None else 0.0)
        ob_date_val = data.get("opening_balance_date")
        self.opening_balance_date_edit.setDate(QDate(ob_date_val) if ob_date_val else QDate.currentDate())
        self._on_opening_balance_changed(self.opening_balance_edit.value()) # Update date edit enabled state

        self.description_edit.setText(data.get("description", "") or "")
        self.is_active_check.setChecked(data.get("is_active", True))

        # Set comboboxes - ensure they are populated first
        currency_idx = self.currency_combo.findData(data.get("currency_code", "SGD"))
        if currency_idx != -1: self.currency_combo.setCurrentIndex(currency_idx)
        
        gl_acc_id = data.get("gl_account_id")
        gl_acc_idx = self.gl_account_combo.findData(gl_acc_id if gl_acc_id is not None else 0)
        if gl_acc_idx != -1: self.gl_account_combo.setCurrentIndex(gl_acc_idx)

    def _populate_fields_from_orm_after_combos(self, ba_orm: BankAccount): # Called after combos are loaded
        currency_idx = self.currency_combo.findData(ba_orm.currency_code)
        if currency_idx != -1: self.currency_combo.setCurrentIndex(currency_idx)
        else: self.app_core.logger.warning(f"Loaded bank account currency '{ba_orm.currency_code}' not found in combo.")

        gl_acc_idx = self.gl_account_combo.findData(ba_orm.gl_account_id or 0)
        if gl_acc_idx != -1: self.gl_account_combo.setCurrentIndex(gl_acc_idx)
        elif ba_orm.gl_account_id:
             self.app_core.logger.warning(f"Loaded bank account GL ID '{ba_orm.gl_account_id}' not found in combo.")


    @Slot()
    def on_save_bank_account(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        gl_account_id_data = self.gl_account_combo.currentData()
        if not gl_account_id_data or gl_account_id_data == 0:
            QMessageBox.warning(self, "Validation Error", "GL Link Account is required.")
            return
        
        ob_val = Decimal(str(self.opening_balance_edit.value()))
        ob_date_val = self.opening_balance_date_edit.date().toPython() if self.opening_balance_date_edit.isEnabled() else None
        
        common_data_dict = {
            "account_name": self.account_name_edit.text().strip(),
            "account_number": self.account_number_edit.text().strip(),
            "bank_name": self.bank_name_edit.text().strip(),
            "bank_branch": self.bank_branch_edit.text().strip() or None,
            "bank_swift_code": self.bank_swift_code_edit.text().strip() or None,
            "currency_code": self.currency_combo.currentData() or "SGD",
            "opening_balance": ob_val,
            "opening_balance_date": ob_date_val,
            "gl_account_id": int(gl_account_id_data),
            "is_active": self.is_active_check.isChecked(),
            "description": self.description_edit.toPlainText().strip() or None,
            "user_id": self.current_user_id
        }

        try:
            if self.bank_account_id:
                dto = BankAccountUpdateData(id=self.bank_account_id, **common_data_dict) # type: ignore
            else:
                dto = BankAccountCreateData(**common_data_dict) # type: ignore
        except ValueError as pydantic_error:
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
             return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
        )

    async def _perform_save(self, dto: Union[BankAccountCreateData, BankAccountUpdateData]):
        if not self.app_core.bank_account_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Bank Account Manager not available."))
            return

        result: Result[BankAccount]
        is_update = isinstance(dto, BankAccountUpdateData)
        action_verb_past = "updated" if is_update else "created"

        if is_update:
            result = await self.app_core.bank_account_manager.update_bank_account(dto.id, dto)
        else:
            result = await self.app_core.bank_account_manager.create_bank_account(dto)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str, f"Bank Account '{result.value.account_name}' {action_verb_past} successfully (ID: {result.value.id})."))
            self.bank_account_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to save bank account:\n{', '.join(result.errors)}"))
