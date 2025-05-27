# app/ui/customers/customer_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QCompleter
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, AppBaseModel
from app.models.business.customer import Customer
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class CustomerDialog(QDialog):
    customer_saved = Signal(int) # Emits customer ID on successful save

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 customer_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.customer_id = customer_id
        self.loaded_customer_data: Optional[Customer] = None # Store loaded ORM for pre-filling

        self._currencies_cache: List[Currency] = []
        self._receivables_accounts_cache: List[Account] = []
        
        self.setWindowTitle("Edit Customer" if self.customer_id else "Add New Customer")
        self.setMinimumWidth(550) # Adjusted width
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        # Load combo box data asynchronously
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))

        if self.customer_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_customer_details()))


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Basic Info
        self.customer_code_edit = QLineEdit(); form_layout.addRow("Customer Code*:", self.customer_code_edit)
        self.name_edit = QLineEdit(); form_layout.addRow("Customer Name*:", self.name_edit)
        self.legal_name_edit = QLineEdit(); form_layout.addRow("Legal Name:", self.legal_name_edit)
        self.uen_no_edit = QLineEdit(); form_layout.addRow("UEN No.:", self.uen_no_edit)
        
        gst_layout = QHBoxLayout()
        self.gst_registered_check = QCheckBox("GST Registered"); gst_layout.addWidget(self.gst_registered_check)
        self.gst_no_edit = QLineEdit(); self.gst_no_edit.setPlaceholderText("GST Registration No."); gst_layout.addWidget(self.gst_no_edit)
        form_layout.addRow(gst_layout) # Add layout for GST fields

        # Contact Info
        self.contact_person_edit = QLineEdit(); form_layout.addRow("Contact Person:", self.contact_person_edit)
        self.email_edit = QLineEdit(); self.email_edit.setPlaceholderText("example@domain.com"); form_layout.addRow("Email:", self.email_edit)
        self.phone_edit = QLineEdit(); form_layout.addRow("Phone:", self.phone_edit)

        # Address Info
        self.address_line1_edit = QLineEdit(); form_layout.addRow("Address Line 1:", self.address_line1_edit)
        self.address_line2_edit = QLineEdit(); form_layout.addRow("Address Line 2:", self.address_line2_edit)
        self.postal_code_edit = QLineEdit(); form_layout.addRow("Postal Code:", self.postal_code_edit)
        self.city_edit = QLineEdit(); self.city_edit.setText("Singapore"); form_layout.addRow("City:", self.city_edit)
        self.country_edit = QLineEdit(); self.country_edit.setText("Singapore"); form_layout.addRow("Country:", self.country_edit)
        
        # Financial Info
        self.credit_terms_spin = QSpinBox(); self.credit_terms_spin.setRange(0, 365); self.credit_terms_spin.setValue(30); form_layout.addRow("Credit Terms (Days):", self.credit_terms_spin)
        self.credit_limit_edit = QLineEdit(); self.credit_limit_edit.setPlaceholderText("0.00"); form_layout.addRow("Credit Limit:", self.credit_limit_edit)
        
        self.currency_code_combo = QComboBox()
        self.currency_code_combo.setMinimumWidth(150)
        form_layout.addRow("Default Currency*:", self.currency_code_combo)
        
        self.receivables_account_combo = QComboBox()
        self.receivables_account_combo.setMinimumWidth(250)
        form_layout.addRow("A/R Account:", self.receivables_account_combo)

        # Other Info
        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True); form_layout.addRow(self.is_active_check)
        self.customer_since_date_edit = QDateEdit(QDate.currentDate()); self.customer_since_date_edit.setCalendarPopup(True); self.customer_since_date_edit.setDisplayFormat("dd/MM/yyyy"); form_layout.addRow("Customer Since:", self.customer_since_date_edit)
        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(80); form_layout.addRow("Notes:", self.notes_edit)
        
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_customer)
        self.button_box.rejected.connect(self.reject)
        self.gst_registered_check.stateChanged.connect(lambda state: self.gst_no_edit.setEnabled(state == Qt.CheckState.Checked.value))
        self.gst_no_edit.setEnabled(self.gst_registered_check.isChecked())


    async def _load_combo_data(self):
        """ Load data for Currency and Receivables Account comboboxes. """
        try:
            if self.app_core.currency_manager:
                active_currencies = await self.app_core.currency_manager.get_all_currencies() # Get all, filter active in UI if needed
                self._currencies_cache = [c for c in active_currencies if c.is_active]
            
            if self.app_core.chart_of_accounts_manager:
                # Fetch Asset accounts, ideally filtered for AR control accounts by sub_type or a flag
                ar_accounts = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(account_type="Asset", active_only=True)
                self._receivables_accounts_cache = [acc for acc in ar_accounts if acc.is_active and (acc.is_control_account or not acc.is_bank_account)] # Basic filter
            
            # Serialize data for thread-safe UI update
            currencies_json = json.dumps([{"code": c.code, "name": c.name} for c in self._currencies_cache], default=json_converter)
            accounts_json = json.dumps([{"id": acc.id, "code": acc.code, "name": acc.name} for acc in self._receivables_accounts_cache], default=json_converter)

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, currencies_json), Q_ARG(str, accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for CustomerDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str)
    def _populate_combos_slot(self, currencies_json: str, accounts_json: str):
        try:
            currencies_data = json.loads(currencies_json, object_hook=json_date_hook)
            accounts_data = json.loads(accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing combo JSON data: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing dropdown data.")
            return

        # Populate Currency ComboBox
        self.currency_code_combo.clear()
        for curr in currencies_data: self.currency_code_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        
        # Populate Receivables Account ComboBox
        self.receivables_account_combo.clear()
        self.receivables_account_combo.addItem("None", 0) # Option for no specific AR account
        for acc in accounts_data: self.receivables_account_combo.addItem(f"{acc['code']} - {acc['name']}", acc['id'])
        
        # If editing, try to set current values after combos are populated
        if self.loaded_customer_data:
            self._populate_fields_from_orm(self.loaded_customer_data)


    async def _load_existing_customer_details(self):
        if not self.customer_id or not self.app_core.customer_manager: return
        self.loaded_customer_data = await self.app_core.customer_manager.get_customer_for_dialog(self.customer_id)
        if self.loaded_customer_data:
            # Data passed via QMetaObject needs to be simple types or JSON serializable
            customer_dict = {col.name: getattr(self.loaded_customer_data, col.name) for col in Customer.__table__.columns}
            # Convert Decimal and date/datetime to string for JSON
            customer_json_str = json.dumps(customer_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, customer_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Customer ID {self.customer_id} not found.")
            self.reject() # Close dialog if customer not found

    @Slot(str)
    def _populate_fields_slot(self, customer_json_str: str):
        try:
            customer_data = json.loads(customer_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse customer data for editing."); return
        
        self._populate_fields_from_dict(customer_data)


    def _populate_fields_from_orm(self, customer_orm: Customer): # Primarily for setting combos after they are loaded
        currency_idx = self.currency_code_combo.findData(customer_orm.currency_code)
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        else: self.app_core.logger.warning(f"Loaded customer currency '{customer_orm.currency_code}' not found in active currencies combo.")

        ar_acc_idx = self.receivables_account_combo.findData(customer_orm.receivables_account_id or 0)
        if ar_acc_idx != -1: self.receivables_account_combo.setCurrentIndex(ar_acc_idx)
        elif customer_orm.receivables_account_id:
             self.app_core.logger.warning(f"Loaded customer A/R account ID '{customer_orm.receivables_account_id}' not found in combo.")


    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.customer_code_edit.setText(data.get("customer_code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.legal_name_edit.setText(data.get("legal_name", "") or "")
        self.uen_no_edit.setText(data.get("uen_no", "") or "")
        self.gst_registered_check.setChecked(data.get("gst_registered", False))
        self.gst_no_edit.setText(data.get("gst_no", "") or "")
        self.gst_no_edit.setEnabled(data.get("gst_registered", False))
        self.contact_person_edit.setText(data.get("contact_person", "") or "")
        self.email_edit.setText(data.get("email", "") or "")
        self.phone_edit.setText(data.get("phone", "") or "")
        self.address_line1_edit.setText(data.get("address_line1", "") or "")
        self.address_line2_edit.setText(data.get("address_line2", "") or "")
        self.postal_code_edit.setText(data.get("postal_code", "") or "")
        self.city_edit.setText(data.get("city", "") or "Singapore")
        self.country_edit.setText(data.get("country", "") or "Singapore")
        self.credit_terms_spin.setValue(data.get("credit_terms", 30))
        cl_val = data.get("credit_limit")
        self.credit_limit_edit.setText(f"{Decimal(str(cl_val)):.2f}" if cl_val is not None else "")
        
        # Set comboboxes - ensure they are populated first
        currency_idx = self.currency_code_combo.findData(data.get("currency_code", "SGD"))
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        
        ar_acc_id = data.get("receivables_account_id")
        ar_acc_idx = self.receivables_account_combo.findData(ar_acc_id if ar_acc_id is not None else 0)
        if ar_acc_idx != -1: self.receivables_account_combo.setCurrentIndex(ar_acc_idx)

        self.is_active_check.setChecked(data.get("is_active", True))
        cs_date = data.get("customer_since")
        self.customer_since_date_edit.setDate(QDate(cs_date) if cs_date else QDate.currentDate())
        self.notes_edit.setText(data.get("notes", "") or "")


    @Slot()
    def on_save_customer(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        try:
            credit_limit_val_str = self.credit_limit_edit.text().strip()
            credit_limit_decimal = Decimal(credit_limit_val_str) if credit_limit_val_str else None
        except InvalidOperation:
            QMessageBox.warning(self, "Input Error", "Invalid Credit Limit format. Please enter a valid number or leave blank."); return

        receivables_acc_id_data = self.receivables_account_combo.currentData()
        receivables_acc_id = int(receivables_acc_id_data) if receivables_acc_id_data and int(receivables_acc_id_data) != 0 else None
        
        customer_since_py_date = self.customer_since_date_edit.date().toPython()

        # Common data dictionary for DTOs
        data_dict = {
            "customer_code": self.customer_code_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "legal_name": self.legal_name_edit.text().strip() or None,
            "uen_no": self.uen_no_edit.text().strip() or None,
            "gst_registered": self.gst_registered_check.isChecked(),
            "gst_no": self.gst_no_edit.text().strip() if self.gst_registered_check.isChecked() else None,
            "contact_person": self.contact_person_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None, # Pydantic will validate EmailStr
            "phone": self.phone_edit.text().strip() or None,
            "address_line1": self.address_line1_edit.text().strip() or None,
            "address_line2": self.address_line2_edit.text().strip() or None,
            "postal_code": self.postal_code_edit.text().strip() or None,
            "city": self.city_edit.text().strip() or None,
            "country": self.country_edit.text().strip() or "Singapore",
            "credit_terms": self.credit_terms_spin.value(),
            "credit_limit": credit_limit_decimal,
            "currency_code": self.currency_code_combo.currentData() or "SGD",
            "is_active": self.is_active_check.isChecked(),
            "customer_since": customer_since_py_date,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "receivables_account_id": receivables_acc_id,
            "user_id": self.current_user_id
        }

        try:
            if self.customer_id: # Update
                dto = CustomerUpdateData(id=self.customer_id, **data_dict) # type: ignore
            else: # Create
                dto = CustomerCreateData(**data_dict) # type: ignore
        except ValueError as pydantic_error: # Pydantic validation error
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
             return

        # Disable save button during operation
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)

        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button else None
        )

    async def _perform_save(self, dto: CustomerCreateData | CustomerUpdateData):
        if not self.app_core.customer_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Customer Manager not available."))
            return

        result: Result[Customer]
        if isinstance(dto, CustomerUpdateData):
            result = await self.app_core.customer_manager.update_customer(dto.id, dto)
        else:
            result = await self.app_core.customer_manager.create_customer(dto)

        if result.is_success and result.value:
            action = "updated" if isinstance(dto, CustomerUpdateData) else "created"
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Customer {action} successfully (ID: {result.value.id})."))
            self.customer_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save customer:\n{', '.join(result.errors)}"))
