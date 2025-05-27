# File: app/ui/vendors/vendor_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox, # Added QDoubleSpinBox
    QCompleter
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import VendorCreateData, VendorUpdateData
from app.models.business.vendor import Vendor
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class VendorDialog(QDialog):
    vendor_saved = Signal(int) # Emits vendor ID on successful save

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 vendor_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.vendor_id = vendor_id
        self.loaded_vendor_data: Optional[Vendor] = None 

        self._currencies_cache: List[Currency] = []
        self._payables_accounts_cache: List[Account] = []
        
        self.setWindowTitle("Edit Vendor" if self.vendor_id else "Add New Vendor")
        self.setMinimumWidth(600) # Adjusted width for more fields
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        if self.vendor_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_vendor_details()))

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Basic Info
        self.vendor_code_edit = QLineEdit(); form_layout.addRow("Vendor Code*:", self.vendor_code_edit)
        self.name_edit = QLineEdit(); form_layout.addRow("Vendor Name*:", self.name_edit)
        self.legal_name_edit = QLineEdit(); form_layout.addRow("Legal Name:", self.legal_name_edit)
        self.uen_no_edit = QLineEdit(); form_layout.addRow("UEN No.:", self.uen_no_edit)
        
        gst_layout = QHBoxLayout()
        self.gst_registered_check = QCheckBox("GST Registered"); gst_layout.addWidget(self.gst_registered_check)
        self.gst_no_edit = QLineEdit(); self.gst_no_edit.setPlaceholderText("GST Registration No."); gst_layout.addWidget(self.gst_no_edit)
        form_layout.addRow(gst_layout)

        wht_layout = QHBoxLayout()
        self.wht_applicable_check = QCheckBox("WHT Applicable"); wht_layout.addWidget(self.wht_applicable_check)
        self.wht_rate_spin = QDoubleSpinBox(); 
        self.wht_rate_spin.setDecimals(2); self.wht_rate_spin.setRange(0, 100); self.wht_rate_spin.setSuffix(" %")
        wht_layout.addWidget(self.wht_rate_spin)
        form_layout.addRow(wht_layout)


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
        self.payment_terms_spin = QSpinBox(); self.payment_terms_spin.setRange(0, 365); self.payment_terms_spin.setValue(30); form_layout.addRow("Payment Terms (Days):", self.payment_terms_spin)
        
        self.currency_code_combo = QComboBox(); self.currency_code_combo.setMinimumWidth(150)
        form_layout.addRow("Default Currency*:", self.currency_code_combo)
        
        self.payables_account_combo = QComboBox(); self.payables_account_combo.setMinimumWidth(250)
        form_layout.addRow("A/P Account:", self.payables_account_combo)

        # Bank Details
        bank_details_group = QGroupBox("Vendor Bank Details")
        bank_form_layout = QFormLayout(bank_details_group)
        self.bank_account_name_edit = QLineEdit(); bank_form_layout.addRow("Account Name:", self.bank_account_name_edit)
        self.bank_account_number_edit = QLineEdit(); bank_form_layout.addRow("Account Number:", self.bank_account_number_edit)
        self.bank_name_edit = QLineEdit(); bank_form_layout.addRow("Bank Name:", self.bank_name_edit)
        self.bank_branch_edit = QLineEdit(); bank_form_layout.addRow("Bank Branch:", self.bank_branch_edit)
        self.bank_swift_code_edit = QLineEdit(); bank_form_layout.addRow("SWIFT Code:", self.bank_swift_code_edit)
        form_layout.addRow(bank_details_group)


        # Other Info
        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True); form_layout.addRow(self.is_active_check)
        self.vendor_since_date_edit = QDateEdit(QDate.currentDate()); self.vendor_since_date_edit.setCalendarPopup(True); self.vendor_since_date_edit.setDisplayFormat("dd/MM/yyyy"); form_layout.addRow("Vendor Since:", self.vendor_since_date_edit)
        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(80); form_layout.addRow("Notes:", self.notes_edit)
        
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_vendor)
        self.button_box.rejected.connect(self.reject)
        self.gst_registered_check.stateChanged.connect(lambda state: self.gst_no_edit.setEnabled(state == Qt.CheckState.Checked.value))
        self.gst_no_edit.setEnabled(self.gst_registered_check.isChecked())
        self.wht_applicable_check.stateChanged.connect(lambda state: self.wht_rate_spin.setEnabled(state == Qt.CheckState.Checked.value))
        self.wht_rate_spin.setEnabled(self.wht_applicable_check.isChecked())


    async def _load_combo_data(self):
        try:
            if self.app_core.currency_manager:
                active_currencies = await self.app_core.currency_manager.get_all_currencies()
                self._currencies_cache = [c for c in active_currencies if c.is_active]
            
            if self.app_core.chart_of_accounts_manager:
                # Fetch Liability accounts, ideally filtered for AP control accounts
                ap_accounts = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(account_type="Liability", active_only=True)
                self._payables_accounts_cache = [acc for acc in ap_accounts if acc.is_active and (acc.is_control_account or "Payable" in acc.name)] # Basic filter
            
            currencies_json = json.dumps([{"code": c.code, "name": c.name} for c in self._currencies_cache], default=json_converter)
            accounts_json = json.dumps([{"id": acc.id, "code": acc.code, "name": acc.name} for acc in self._payables_accounts_cache], default=json_converter)

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, currencies_json), Q_ARG(str, accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for VendorDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str)
    def _populate_combos_slot(self, currencies_json: str, accounts_json: str):
        try:
            currencies_data = json.loads(currencies_json, object_hook=json_date_hook)
            accounts_data = json.loads(accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing combo JSON data for VendorDialog: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing dropdown data.")
            return

        self.currency_code_combo.clear()
        for curr in currencies_data: self.currency_code_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        
        self.payables_account_combo.clear()
        self.payables_account_combo.addItem("None", 0) 
        for acc in accounts_data: self.payables_account_combo.addItem(f"{acc['code']} - {acc['name']}", acc['id'])
        
        if self.loaded_vendor_data: # If editing, set current values after combos are populated
            self._populate_fields_from_orm(self.loaded_vendor_data)


    async def _load_existing_vendor_details(self):
        if not self.vendor_id or not self.app_core.vendor_manager: return # Changed from customer_manager
        self.loaded_vendor_data = await self.app_core.vendor_manager.get_vendor_for_dialog(self.vendor_id) # Changed
        if self.loaded_vendor_data:
            vendor_dict = {col.name: getattr(self.loaded_vendor_data, col.name) for col in Vendor.__table__.columns}
            vendor_json_str = json.dumps(vendor_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, vendor_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Vendor ID {self.vendor_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, vendor_json_str: str):
        try:
            vendor_data = json.loads(vendor_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse vendor data for editing."); return
        self._populate_fields_from_dict(vendor_data)

    def _populate_fields_from_orm(self, vendor_orm: Vendor): # Called after combos populated, if editing
        currency_idx = self.currency_code_combo.findData(vendor_orm.currency_code)
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        else: self.app_core.logger.warning(f"Loaded vendor currency '{vendor_orm.currency_code}' not found in active currencies combo.")

        ap_acc_idx = self.payables_account_combo.findData(vendor_orm.payables_account_id or 0)
        if ap_acc_idx != -1: self.payables_account_combo.setCurrentIndex(ap_acc_idx)
        elif vendor_orm.payables_account_id:
             self.app_core.logger.warning(f"Loaded vendor A/P account ID '{vendor_orm.payables_account_id}' not found in combo.")

    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.vendor_code_edit.setText(data.get("vendor_code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.legal_name_edit.setText(data.get("legal_name", "") or "")
        self.uen_no_edit.setText(data.get("uen_no", "") or "")
        self.gst_registered_check.setChecked(data.get("gst_registered", False))
        self.gst_no_edit.setText(data.get("gst_no", "") or ""); self.gst_no_edit.setEnabled(data.get("gst_registered", False))
        self.wht_applicable_check.setChecked(data.get("withholding_tax_applicable", False))
        self.wht_rate_spin.setValue(float(data.get("withholding_tax_rate", 0.0) or 0.0))
        self.wht_rate_spin.setEnabled(data.get("withholding_tax_applicable", False))
        self.contact_person_edit.setText(data.get("contact_person", "") or "")
        self.email_edit.setText(data.get("email", "") or "")
        self.phone_edit.setText(data.get("phone", "") or "")
        self.address_line1_edit.setText(data.get("address_line1", "") or "")
        self.address_line2_edit.setText(data.get("address_line2", "") or "")
        self.postal_code_edit.setText(data.get("postal_code", "") or "")
        self.city_edit.setText(data.get("city", "") or "Singapore")
        self.country_edit.setText(data.get("country", "") or "Singapore")
        self.payment_terms_spin.setValue(data.get("payment_terms", 30))
        
        currency_idx = self.currency_code_combo.findData(data.get("currency_code", "SGD"))
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        
        ap_acc_id = data.get("payables_account_id")
        ap_acc_idx = self.payables_account_combo.findData(ap_acc_id if ap_acc_id is not None else 0)
        if ap_acc_idx != -1: self.payables_account_combo.setCurrentIndex(ap_acc_idx)

        self.bank_account_name_edit.setText(data.get("bank_account_name","") or "")
        self.bank_account_number_edit.setText(data.get("bank_account_number","") or "")
        self.bank_name_edit.setText(data.get("bank_name","") or "")
        self.bank_branch_edit.setText(data.get("bank_branch","") or "")
        self.bank_swift_code_edit.setText(data.get("bank_swift_code","") or "")

        self.is_active_check.setChecked(data.get("is_active", True))
        vs_date = data.get("vendor_since")
        self.vendor_since_date_edit.setDate(QDate(vs_date) if vs_date else QDate.currentDate())
        self.notes_edit.setText(data.get("notes", "") or "")

    @Slot()
    def on_save_vendor(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        payables_acc_id_data = self.payables_account_combo.currentData()
        payables_acc_id = int(payables_acc_id_data) if payables_acc_id_data and int(payables_acc_id_data) != 0 else None
        
        vendor_since_py_date = self.vendor_since_date_edit.date().toPython()

        data_dict = {
            "vendor_code": self.vendor_code_edit.text().strip(), "name": self.name_edit.text().strip(),
            "legal_name": self.legal_name_edit.text().strip() or None, "uen_no": self.uen_no_edit.text().strip() or None,
            "gst_registered": self.gst_registered_check.isChecked(),
            "gst_no": self.gst_no_edit.text().strip() if self.gst_registered_check.isChecked() else None,
            "withholding_tax_applicable": self.wht_applicable_check.isChecked(),
            "withholding_tax_rate": Decimal(str(self.wht_rate_spin.value())) if self.wht_applicable_check.isChecked() else None,
            "contact_person": self.contact_person_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None, 
            "phone": self.phone_edit.text().strip() or None,
            "address_line1": self.address_line1_edit.text().strip() or None,
            "address_line2": self.address_line2_edit.text().strip() or None,
            "postal_code": self.postal_code_edit.text().strip() or None,
            "city": self.city_edit.text().strip() or None,
            "country": self.country_edit.text().strip() or "Singapore",
            "payment_terms": self.payment_terms_spin.value(),
            "currency_code": self.currency_code_combo.currentData() or "SGD",
            "is_active": self.is_active_check.isChecked(),
            "vendor_since": vendor_since_py_date,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "bank_account_name": self.bank_account_name_edit.text().strip() or None,
            "bank_account_number": self.bank_account_number_edit.text().strip() or None,
            "bank_name": self.bank_name_edit.text().strip() or None,
            "bank_branch": self.bank_branch_edit.text().strip() or None,
            "bank_swift_code": self.bank_swift_code_edit.text().strip() or None,
            "payables_account_id": payables_acc_id,
            "user_id": self.current_user_id
        }

        try:
            if self.vendor_id: dto = VendorUpdateData(id=self.vendor_id, **data_dict) # type: ignore
            else: dto = VendorCreateData(**data_dict) # type: ignore
        except ValueError as pydantic_error: 
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}"); return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button else None)

    async def _perform_save(self, dto: VendorCreateData | VendorUpdateData):
        if not self.app_core.vendor_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Vendor Manager not available."))
            return

        result: Result[Vendor]
        if isinstance(dto, VendorUpdateData): result = await self.app_core.vendor_manager.update_vendor(dto.id, dto)
        else: result = await self.app_core.vendor_manager.create_vendor(dto)

        if result.is_success and result.value:
            action = "updated" if isinstance(dto, VendorUpdateData) else "created"
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Vendor {action} successfully (ID: {result.value.id})."))
            self.vendor_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save vendor:\n{', '.join(result.errors)}"))
