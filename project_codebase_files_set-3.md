# app/ui/vendors/vendor_table_model.py
```py
# File: app/ui/vendors/vendor_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import VendorSummaryData # Using the DTO for type safety

class VendorTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[VendorSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers should match fields in VendorSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Email", "Phone", "Active"]
        self._data: List[VendorSummaryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        vendor_summary: VendorSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(vendor_summary.id)
            if col == 1: return vendor_summary.vendor_code
            if col == 2: return vendor_summary.name
            if col == 3: return str(vendor_summary.email) if vendor_summary.email else ""
            if col == 4: return vendor_summary.phone if vendor_summary.phone else ""
            if col == 5: return "Yes" if vendor_summary.is_active else "No"
            
            header_key = self._headers[col].lower().replace(' ', '_')
            return str(getattr(vendor_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: 
                return vendor_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 5: # Active status
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_vendor_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_vendor_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[VendorSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/vendors/vendor_dialog.py
```py
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

```

# app/ui/vendors/__init__.py
```py
# app/ui/vendors/__init__.py
from .vendors_widget import VendorsWidget # Was previously just a stub, now functional
from .vendor_dialog import VendorDialog
from .vendor_table_model import VendorTableModel

__all__ = [
    "VendorsWidget",
    "VendorDialog",
    "VendorTableModel",
]


```

# app/ui/vendors/vendors_widget.py
```py
# app/ui/vendors/vendors_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox # Added for filtering/search
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.vendors.vendor_table_model import VendorTableModel 
from app.ui.vendors.vendor_dialog import VendorDialog 
from app.utils.pydantic_models import VendorSummaryData 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.vendor import Vendor # For Result type hint from manager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class VendorsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for VendorsWidget.")
        except ImportError:
            self.app_core.logger.info("VendorsWidget: Compiled Qt resources not found. Using direct file paths.")
            # self.icon_path_prefix remains "resources/icons/"

        self._init_ui()
        # Initial load triggered by filter button click to respect default filter settings
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_vendors()))


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        # --- Toolbar ---
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        # --- Filter/Search Area ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter code, name, or email...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger) 
        filter_layout.addWidget(self.search_edit)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger) 
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"),"Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # --- Table View ---
        self.vendors_table = QTableView()
        self.vendors_table.setAlternatingRowColors(True)
        self.vendors_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vendors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vendors_table.horizontalHeader().setStretchLastSection(False) # Changed for better control
        self.vendors_table.doubleClicked.connect(self._on_edit_vendor) # Or view_vendor
        self.vendors_table.setSortingEnabled(True)

        self.table_model = VendorTableModel()
        self.vendors_table.setModel(self.table_model)
        
        # Configure columns after model is set
        header = self.vendors_table.horizontalHeader()
        for i in range(self.table_model.columnCount()): # Default to ResizeToContents
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.vendors_table.setColumnHidden(id_col_idx, True)
        
        if "Name" in self.table_model._headers:
            name_col_model_idx = self.table_model._headers.index("Name")
            # Calculate visible index for "Name" if "ID" is hidden before it
            visible_name_idx = name_col_model_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_model_idx and self.vendors_table.isColumnHidden(self.table_model._headers.index("ID")):
                visible_name_idx -=1
            
            if not self.vendors_table.isColumnHidden(name_col_model_idx):
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        else: 
             # Fallback: if ID is hidden (col 0), then Code (model col 1 -> vis col 0), Name (model col 2 -> vis col 1)
             # Stretch the second visible column which is typically Name.
             if self.table_model.columnCount() > 2 and self.vendors_table.isColumnHidden(0):
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
             elif self.table_model.columnCount() > 1: # If ID is not hidden or not present
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


        self.main_layout.addWidget(self.vendors_table)
        self.setLayout(self.main_layout)

        if self.vendors_table.selectionModel():
            self.vendors_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Vendor Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Vendor", self)
        self.toolbar_add_action.triggered.connect(self._on_add_vendor)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Vendor", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_vendor)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self) # Icon might need specific "activate" variant too
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_vendors()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_vendors()) # Trigger load with cleared filters

    @Slot()
    def _update_action_states(self):
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_vendors(self):
        if not self.app_core.vendor_manager:
            self.app_core.logger.error("VendorManager not available in VendorsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Vendor Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            
            result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(
                active_only=active_only, 
                search_term=search_term,
                page=1, 
                page_size=200 # Load a reasonable number for MVP table, pagination UI later
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load vendors: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading vendors: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            vendor_summaries: List[VendorSummaryData] = [VendorSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(vendor_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse vendor data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid vendor data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_vendor(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a vendor.")
            return
        
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()

    def _get_selected_vendor_id(self) -> Optional[int]:
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        if not selected_rows: # No message if simply no selection for state update
            return None
        if len(selected_rows) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single vendor for this action.")
            return None
        return self.table_model.get_vendor_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_vendor(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            # Message only if action was explicitly triggered and no single item was selected
            if self.sender() == self.toolbar_edit_action : # type: ignore
                 QMessageBox.information(self, "Selection", "Please select a single vendor to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a vendor.")
            return
            
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_view_vendor_double_click(self, index: QModelIndex): # Renamed for clarity
        if not index.isValid(): return
        vendor_id = self.table_model.get_vendor_id_at_row(index.row())
        if vendor_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to view/edit vendor.")
            return
        # For MVP, double-click opens for edit. Can be changed to view-only later.
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single vendor to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change vendor status.")
            return
            
        vendor_status_active = self.table_model.get_vendor_status_at_row(self.vendors_table.currentIndex().row())
        action_verb = "deactivate" if vendor_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this vendor?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.vendor_manager.toggle_vendor_active_status(vendor_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None) # Handle scheduling failure

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule vendor status toggle."); return
        try:
            result: Result[Vendor] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Vendor {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_vendors()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle vendor status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for vendor: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/dashboard/__init__.py
```py
# File: app/ui/dashboard/__init__.py
# (Content as previously generated)
from .dashboard_widget import DashboardWidget

__all__ = ["DashboardWidget"]

```

# app/ui/dashboard/dashboard_widget.py
```py
# app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
    QScrollArea, QFrame, QFormLayout, QDateEdit
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QMargins, QDate
from PySide6.QtGui import QFont, QIcon, QPainter, QColor
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis

from typing import Optional, TYPE_CHECKING, List, Dict 
from decimal import Decimal, InvalidOperation 
import json 
from datetime import date as python_date, datetime, timedelta

from app.utils.pydantic_models import DashboardKPIData
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class DashboardWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None): 
        super().__init__(parent)
        self.app_core = app_core
        self._load_request_count = 0 
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
            
        self._group_colors = [QColor("#4F81BD"), QColor("#C0504D"), QColor("#9BBB59")]

        self._init_ui()
        self.app_core.logger.info("DashboardWidget: Scheduling initial KPI load.")
        QTimer.singleShot(0, self._request_kpi_load)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(QLabel("<b>Dashboard As Of Date:</b>"))
        self.as_of_date_edit = QDateEdit(QDate.currentDate())
        self.as_of_date_edit.setCalendarPopup(True)
        self.as_of_date_edit.setDisplayFormat("dd/MM/yyyy")
        top_controls_layout.addWidget(self.as_of_date_edit)
        top_controls_layout.addStretch()
        self.refresh_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh KPIs")
        self.refresh_button.clicked.connect(self._request_kpi_load)
        top_controls_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(top_controls_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(scroll_area)

        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        kpi_group = QGroupBox("Key Performance Indicators")
        container_layout.addWidget(kpi_group)
        
        self.kpi_layout = QGridLayout(kpi_group) 
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setColumnStretch(1, 1) 
        self.kpi_layout.setColumnStretch(3, 1) 
        self.kpi_layout.setColumnMinimumWidth(0, 220) 
        self.kpi_layout.setColumnMinimumWidth(2, 220) 

        def add_kpi_row(layout: QGridLayout, row: int, col_offset: int, title: str) -> QLabel:
            title_label = QLabel(title)
            title_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            value_label = QLabel("Loading...")
            value_label.setFont(QFont(self.font().family(), 11)) 
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(title_label, row, col_offset)
            layout.addWidget(value_label, row, col_offset + 1)
            return value_label

        current_row = 0
        self.period_label = QLabel("Period: Loading...")
        self.period_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.base_currency_label, current_row, 2, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        current_row += 1
        
        self.revenue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Revenue (YTD):")
        self.cash_balance_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Cash Balance:")
        current_row += 1
        self.expenses_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Expenses (YTD):")
        self.current_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Ratio:") 
        current_row += 1
        self.net_profit_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Net Profit / (Loss) (YTD):")
        self.quick_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Quick Ratio (Acid Test):")
        current_row += 1
        
        self.debt_to_equity_label = add_kpi_row(self.kpi_layout, current_row, 2, "Debt-to-Equity Ratio:")
        current_row += 1

        self.kpi_layout.addWidget(QLabel("---"), current_row, 0, 1, 4) 
        current_row += 1
        self.ar_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Outstanding AR:")
        self.ap_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total Outstanding AP:")
        current_row += 1
        self.ar_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total AR Overdue:")
        self.ap_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total AP Overdue:")
        current_row += 1
        
        self.ar_aging_chart_view = self._create_aging_chart_view("AR Aging Summary")
        self.kpi_layout.addWidget(self.ar_aging_chart_view, current_row, 0, 1, 2) 

        self.ap_aging_chart_view = self._create_aging_chart_view("AP Aging Summary")
        self.kpi_layout.addWidget(self.ap_aging_chart_view, current_row, 2, 1, 2) 
        
        container_layout.addStretch() 

    def _create_aging_chart_view(self, title: str) -> QChartView:
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(False)
        chart.setMargins(QMargins(0,0,0,0))
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(250)
        return chart_view

    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None: return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        try:
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)" 
            return f"{prefix}{value:,.2f}"
        except (TypeError, InvalidOperation): return f"{prefix}Error"

    def _format_ratio_for_display(self, value: Optional[Decimal]) -> str:
        if value is None: return "N/A"
        try:
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)" 
            return f"{value:.2f} : 1"
        except (TypeError, InvalidOperation): return "Error"

    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count}). Setting labels to 'Loading...'.")
        
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
            self.ar_overdue_value_label, self.ap_overdue_value_label,
            self.current_ratio_label, self.quick_ratio_label, self.debt_to_equity_label
        ]
        for label in labels_to_reset:
            if hasattr(self, 'app_core') and self.app_core and hasattr(self.app_core, 'logger'): 
                 self.app_core.logger.debug(f"DashboardWidget: Resetting label to 'Loading...'")
            label.setText("Loading...")
        
        self.ar_aging_chart_view.chart().removeAllSeries()
        self.ap_aging_chart_view.chart().removeAllSeries()

        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...")

        as_of_date = self.as_of_date_edit.date().toPython()
        future = schedule_task_from_qt(self._fetch_kpis_data(as_of_date))
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
        else:
            self.app_core.logger.error("DashboardWidget: Failed to schedule _fetch_kpis_data task.")
            self.refresh_button.setEnabled(True) 

    async def _fetch_kpis_data(self, as_of_date: python_date):
        self.app_core.logger.info("DashboardWidget: _fetch_kpis_data started.")
        kpi_data_result: Optional[DashboardKPIData] = None
        json_payload: Optional[str] = None
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("DashboardWidget: Dashboard Manager not available in _fetch_kpis_data.")
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis(as_of_date=as_of_date)
                if kpi_data_result:
                    self.app_core.logger.info(f"DashboardWidget: Fetched KPI data: Period='{kpi_data_result.kpi_period_description}', Revenue='{kpi_data_result.total_revenue_ytd}'")
                    json_payload = kpi_data_result.model_dump_json()
                else:
                    self.app_core.logger.warning("DashboardWidget: DashboardManager.get_dashboard_kpis returned None.")
        except Exception as e:
            self.app_core.logger.error(f"DashboardWidget: Exception in _fetch_kpis_data during manager call: {e}", exc_info=True)
        
        self.app_core.logger.info(f"DashboardWidget: Queuing _update_kpi_display_slot with payload: {'JSON string' if json_payload else 'None'}")
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_payload if json_payload is not None else ""))

    @Slot(str)
    def _update_kpi_display_slot(self, kpi_data_json_str: str):
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Received JSON string length: {len(kpi_data_json_str)}")
        self.refresh_button.setEnabled(True)
        
        kpi_data_dto: Optional[DashboardKPIData] = None
        if kpi_data_json_str:
            try:
                kpi_data_dto = DashboardKPIData.model_validate_json(kpi_data_json_str)
                self.app_core.logger.info(f"DashboardWidget: Successfully deserialized KPI JSON to DTO.")
            except Exception as e:
                self.app_core.logger.error(f"DashboardWidget: Error deserializing/validating KPI JSON: '{kpi_data_json_str[:100]}...' - Error: {e}", exc_info=True)
        
        if kpi_data_dto:
            self.app_core.logger.info(f"DashboardWidget: Updating UI with KPI Data: Period='{kpi_data_dto.kpi_period_description}'")
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
            self.ar_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ar_overdue, bc_symbol)) 
            self.ap_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ap_overdue, bc_symbol)) 

            self._update_aging_chart(self.ar_aging_chart_view, kpi_data_dto, "ar")
            self.ap_aging_chart_view.chart().setTitleFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            self._update_aging_chart(self.ap_aging_chart_view, kpi_data_dto, "ap")
            
            self.current_ratio_label.setText(self._format_ratio_for_display(kpi_data_dto.current_ratio))
            self.quick_ratio_label.setText(self._format_ratio_for_display(kpi_data_dto.quick_ratio))
            self.debt_to_equity_label.setText(self._format_ratio_for_display(kpi_data_dto.debt_to_equity_ratio))

            self.app_core.logger.info("DashboardWidget: UI labels and charts updated with KPI data.")
        else:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with no valid DTO. Setting error text.")
            error_text = "N/A - Data unavailable"
            for label in [self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
                          self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
                          self.ar_overdue_value_label, self.ap_overdue_value_label,
                          self.current_ratio_label, self.quick_ratio_label, self.debt_to_equity_label]:
                label.setText(error_text)
            self.ar_aging_chart_view.chart().removeAllSeries()
            self.ap_aging_chart_view.chart().removeAllSeries()
            self.period_label.setText("Period: N/A")
            self.base_currency_label.setText("Currency: N/A")
            if kpi_data_json_str: 
                 QMessageBox.warning(self, "Dashboard Data Error", "Could not process Key Performance Indicators data.")

    def _update_aging_chart(self, chart_view: QChartView, kpi_data: DashboardKPIData, data_prefix: str):
        chart = chart_view.chart()
        chart.removeAllSeries()
        for axis in chart.axes(): chart.removeAxis(axis)

        bar_set = QBarSet("Amount")
        bar_set.setColor(QColor("#4F81BD"))
        
        aging_data = [
            kpi_data.ar_aging_current if data_prefix == "ar" else kpi_data.ap_aging_current,
            kpi_data.ar_aging_1_30 if data_prefix == "ar" else kpi_data.ap_aging_1_30,
            kpi_data.ar_aging_31_60 if data_prefix == "ar" else kpi_data.ap_aging_31_60,
            kpi_data.ar_aging_61_90 if data_prefix == "ar" else kpi_data.ap_aging_61_90,
            kpi_data.ar_aging_91_plus if data_prefix == "ar" else kpi_data.ap_aging_91_plus
        ]
        
        max_val = 0
        for val in aging_data:
            float_val = float(val)
            bar_set.append(float_val)
            if float_val > max_val: max_val = float_val

        series = QBarSeries()
        series.append(bar_set)
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        chart.addSeries(series)

        categories = ["Current", "1-30", "31-60", "61-90", "91+"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%'i")
        axis_y.setRange(0, max_val * 1.15 if max_val > 0 else 100)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

```

# app/ui/payments/__init__.py
```py
# File: app/ui/payments/__init__.py
# This directory will house UI components for the Payments module.
from .payment_table_model import PaymentTableModel
from .payment_dialog import PaymentDialog 
from .payments_widget import PaymentsWidget # New Import

__all__ = [
    "PaymentTableModel",
    "PaymentDialog", 
    "PaymentsWidget", # New Export
]

```

# app/ui/payments/payments_widget.py
```py
# File: app/ui/payments/payments_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.payments.payment_table_model import PaymentTableModel
from app.ui.payments.payment_dialog import PaymentDialog
from app.utils.pydantic_models import PaymentSummaryData, CustomerSummaryData, VendorSummaryData
from app.common.enums import PaymentStatusEnum, PaymentEntityTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class PaymentsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._customers_cache_for_filter: List[Dict[str, Any]] = []
        self._vendors_cache_for_filter: List[Dict[str, Any]] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_filter_combos()))
        QTimer.singleShot(100, lambda: self.apply_filter_button.click()) # Initial load

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addLayout(self.filter_layout_main) 

        self.payments_table = QTableView()
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.payments_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # self.payments_table.doubleClicked.connect(self._on_view_payment_double_click) # For future view
        self.payments_table.setSortingEnabled(True)

        self.table_model = PaymentTableModel()
        self.payments_table.setModel(self.table_model)
        
        header = self.payments_table.horizontalHeader()
        # Adjust column widths - example
        if "ID" in self.table_model._headers:
            self.payments_table.setColumnHidden(self.table_model._headers.index("ID"), True)
        if "Payment No" in self.table_model._headers:
            header.setSectionResizeMode(self.table_model._headers.index("Payment No"), QHeaderView.ResizeMode.ResizeToContents)
        if "Entity Name" in self.table_model._headers:
             header.setSectionResizeMode(self.table_model._headers.index("Entity Name"), QHeaderView.ResizeMode.Stretch)
        if "Amount" in self.table_model._headers:
             header.setSectionResizeMode(self.table_model._headers.index("Amount"), QHeaderView.ResizeMode.ResizeToContents)

        self.main_layout.addWidget(self.payments_table)
        self.setLayout(self.main_layout)

        if self.payments_table.selectionModel():
            self.payments_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Payments Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_payment_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Payment/Receipt", self)
        self.toolbar_add_payment_action.triggered.connect(self._on_add_payment)
        self.toolbar.addAction(self.toolbar_add_payment_action)

        # Add View, Void actions later
        # self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Payment", self)
        # self.toolbar_view_action.triggered.connect(self._on_view_payment)
        # self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_payments()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout_main = QHBoxLayout()
        
        self.filter_layout_main.addWidget(QLabel("Entity Type:"))
        self.entity_type_filter_combo = QComboBox()
        self.entity_type_filter_combo.addItem("All Entities", None)
        self.entity_type_filter_combo.addItem(PaymentEntityTypeEnum.CUSTOMER.value, PaymentEntityTypeEnum.CUSTOMER)
        self.entity_type_filter_combo.addItem(PaymentEntityTypeEnum.VENDOR.value, PaymentEntityTypeEnum.VENDOR)
        self.entity_type_filter_combo.currentIndexChanged.connect(self._on_entity_type_filter_changed)
        self.filter_layout_main.addWidget(self.entity_type_filter_combo)

        self.entity_filter_label = QLabel("Entity:")
        self.filter_layout_main.addWidget(self.entity_filter_label)
        self.entity_filter_combo = QComboBox(); self.entity_filter_combo.setMinimumWidth(180)
        self.entity_filter_combo.addItem("All", 0)
        self.entity_filter_combo.setEditable(True)
        entity_completer = QCompleter(self); entity_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        entity_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.entity_filter_combo.setCompleter(entity_completer)
        self.filter_layout_main.addWidget(self.entity_filter_combo)

        self.filter_layout_main.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses", None) 
        for status_enum in PaymentStatusEnum: self.status_filter_combo.addItem(status_enum.value, status_enum)
        self.filter_layout_main.addWidget(self.status_filter_combo)

        self.filter_layout_main.addWidget(QLabel("From:"))
        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout_main.addWidget(self.start_date_filter_edit)

        self.filter_layout_main.addWidget(QLabel("To:"))
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout_main.addWidget(self.end_date_filter_edit)

        self.apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply")
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_payments()))
        self.filter_layout_main.addWidget(self.apply_filter_button)
        
        self.clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        self.filter_layout_main.addWidget(self.clear_filter_button)
        self.filter_layout_main.addStretch()

    async def _load_filter_combos(self):
        # Load customers and vendors for the entity filter combo
        if self.app_core.customer_manager:
            cust_res = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1)
            if cust_res.is_success and cust_res.value:
                self._customers_cache_for_filter = [c.model_dump() for c in cust_result.value] if cust_result.is_success and cust_result.value else []
        if self.app_core.vendor_manager:
            vend_res = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1)
            if vend_res.is_success and vend_res.value:
                self._vendors_cache_for_filter = [v.model_dump() for v in vend_result.value] if vend_result.is_success and vend_result.value else []
        
        # Initial population based on "All Entities"
        self._on_entity_type_filter_changed()


    @Slot()
    def _on_entity_type_filter_changed(self):
        self.entity_filter_combo.clear()
        self.entity_filter_combo.addItem("All", 0)
        entity_type_enum = self.entity_type_filter_combo.currentData()
        
        cache_to_use: List[Dict[str, Any]] = []
        code_field = "customer_code"

        if entity_type_enum == PaymentEntityTypeEnum.CUSTOMER:
            cache_to_use = self._customers_cache_for_filter
            code_field = "customer_code"
            self.entity_filter_label.setText("Customer:")
        elif entity_type_enum == PaymentEntityTypeEnum.VENDOR:
            cache_to_use = self._vendors_cache_for_filter
            code_field = "vendor_code"
            self.entity_filter_label.setText("Vendor:")
        else: # All Entities
            self.entity_filter_label.setText("Entity:")
            # Optionally, could add all customers then all vendors to the list
            # For now, if "All Entities" is selected, the entity_filter_combo can remain "All"
            # and the manager will not filter by specific entity_id.
            pass
        
        for entity in cache_to_use:
            self.entity_filter_combo.addItem(f"{entity.get(code_field, '')} - {entity.get('name', '')}", entity.get('id'))
        
        if isinstance(self.entity_filter_combo.completer(), QCompleter):
            self.entity_filter_combo.completer().setModel(self.entity_filter_combo.model())
        
        # Trigger a refresh if entity type changes
        self.toolbar_refresh_action.trigger()


    @Slot()
    def _clear_filters_and_load(self):
        self.entity_type_filter_combo.setCurrentIndex(0) 
        # _on_entity_type_filter_changed will clear entity_filter_combo and trigger refresh
        self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        # schedule_task_from_qt(self._load_payments()) # Already triggered by combo changes

    @Slot()
    def _update_action_states(self):
        # For now, only Add action is primary. View/Void can be added later.
        self.toolbar_add_payment_action.setEnabled(True) 

    async def _load_payments(self):
        if not self.app_core.payment_manager:
            self.app_core.logger.error("PaymentManager not available."); return
        try:
            entity_type_filter = self.entity_type_filter_combo.currentData()
            entity_id_filter_data = self.entity_filter_combo.currentData()
            entity_id_filter = int(entity_id_filter_data) if entity_id_filter_data and entity_id_filter_data != 0 else None
            
            status_filter = self.status_filter_combo.currentData()
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()

            result: Result[List[PaymentSummaryData]] = await self.app_core.payment_manager.get_payments_for_listing(
                entity_type=entity_type_filter, entity_id=entity_id_filter,
                status=status_filter, start_date=start_date, end_date=end_date,
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump(mode='json') for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load payments: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading payments: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            summaries = [PaymentSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate payment data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_payment(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        # Determine if a specific entity type or entity is pre-selected from filters
        preselected_entity_type = self.entity_type_filter_combo.currentData()
        preselected_entity_id = self.entity_filter_combo.currentData()
        if preselected_entity_id == 0: preselected_entity_id = None # Treat "All" as no preselection

        dialog = PaymentDialog(self.app_core, self.app_core.current_user.id, 
                               # Pass preselected_entity_type and _id to dialog if needed for defaulting
                               # For now, PaymentDialog manages its own entity selection.
                               parent=self)
        dialog.payment_saved.connect(lambda _id: schedule_task_from_qt(self._load_payments()))
        dialog.exec()

```

# app/ui/payments/payment_dialog.py
```py
# app/ui/payments/payment_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QDateEdit, QComboBox, QTextEdit, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QLabel, 
    QFrame, QCompleter, QCheckBox, QApplication, QAbstractSpinBox
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG, QModelIndex, QAbstractItemModel 
from PySide6.QtGui import QIcon, QColor
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union, cast

import json
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import (
    PaymentCreateData, PaymentAllocationBaseData, 
    CustomerSummaryData, VendorSummaryData, BankAccountSummaryData,
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData 
)
from app.models.business.payment import Payment, PaymentAllocation # Corrected import
from app.common.enums import (
    PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, 
    PaymentAllocationDocTypeEnum, InvoiceStatusEnum, PaymentStatusEnum
)
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook
from app.ui.sales_invoices.sales_invoice_dialog import LineItemNumericDelegate 


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class AllocationAmountDelegate(LineItemNumericDelegate):
    def __init__(self, parent_dialog: "PaymentDialog"):
        super().__init__(decimals=2, allow_negative=False, parent=parent_dialog)
        self.parent_dialog = parent_dialog

    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractItemModel, index: QModelIndex): # type: ignore
        super().setModelData(editor, model, index)
        self.parent_dialog._update_allocation_totals_and_checkbox(index.row())


class PaymentDialog(QDialog):
    payment_saved = Signal(int) 

    ALLOC_COL_SELECT = 0
    ALLOC_COL_DOC_TYPE = 1
    ALLOC_COL_DOC_NO = 2
    ALLOC_COL_DOC_DATE = 3
    ALLOC_COL_DOC_TOTAL = 4
    ALLOC_COL_OUTSTANDING = 5
    ALLOC_COL_TO_ALLOCATE = 6

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 payment_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.payment_id = payment_id 
        self.loaded_payment_data: Optional[Payment] = None 
        self.view_only_mode = False 

        self._customers_cache: List[Dict[str, Any]] = []
        self._vendors_cache: List[Dict[str, Any]] = []
        self._bank_accounts_cache: List[Dict[str, Any]] = []
        self._currencies_cache: List[Dict[str, Any]] = []
        self._allocatable_invoices_cache: List[Dict[str, Any]] = [] 
        self._base_currency: str = "SGD"
        self._in_data_load: bool = False 

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(950, 800) 
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.payment_id:
            QTimer.singleShot(100, lambda: schedule_task_from_qt(self._load_existing_payment_data()))
        else: 
            self._update_dynamic_fields()
            self._update_allocation_totals() 

    def _get_window_title(self) -> str:
        pay_no_str = ""
        if self.loaded_payment_data and self.loaded_payment_data.payment_no: 
            pay_no_str = f" ({self.loaded_payment_data.payment_no})"
        
        if self.view_only_mode: return f"View Payment{pay_no_str}"
        if self.payment_id: return f"Edit Payment{pay_no_str}" 
        return "New Payment / Receipt"

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        header_form = QFormLayout()
        header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        header_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        entity_type_layout = QHBoxLayout()
        self.payment_type_combo = QComboBox()
        self.payment_type_combo.addItem(PaymentTypeEnum.CUSTOMER_PAYMENT.value, PaymentTypeEnum.CUSTOMER_PAYMENT)
        self.payment_type_combo.addItem(PaymentTypeEnum.VENDOR_PAYMENT.value, PaymentTypeEnum.VENDOR_PAYMENT)
        entity_type_layout.addWidget(QLabel("Payment Type*:"))
        entity_type_layout.addWidget(self.payment_type_combo)
        
        self.entity_label = QLabel("Customer*:") 
        self.entity_combo = QComboBox()
        self.entity_combo.setEditable(True); self.entity_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.entity_combo.setMinimumWidth(250)
        entity_completer = QCompleter(); entity_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        entity_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.entity_combo.setCompleter(entity_completer)
        entity_type_layout.addWidget(self.entity_label); entity_type_layout.addWidget(self.entity_combo)
        entity_type_layout.addStretch()
        header_form.addRow(entity_type_layout)

        self.payment_date_edit = QDateEdit(QDate.currentDate())
        self.payment_date_edit.setCalendarPopup(True); self.payment_date_edit.setDisplayFormat("dd/MM/yyyy")
        header_form.addRow("Payment Date*:", self.payment_date_edit)

        self.payment_method_combo = QComboBox()
        for pm_enum in PaymentMethodEnum: self.payment_method_combo.addItem(pm_enum.value, pm_enum)
        header_form.addRow("Payment Method*:", self.payment_method_combo)

        self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250)
        header_form.addRow("Bank Account:", self.bank_account_combo)

        self.currency_combo = QComboBox()
        self.exchange_rate_spin = QDoubleSpinBox()
        self.exchange_rate_spin.setDecimals(6); self.exchange_rate_spin.setRange(0.000001, 999999.0); self.exchange_rate_spin.setValue(1.0)
        currency_layout = QHBoxLayout(); currency_layout.addWidget(self.currency_combo); currency_layout.addWidget(QLabel("Exch. Rate:")); currency_layout.addWidget(self.exchange_rate_spin)
        header_form.addRow("Currency*:", currency_layout)

        self.payment_amount_edit = QDoubleSpinBox()
        self.payment_amount_edit.setDecimals(2); self.payment_amount_edit.setRange(0.01, 999999999.99)
        self.payment_amount_edit.setGroupSeparatorShown(True)
        header_form.addRow("Payment Amount*:", self.payment_amount_edit)

        self.reference_edit = QLineEdit(); self.reference_edit.setPlaceholderText("e.g., Transaction ID, Deposit Slip No.")
        header_form.addRow("Reference:", self.reference_edit)
        
        self.cheque_no_edit = QLineEdit(); self.cheque_no_edit.setPlaceholderText("Cheque Number if applicable")
        self.cheque_no_label = QLabel("Cheque No.:")
        header_form.addRow(self.cheque_no_label, self.cheque_no_edit)

        self.description_edit = QTextEdit(); self.description_edit.setFixedHeight(60)
        header_form.addRow("Description/Notes:", self.description_edit)
        main_layout.addLayout(header_form)
        main_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))

        alloc_group = QGroupBox("Invoice Allocations")
        alloc_main_layout = QVBoxLayout(alloc_group)
        self.allocations_table = QTableWidget()
        self.allocations_table.setColumnCount(7)
        self.allocations_table.setHorizontalHeaderLabels([
            "Apply", "Doc Type", "Doc No.", "Doc Date", 
            "Doc Total", "Outstanding", "Allocate Amt"
        ])
        self._configure_allocations_table()
        alloc_main_layout.addWidget(self.allocations_table)
        
        alloc_totals_layout = QHBoxLayout()
        self.total_allocated_label = QLabel("Total Allocated: 0.00")
        self.unallocated_amount_label = QLabel("Unallocated: 0.00")
        font_bold = QFont(); font_bold.setBold(True)
        self.total_allocated_label.setFont(font_bold)
        self.unallocated_amount_label.setFont(font_bold)
        alloc_totals_layout.addStretch(); alloc_totals_layout.addWidget(self.total_allocated_label)
        alloc_totals_layout.addWidget(QLabel(" | ")); alloc_totals_layout.addWidget(self.unallocated_amount_label)
        alloc_main_layout.addLayout(alloc_totals_layout)
        main_layout.addWidget(alloc_group)

        self.button_box = QDialogButtonBox()
        self.save_button = self.button_box.addButton("Save Payment", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _configure_allocations_table(self):
        header = self.allocations_table.horizontalHeader()
        self.allocations_table.setColumnWidth(self.ALLOC_COL_SELECT, 50)
        header.setSectionResizeMode(self.ALLOC_COL_SELECT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.ALLOC_COL_DOC_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.ALLOC_COL_DOC_NO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.ALLOC_COL_DOC_DATE, QHeaderView.ResizeMode.ResizeToContents)
        for col in [self.ALLOC_COL_DOC_TOTAL, self.ALLOC_COL_OUTSTANDING, self.ALLOC_COL_TO_ALLOCATE]:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        
        self.allocations_table.setItemDelegateForColumn(self.ALLOC_COL_TO_ALLOCATE, AllocationAmountDelegate(self))

    def _connect_signals(self):
        self.payment_type_combo.currentDataChanged.connect(self._on_payment_type_changed)
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        self.payment_method_combo.currentDataChanged.connect(self._update_dynamic_fields)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.payment_amount_edit.valueChanged.connect(self._update_allocation_totals)
        
        self.save_button.clicked.connect(self.on_save_payment)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button: cancel_button.clicked.connect(self.reject)

    async def _load_initial_combo_data(self):
        try:
            cs_svc = self.app_core.company_settings_service
            if cs_svc: settings = await cs_svc.get_company_settings(); self._base_currency = settings.base_currency if settings else "SGD"
            if self.app_core.currency_manager:
                curr_orms = await self.app_core.currency_manager.get_all_active_currencies()
                self._currencies_cache = [{"code":c.code, "name":c.name} for c in curr_orms]
            if self.app_core.bank_account_manager:
                ba_result = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(active_only=True, page_size=-1)
                if ba_result.is_success and ba_result.value:
                    self._bank_accounts_cache = [ba.model_dump() for ba in ba_result.value]
            QMetaObject.invokeMethod(self, "_populate_static_combos_slot", Qt.ConnectionType.QueuedConnection)
            current_payment_type = self.payment_type_combo.currentData()
            if current_payment_type: self._on_payment_type_changed(current_payment_type)
        except Exception as e: self.app_core.logger.error(f"Error loading initial combo data for PaymentDialog: {e}", exc_info=True); QMessageBox.warning(self, "Data Load Error", f"Could not load initial dropdown data: {str(e)}")

    @Slot()
    def _populate_static_combos_slot(self):
        self._in_data_load = True
        self.currency_combo.clear()
        for curr in self._currencies_cache: self.currency_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        base_curr_idx = self.currency_combo.findData(self._base_currency)
        if base_curr_idx != -1: self.currency_combo.setCurrentIndex(base_curr_idx)
        elif self._currencies_cache : self.currency_combo.setCurrentIndex(0)
        self._on_currency_changed() 
        self.bank_account_combo.clear(); self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        for ba in self._bank_accounts_cache: self.bank_account_combo.addItem(f"{ba['account_name']} ({ba['bank_name']} - {ba['currency_code']})", ba['id'])
        self._update_dynamic_fields()
        self._in_data_load = False
        if self.loaded_payment_data: 
             self._populate_header_fields_from_orm(self.loaded_payment_data)

    @Slot(PaymentTypeEnum)
    def _on_payment_type_changed(self, payment_type: Optional[PaymentTypeEnum]):
        self._in_data_load = True
        self.entity_combo.clear(); self.entity_combo.addItem("-- Select Entity --", 0)
        self._allocatable_invoices_cache = []; self._clear_allocations_table()
        if payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT:
            self.entity_label.setText("Customer*:")
            schedule_task_from_qt(self._load_entities(PaymentEntityTypeEnum.CUSTOMER))
        elif payment_type == PaymentTypeEnum.VENDOR_PAYMENT:
            self.entity_label.setText("Vendor*:")
            schedule_task_from_qt(self._load_entities(PaymentEntityTypeEnum.VENDOR))
        else: self.entity_label.setText("Entity*:"); self.entity_combo.setEnabled(False)
        self._update_dynamic_fields()
        self._in_data_load = False

    async def _load_entities(self, entity_type: PaymentEntityTypeEnum):
        entity_list_json = "[]"; cache_to_update = []
        if entity_type == PaymentEntityTypeEnum.CUSTOMER and self.app_core.customer_manager:
            cust_result: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1) # type: ignore
            if cust_result.is_success and cust_result.value: self._customers_cache = [c.model_dump() for c in cust_result.value]; cache_to_update = self._customers_cache
        elif entity_type == PaymentEntityTypeEnum.VENDOR and self.app_core.vendor_manager:
            vend_result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1) # type: ignore
            if vend_result.is_success and vend_result.value: self._vendors_cache = [v.model_dump() for v in vend_result.value]; cache_to_update = self._vendors_cache
        entity_list_json = json.dumps(cache_to_update, default=json_converter)
        QMetaObject.invokeMethod(self, "_populate_entity_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, entity_list_json), Q_ARG(str, entity_type.value))

    @Slot(str, str)
    def _populate_entity_combo_slot(self, entities_json: str, entity_type_str: str):
        self._in_data_load = True; self.entity_combo.clear(); self.entity_combo.addItem("-- Select Entity --", 0)
        try:
            entities_data = json.loads(entities_json)
            code_field = "customer_code" if entity_type_str == PaymentEntityTypeEnum.CUSTOMER.value else "vendor_code"
            for entity in entities_data: self.entity_combo.addItem(f"{entity[code_field]} - {entity['name']}", entity['id'])
            if isinstance(self.entity_combo.completer(), QCompleter): self.entity_combo.completer().setModel(self.entity_combo.model())
            self.entity_combo.setEnabled(True)
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Error parsing entities JSON for PaymentDialog ({entity_type_str}): {e}"); self.entity_combo.setEnabled(False)
        self._in_data_load = False
        if self.loaded_payment_data: self._populate_header_fields_from_orm(self.loaded_payment_data)

    @Slot()
    def _on_entity_changed(self):
        if self._in_data_load: return
        current_entity_id = self.entity_combo.currentData()
        self._allocatable_invoices_cache = []; self._clear_allocations_table()
        if current_entity_id and current_entity_id != 0:
            entity_type_enum = self.payment_type_combo.currentData()
            cache_to_use = self._customers_cache if entity_type_enum == PaymentTypeEnum.CUSTOMER_PAYMENT else self._vendors_cache
            selected_entity = next((e for e in cache_to_use if e.get("id") == current_entity_id), None)
            if selected_entity and selected_entity.get("currency_code"):
                curr_idx = self.currency_combo.findData(selected_entity["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
            schedule_task_from_qt(self._load_allocatable_documents())
        self._update_allocation_totals()

    @Slot()
    def _update_dynamic_fields(self):
        payment_method = self.payment_method_combo.currentData()
        is_cheque = (payment_method == PaymentMethodEnum.CHECK)
        is_cash = (payment_method == PaymentMethodEnum.CASH)
        self.cheque_no_label.setVisible(is_cheque); self.cheque_no_edit.setVisible(is_cheque)
        self.bank_account_combo.setEnabled(not is_cash and not self.view_only_mode)
        if is_cash: self.bank_account_combo.setCurrentIndex(0) 
        self._update_amount_prefix()

    @Slot()
    def _on_currency_changed(self):
        selected_currency = self.currency_combo.currentData()
        is_base = (selected_currency == self._base_currency)
        can_edit_rate = not is_base and not self.view_only_mode
        self.exchange_rate_spin.setEnabled(can_edit_rate)
        self.exchange_rate_spin.setReadOnly(not can_edit_rate)
        if is_base: self.exchange_rate_spin.setValue(1.0)
        self._update_amount_prefix()

    def _update_amount_prefix(self):
        currency_code = self.currency_combo.currentData()
        if not currency_code: 
            ba_id = self.bank_account_combo.currentData()
            if ba_id and ba_id != 0:
                 selected_ba = next((b for b in self._bank_accounts_cache if b.get("id") == ba_id), None)
                 if selected_ba: currency_code = selected_ba.get("currency_code")
        self.payment_amount_edit.setPrefix(f"{currency_code} " if currency_code else "$ ")

    def _clear_allocations_table(self):
        self.allocations_table.setRowCount(0)

    async def _load_allocatable_documents(self):
        self._in_data_load = True
        self._clear_allocations_table(); self._allocatable_invoices_cache = []
        entity_id = self.entity_combo.currentData()
        payment_type = self.payment_type_combo.currentData()
        if not entity_id or entity_id == 0 or not payment_type: self._in_data_load = False; return

        invoices_to_allocate: List[Dict[str, Any]] = []
        try:
            if payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT and self.app_core.sales_invoice_manager:
                result_si: Result[List[SalesInvoiceSummaryData]] = await self.app_core.sales_invoice_manager.get_invoices_for_listing(
                    customer_id=entity_id, status_list=[InvoiceStatusEnum.APPROVED, InvoiceStatusEnum.PARTIALLY_PAID, InvoiceStatusEnum.OVERDUE],
                    page_size=-1 
                ) # type: ignore
                if result_si.is_success and result_si.value:
                    for inv_summary in result_si.value:
                        # Ensure currency_code exists in SalesInvoiceSummaryData for this to work
                        currency = getattr(inv_summary, 'currency_code', self.currency_combo.currentData())
                        invoices_to_allocate.append({
                            "id": inv_summary.id, "doc_type": PaymentAllocationDocTypeEnum.SALES_INVOICE,
                            "doc_no": inv_summary.invoice_no, "doc_date": inv_summary.invoice_date,
                            "doc_total": inv_summary.total_amount, "amount_paid": inv_summary.amount_paid,
                            "outstanding": inv_summary.total_amount - inv_summary.amount_paid, 
                            "currency": currency
                        })
            elif payment_type == PaymentTypeEnum.VENDOR_PAYMENT and self.app_core.purchase_invoice_manager:
                result_pi: Result[List[PurchaseInvoiceSummaryData]] = await self.app_core.purchase_invoice_manager.get_invoices_for_listing(
                    vendor_id=entity_id, status_list=[InvoiceStatusEnum.APPROVED, InvoiceStatusEnum.PARTIALLY_PAID, InvoiceStatusEnum.OVERDUE],
                    page_size=-1
                ) # type: ignore
                if result_pi.is_success and result_pi.value:
                    for inv_summary in result_pi.value:
                        # Ensure currency_code and amount_paid exist for PurchaseInvoiceSummaryData
                        currency = getattr(inv_summary, 'currency_code', self.currency_combo.currentData())
                        amount_paid = getattr(inv_summary, 'amount_paid', Decimal(0))
                        invoices_to_allocate.append({
                            "id": inv_summary.id, "doc_type": PaymentAllocationDocTypeEnum.PURCHASE_INVOICE,
                            "doc_no": inv_summary.invoice_no, "doc_date": inv_summary.invoice_date, 
                            "doc_total": inv_summary.total_amount, "amount_paid": amount_paid,
                            "outstanding": inv_summary.total_amount - amount_paid, 
                            "currency": currency
                        })
            self._allocatable_invoices_cache = invoices_to_allocate
            QMetaObject.invokeMethod(self, "_populate_allocations_table_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading allocatable documents: {e}", exc_info=True)
            QMessageBox.warning(self, "Load Error", f"Could not load documents for allocation: {str(e)}")
        finally:
            self._in_data_load = False

    @Slot()
    def _populate_allocations_table_slot(self):
        self._in_data_load = True; self.allocations_table.setRowCount(0)
        payment_currency = self.currency_combo.currentData()
        
        for inv_data in self._allocatable_invoices_cache:
            if inv_data.get("currency") != payment_currency:
                self.app_core.logger.debug(f"Skipping invoice {inv_data['doc_no']} due to currency mismatch ({inv_data.get('currency')} vs {payment_currency})")
                continue
            
            row_idx = self.allocations_table.rowCount() 
            self.allocations_table.insertRow(row_idx)
            
            chk_box_item_widget = QWidget(); chk_box_layout = QHBoxLayout(chk_box_item_widget); chk_box_layout.setContentsMargins(0,0,0,0); chk_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            select_chk = QCheckBox(); chk_box_layout.addWidget(select_chk)
            self.allocations_table.setCellWidget(row_idx, self.ALLOC_COL_SELECT, chk_box_item_widget)
            select_chk.stateChanged.connect(lambda state, r=row_idx: self._on_allocation_select_changed(r, state))

            doc_type_str = inv_data["doc_type"].value if isinstance(inv_data["doc_type"], PaymentAllocationDocTypeEnum) else str(inv_data["doc_type"])
            self.allocations_table.setItem(row_idx, self.ALLOC_COL_DOC_TYPE, QTableWidgetItem(doc_type_str))
            doc_no_item = QTableWidgetItem(inv_data["doc_no"])
            doc_no_item.setData(Qt.ItemDataRole.UserRole, inv_data['id']) 
            self.allocations_table.setItem(row_idx, self.ALLOC_COL_DOC_NO, doc_no_item)
            doc_date_str = inv_data["doc_date"].strftime('%d/%m/%Y') if isinstance(inv_data["doc_date"], date) else str(inv_data["doc_date"])
            self.allocations_table.setItem(row_idx, self.ALLOC_COL_DOC_DATE, QTableWidgetItem(doc_date_str))
            
            doc_total_item = QTableWidgetItem(f"{inv_data['doc_total']:.2f}")
            doc_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.allocations_table.setItem(row_idx, self.ALLOC_COL_DOC_TOTAL, doc_total_item)
            
            outstanding_item = QTableWidgetItem(f"{inv_data['outstanding']:.2f}")
            outstanding_item.setData(Qt.ItemDataRole.UserRole, inv_data['outstanding']) 
            outstanding_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.allocations_table.setItem(row_idx, self.ALLOC_COL_OUTSTANDING, outstanding_item)

            for col in range(self.ALLOC_COL_DOC_TYPE, self.ALLOC_COL_OUTSTANDING + 1): 
                item = self.allocations_table.item(row_idx, col)
                if item: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            allocate_spin = QDoubleSpinBox()
            allocate_spin.setDecimals(2); allocate_spin.setRange(0.00, float(inv_data['outstanding'])) 
            allocate_spin.setGroupSeparatorShown(True); allocate_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            allocate_spin.setValue(0.00) 
            self.allocations_table.setCellWidget(row_idx, self.ALLOC_COL_TO_ALLOCATE, allocate_spin)
        
        self._update_allocation_totals()
        self._in_data_load = False
        if self.loaded_payment_data and self.loaded_payment_data.allocations: 
            self._populate_existing_allocations(self.loaded_payment_data.allocations)


    @Slot(int, int)
    def _on_allocation_select_changed(self, row: int, state: int):
        if self._in_data_load: return
        allocate_spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(row, self.ALLOC_COL_TO_ALLOCATE))
        outstanding_item = self.allocations_table.item(row, self.ALLOC_COL_OUTSTANDING)
        if not allocate_spin or not outstanding_item: return

        outstanding_amount = Decimal(outstanding_item.data(Qt.ItemDataRole.UserRole) or '0')
        payment_total_amount = Decimal(str(self.payment_amount_edit.value()))
        
        current_total_allocated_elsewhere = Decimal(0)
        for r in range(self.allocations_table.rowCount()):
            if r == row: continue 
            spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(r, self.ALLOC_COL_TO_ALLOCATE))
            if spin: current_total_allocated_elsewhere += Decimal(str(spin.value()))
        
        remaining_payment_to_allocate = payment_total_amount - current_total_allocated_elsewhere

        if Qt.CheckState(state) == Qt.CheckState.Checked:
            amount_to_auto_allocate = min(outstanding_amount, remaining_payment_to_allocate)
            if amount_to_auto_allocate < Decimal("0.01") and outstanding_amount > Decimal("0.005"): 
                 allocate_spin.setValue(0.00) 
                 QMessageBox.information(self, "Allocation Info", f"Not enough unallocated payment amount to apply to {self.allocations_table.item(row, self.ALLOC_COL_DOC_NO).text()}.")
                 chk_box_widget = cast(QWidget, self.allocations_table.cellWidget(row, self.ALLOC_COL_SELECT))
                 if chk_box_widget:
                     chk_box = chk_box_widget.findChild(QCheckBox)
                     if chk_box: self._in_data_load = True; chk_box.setChecked(False); self._in_data_load = False
            else:
                allocate_spin.setValue(float(max(Decimal(0), amount_to_auto_allocate)))
        else: 
            allocate_spin.setValue(0.00)
        self._update_allocation_totals()

    def _update_allocation_totals_and_checkbox(self, row: int):
        if self._in_data_load: return
        allocate_spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(row, self.ALLOC_COL_TO_ALLOCATE))
        chk_box_widget = cast(QWidget, self.allocations_table.cellWidget(row, self.ALLOC_COL_SELECT))
        if not allocate_spin or not chk_box_widget: return
        chk_box = chk_box_widget.findChild(QCheckBox)
        if not chk_box: return

        current_allocation = Decimal(str(allocate_spin.value()))
        outstanding_item = self.allocations_table.item(row, self.ALLOC_COL_OUTSTANDING)
        max_allocatable_for_line = Decimal(outstanding_item.data(Qt.ItemDataRole.UserRole) or '0')

        if current_allocation > max_allocatable_for_line:
            QMessageBox.warning(self, "Allocation Error", f"Allocation for {self.allocations_table.item(row, self.ALLOC_COL_DOC_NO).text()} cannot exceed its outstanding amount of {max_allocatable_for_line:.2f}.")
            allocate_spin.setValue(float(max_allocatable_for_line))
            current_allocation = max_allocatable_for_line

        payment_total_amount = Decimal(str(self.payment_amount_edit.value()))
        temp_total_allocated = Decimal(0)
        for r in range(self.allocations_table.rowCount()):
            spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(r, self.ALLOC_COL_TO_ALLOCATE))
            if spin: temp_total_allocated += Decimal(str(spin.value()))
        
        if temp_total_allocated > payment_total_amount:
            over_allocated = temp_total_allocated - payment_total_amount
            corrected_line_allocation = max(Decimal(0), current_allocation - over_allocated)
            if corrected_line_allocation != current_allocation: 
                QMessageBox.warning(self, "Allocation Error", f"Total allocated amount exceeds payment amount. Reducing allocation for current line.")
                allocate_spin.setValue(float(corrected_line_allocation))

        self._in_data_load = True 
        chk_box.setChecked(Decimal(str(allocate_spin.value())) > Decimal("0.005"))
        self._in_data_load = False
        self._update_allocation_totals()

    def _update_allocation_totals(self):
        total_allocated = Decimal(0)
        for r in range(self.allocations_table.rowCount()):
            allocate_spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(r, self.ALLOC_COL_TO_ALLOCATE))
            if allocate_spin: total_allocated += Decimal(str(allocate_spin.value()))
        payment_amount = Decimal(str(self.payment_amount_edit.value())); unallocated_amount = payment_amount - total_allocated
        self.total_allocated_label.setText(f"Total Allocated: {total_allocated:,.2f}")
        if unallocated_amount < Decimal(0): self.unallocated_amount_label.setText(f"OVER-ALLOCATED: {unallocated_amount:,.2f}"); self.unallocated_amount_label.setStyleSheet("font-weight: bold; color: red;")
        elif unallocated_amount == Decimal(0) and payment_amount > 0: self.unallocated_amount_label.setText("Fully Allocated"); self.unallocated_amount_label.setStyleSheet("font-weight: bold; color: green;")
        else: self.unallocated_amount_label.setText(f"Unallocated: {unallocated_amount:,.2f}"); self.unallocated_amount_label.setStyleSheet("font-weight: bold;")

    def _collect_data(self) -> Optional[PaymentCreateData]:
        entity_id_data = self.entity_combo.currentData()
        if not entity_id_data or entity_id_data == 0: QMessageBox.warning(self, "Validation Error", "Entity must be selected."); return None
        payment_type_enum = self.payment_type_combo.currentData()
        entity_type_enum = PaymentEntityTypeEnum.CUSTOMER if payment_type_enum == PaymentTypeEnum.CUSTOMER_PAYMENT else PaymentEntityTypeEnum.VENDOR
        payment_method_enum = self.payment_method_combo.currentData()
        bank_account_id_data = self.bank_account_combo.currentData()
        bank_account_id_val = int(bank_account_id_data) if bank_account_id_data and bank_account_id_data !=0 else None
        if payment_method_enum != PaymentMethodEnum.CASH and not bank_account_id_val: QMessageBox.warning(self, "Validation Error", "Bank Account is required for non-cash payment methods."); return None

        allocations: List[PaymentAllocationBaseData] = []
        total_allocated_check = Decimal(0)
        for r in range(self.allocations_table.rowCount()):
            chk_box_widget = cast(QWidget, self.allocations_table.cellWidget(r, self.ALLOC_COL_SELECT))
            chk_box = chk_box_widget.findChild(QCheckBox) if chk_box_widget else None
            allocate_spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(r, self.ALLOC_COL_TO_ALLOCATE))
            if chk_box and chk_box.isChecked() and allocate_spin and Decimal(str(allocate_spin.value())) > Decimal("0.005"):
                doc_id_item = self.allocations_table.item(r, self.ALLOC_COL_DOC_NO); doc_type_item = self.allocations_table.item(r, self.ALLOC_COL_DOC_TYPE)
                if not doc_id_item or not doc_type_item: continue
                doc_id = doc_id_item.data(Qt.ItemDataRole.UserRole); doc_type_str = doc_type_item.text()
                doc_type_enum_member = next((member for name, member in PaymentAllocationDocTypeEnum.__members__.items() if member.value == doc_type_str), None)
                if not doc_type_enum_member: QMessageBox.warning(self, "Data Error", f"Invalid document type '{doc_type_str}' in allocation line {r+1}."); return None
                amount_to_allocate = Decimal(str(allocate_spin.value()))
                total_allocated_check += amount_to_allocate
                allocations.append(PaymentAllocationBaseData(document_id=int(doc_id), document_type=doc_type_enum_member, amount_allocated=amount_to_allocate))
        
        payment_amount_val = Decimal(str(self.payment_amount_edit.value()))
        if total_allocated_check > payment_amount_val: QMessageBox.warning(self, "Allocation Error", f"Total allocated amount ({total_allocated_check:.2f}) exceeds payment amount ({payment_amount_val:.2f}). Please adjust allocations."); return None

        common_data_dict = {
            "payment_type": payment_type_enum, "payment_method": payment_method_enum,
            "payment_date": self.payment_date_edit.date().toPython(),
            "entity_type": entity_type_enum, "entity_id": int(entity_id_data),
            "bank_account_id": bank_account_id_val,
            "currency_code": self.currency_combo.currentData() or self._base_currency,
            "exchange_rate": Decimal(str(self.exchange_rate_spin.value())), "amount": payment_amount_val,
            "reference": self.reference_edit.text().strip() or None,
            "description": self.description_edit.toPlainText().strip() or None,
            "cheque_no": self.cheque_no_edit.text().strip() if self.cheque_no_label.isVisible() else None,
            "user_id": self.current_user_id, "allocations": allocations
        }
        try:
            return PaymentCreateData(**common_data_dict) # type: ignore
        except ValueError as ve: QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{str(ve)}"); return None

    @Slot()
    def on_save_payment(self):
        if self.view_only_mode: return
        dto = self._collect_data()
        if dto: 
            self.save_button.setEnabled(False)
            future = schedule_task_from_qt(self._perform_save(dto))
            if future: future.add_done_callback(lambda res: self._handle_save_result(res))
            else: self.app_core.logger.error("Failed to schedule _perform_save for payment."); self.save_button.setEnabled(True); QMessageBox.critical(self, "Task Error", "Failed to schedule payment save operation.")

    def _handle_save_result(self, future_obj): 
        self.save_button.setEnabled(True) 
        if future_obj is None: QMessageBox.critical(self, "Task Error", "Payment save task did not run."); return
        try:
            result: Result[Payment] = future_obj.result()
            if result.is_success and result.value:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection, Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Payment '{result.value.payment_no}' saved and posted successfully."))
                self.payment_saved.emit(result.value.id); QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
            else: QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection, Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save payment:\n{', '.join(result.errors)}"))
        except Exception as e: self.app_core.logger.error(f"Exception in _handle_save_result for payment: {e}", exc_info=True); QMessageBox.critical(self, "Save Error", f"An unexpected error occurred during save: {str(e)}")

    async def _perform_save(self, dto: PaymentCreateData): 
        if not self.app_core.payment_manager: return Result.failure(["Payment Manager not available."])
        result = await self.app_core.payment_manager.create_payment(dto)
        return result 

    async def _load_existing_payment_data(self):
        if not self.payment_id or not self.app_core.payment_manager: return
        self._in_data_load = True
        self.loaded_payment_data = await self.app_core.payment_manager.get_payment_for_dialog(self.payment_id)
        self.setWindowTitle(self._get_window_title())
        if self.loaded_payment_data:
            self._populate_header_fields_from_orm(self.loaded_payment_data) 
            self.view_only_mode = self.loaded_payment_data.status != PaymentStatusEnum.DRAFT.value 
            self._set_read_only_state(self.view_only_mode)
        else: QMessageBox.warning(self, "Load Error", f"Payment ID {self.payment_id} not found."); self.reject()
        self._in_data_load = False 
    
    def _populate_header_fields_from_orm(self, payment_orm: Payment):
        self.payment_type_combo.setCurrentIndex(self.payment_type_combo.findData(PaymentTypeEnum(payment_orm.payment_type)))
        entity_idx = self.entity_combo.findData(payment_orm.entity_id); 
        if entity_idx != -1: self.entity_combo.setCurrentIndex(entity_idx)
        else: self.app_core.logger.warning(f"Entity ID {payment_orm.entity_id} for payment not found in combo.")
        self.payment_date_edit.setDate(QDate(payment_orm.payment_date))
        self.payment_method_combo.setCurrentIndex(self.payment_method_combo.findData(PaymentMethodEnum(payment_orm.payment_method)))
        if payment_orm.bank_account_id:
            ba_idx = self.bank_account_combo.findData(payment_orm.bank_account_id)
            if ba_idx != -1: self.bank_account_combo.setCurrentIndex(ba_idx)
        curr_idx = self.currency_combo.findData(payment_orm.currency_code)
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
        self.exchange_rate_spin.setValue(float(payment_orm.exchange_rate))
        self.payment_amount_edit.setValue(float(payment_orm.amount))
        self.reference_edit.setText(payment_orm.reference or "")
        self.description_edit.setText(payment_orm.description or "")
        self.cheque_no_edit.setText(payment_orm.cheque_no or "")
        self._update_dynamic_fields(); self._on_currency_changed()

    def _populate_existing_allocations(self, allocations_orm_list: List[PaymentAllocation]):
        if not self._allocatable_invoices_cache: self.app_core.logger.info("Cannot populate existing allocations: allocatable invoices not yet loaded."); return
        self._in_data_load = True
        for r in range(self.allocations_table.rowCount()):
            doc_id_item = self.allocations_table.item(r, self.ALLOC_COL_DOC_NO); 
            if not doc_id_item: continue
            table_doc_id = doc_id_item.data(Qt.ItemDataRole.UserRole)
            doc_type_item_text = self.allocations_table.item(r, self.ALLOC_COL_DOC_TYPE).text()
            matching_alloc_orm = next((alloc for alloc in allocations_orm_list if alloc.document_id == table_doc_id and alloc.document_type == doc_type_item_text), None)
            if matching_alloc_orm:
                chk_box_widget = cast(QWidget, self.allocations_table.cellWidget(r, self.ALLOC_COL_SELECT))
                chk_box = chk_box_widget.findChild(QCheckBox) if chk_box_widget else None
                allocate_spin = cast(QDoubleSpinBox, self.allocations_table.cellWidget(r, self.ALLOC_COL_TO_ALLOCATE))
                if chk_box: chk_box.setChecked(True)
                if allocate_spin: allocate_spin.setValue(float(matching_alloc_orm.amount))
        self._update_allocation_totals(); self._in_data_load = False
        
    def _set_read_only_state(self, read_only: bool):
        self.payment_type_combo.setEnabled(not read_only)
        self.entity_combo.setEnabled(not read_only)
        self.payment_date_edit.setReadOnly(read_only)
        self.payment_method_combo.setEnabled(not read_only)
        self._update_dynamic_fields() 
        if read_only: 
            self.bank_account_combo.setEnabled(False)
            self.cheque_no_edit.setReadOnly(True)

        self.currency_combo.setEnabled(not read_only)
        self._on_currency_changed() 
        if read_only: 
            self.exchange_rate_spin.setReadOnly(True) 

        self.payment_amount_edit.setReadOnly(read_only)
        self.reference_edit.setReadOnly(read_only)
        self.description_edit.setReadOnly(read_only)
        
        self.allocations_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers if read_only else 
            QAbstractItemView.EditTrigger.AllInputs 
        )
        for r in range(self.allocations_table.rowCount()):
            chk_box_widget = cast(QWidget, self.allocations_table.cellWidget(r, self.ALLOC_COL_SELECT))
            if chk_box_widget:
                chk_box = chk_box_widget.findChild(QCheckBox)
                if chk_box: chk_box.setEnabled(not read_only)
        
        self.save_button.setVisible(not read_only)


```

# app/ui/payments/payment_table_model.py
```py
# File: app/ui/payments/payment_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import PaymentSummaryData
from app.common.enums import PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum

class PaymentTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[PaymentSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Payment No", "Date", "Type", "Method", 
            "Entity Type", "Entity Name", "Amount", "Currency", "Status"
        ]
        self._data: List[PaymentSummaryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_table(self, value: Optional[Decimal]) -> str:
        if value is None: 
            return "0.00"
        try:
            return f"{Decimal(str(value)):,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) 

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        payment_summary: PaymentSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(payment_summary.id)
            if col == 1: return payment_summary.payment_no
            if col == 2: # Date
                pay_date = payment_summary.payment_date
                return pay_date.strftime('%d/%m/%Y') if isinstance(pay_date, python_date) else str(pay_date)
            if col == 3: # Type
                return payment_summary.payment_type.value if isinstance(payment_summary.payment_type, PaymentTypeEnum) else str(payment_summary.payment_type)
            if col == 4: # Method
                 return payment_summary.payment_method.value if isinstance(payment_summary.payment_method, PaymentMethodEnum) else str(payment_summary.payment_method)
            if col == 5: # Entity Type
                 return payment_summary.entity_type.value if isinstance(payment_summary.entity_type, PaymentEntityTypeEnum) else str(payment_summary.entity_type)
            if col == 6: return payment_summary.entity_name
            if col == 7: return self._format_decimal_for_table(payment_summary.amount)
            if col == 8: return payment_summary.currency_code
            if col == 9: # Status
                return payment_summary.status.value if isinstance(payment_summary.status, PaymentStatusEnum) else str(payment_summary.status)
            return ""

        elif role == Qt.ItemDataRole.UserRole: 
            if col == 0: 
                return payment_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Amount":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] in ["Date", "Status", "Type", "Method"]:
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_payment_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole is not used for ID or is somehow None
            return self._data[row].id 
        return None
        
    def get_payment_status_at_row(self, row: int) -> Optional[PaymentStatusEnum]:
        if 0 <= row < len(self._data):
            status_val = self._data[row].status
            return status_val if isinstance(status_val, PaymentStatusEnum) else None
        return None

    def update_data(self, new_data: List[PaymentSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/main_window.py
```py
# File: app/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, 
    QVBoxLayout, QWidget, QMessageBox, QLabel 
)
from PySide6.QtGui import QIcon, QKeySequence, QAction 
from PySide6.QtCore import Qt, QSettings, Signal, Slot, QCoreApplication, QSize 

from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.accounting.accounting_widget import AccountingWidget
from app.ui.sales_invoices.sales_invoices_widget import SalesInvoicesWidget
from app.ui.purchase_invoices.purchase_invoices_widget import PurchaseInvoicesWidget
from app.ui.payments.payments_widget import PaymentsWidget 
from app.ui.customers.customers_widget import CustomersWidget
from app.ui.vendors.vendors_widget import VendorsWidget
from app.ui.products.products_widget import ProductsWidget
from app.ui.banking.banking_widget import BankingWidget
from app.ui.banking.bank_reconciliation_widget import BankReconciliationWidget 
from app.ui.reports.reports_widget import ReportsWidget
from app.ui.settings.settings_widget import SettingsWidget
from app.core.application_core import ApplicationCore

class MainWindow(QMainWindow):
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        self.app_core = app_core
        
        self.setWindowTitle(f"{QCoreApplication.applicationName()} - {QCoreApplication.applicationVersion()}")
        self.setMinimumSize(1024, 768)
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        settings = QSettings() 
        if settings.contains("MainWindow/geometry"):
            self.restoreGeometry(settings.value("MainWindow/geometry")) 
        else:
            self.resize(1280, 800)
        
        self._init_ui()
        
        if settings.contains("MainWindow/state"):
            self.restoreState(settings.value("MainWindow/state")) 
    
    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        self._create_toolbar()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        self._add_module_tabs()
        self._create_status_bar()
        self._create_actions()
        self._create_menus()
    
    def _create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar"); self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setMovable(False); self.toolbar.setIconSize(QSize(24, 24)) 
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        self.dashboard_widget = DashboardWidget(self.app_core); self.tab_widget.addTab(self.dashboard_widget, QIcon(self.icon_path_prefix + "dashboard.svg"), "Dashboard")
        self.accounting_widget = AccountingWidget(self.app_core); self.tab_widget.addTab(self.accounting_widget, QIcon(self.icon_path_prefix + "accounting.svg"), "Accounting")
        self.sales_invoices_widget = SalesInvoicesWidget(self.app_core); self.tab_widget.addTab(self.sales_invoices_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Sales") 
        self.purchase_invoices_widget = PurchaseInvoicesWidget(self.app_core); self.tab_widget.addTab(self.purchase_invoices_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Purchases") 
        self.payments_widget = PaymentsWidget(self.app_core); self.tab_widget.addTab(self.payments_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Payments") 
        self.customers_widget = CustomersWidget(self.app_core); self.tab_widget.addTab(self.customers_widget, QIcon(self.icon_path_prefix + "customers.svg"), "Customers")
        self.vendors_widget = VendorsWidget(self.app_core); self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")
        self.products_widget = ProductsWidget(self.app_core); self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Banking C.R.U.D") 
        self.bank_reconciliation_widget = BankReconciliationWidget(self.app_core)
        self.tab_widget.addTab(self.bank_reconciliation_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Bank Reconciliation") 
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(self.icon_path_prefix + "reports.svg"), "Reports")
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(self.icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready"); self.status_bar.addWidget(self.status_label, 1) 
        user_text = "User: Guest"; 
        if self.app_core.current_user: user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text); self.status_bar.addPermanentWidget(self.user_label)
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}"); self.status_bar.addPermanentWidget(self.version_label)

    def _create_actions(self):
        self.new_company_action = QAction(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...", self); self.new_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New)); self.new_company_action.triggered.connect(self.on_new_company)
        self.open_company_action = QAction(QIcon(self.icon_path_prefix + "open_company.svg"), "Open Company...", self); self.open_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open)); self.open_company_action.triggered.connect(self.on_open_company)
        self.backup_action = QAction(QIcon(self.icon_path_prefix + "backup.svg"), "Backup Data...", self); self.backup_action.triggered.connect(self.on_backup)
        self.restore_action = QAction(QIcon(self.icon_path_prefix + "restore.svg"), "Restore Data...", self); self.restore_action.triggered.connect(self.on_restore)
        self.exit_action = QAction(QIcon(self.icon_path_prefix + "exit.svg"), "Exit", self); self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit)); self.exit_action.triggered.connect(self.close) 
        self.preferences_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Preferences...", self); self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences)); self.preferences_action.triggered.connect(self.on_preferences)
        self.help_contents_action = QAction(QIcon(self.icon_path_prefix + "help.svg"), "Help Contents", self); self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents)); self.help_contents_action.triggered.connect(self.on_help_contents)
        self.about_action = QAction(QIcon(self.icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self); self.about_action.triggered.connect(self.on_about)

    def _create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File"); self.file_menu.addAction(self.new_company_action); self.file_menu.addAction(self.open_company_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.backup_action); self.file_menu.addAction(self.restore_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)
        self.edit_menu = self.menuBar().addMenu("&Edit"); self.edit_menu.addAction(self.preferences_action)
        self.view_menu = self.menuBar().addMenu("&View"); self.tools_menu = self.menuBar().addMenu("&Tools")
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.help_contents_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)
        self.toolbar.addAction(self.new_company_action); self.toolbar.addAction(self.open_company_action); self.toolbar.addSeparator(); self.toolbar.addAction(self.backup_action); self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): QMessageBox.information(self, "New Company", "New company wizard not yet implemented.")
    @Slot()
    def on_open_company(self): QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented.")
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): 
        settings_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.settings_widget: settings_tab_index = i; break
        if settings_tab_index != -1: self.tab_widget.setCurrentIndex(settings_tab_index)
        else: QMessageBox.information(self, "Preferences", "Preferences (Settings Tab) not found or full dialog not yet implemented.")
    @Slot()
    def on_help_contents(self): QMessageBox.information(self, "Help", "Help system not yet implemented.")
    @Slot()
    def on_about(self): QMessageBox.about(self, f"About {QCoreApplication.applicationName()}", f"{QCoreApplication.applicationName()} {QCoreApplication.applicationVersion()}\n\nA comprehensive bookkeeping application for Singapore small businesses.\n\n© 2024 {QCoreApplication.organizationName()}"); 
    def closeEvent(self, event): 
        settings = QSettings(); settings.setValue("MainWindow/geometry", self.saveGeometry()); settings.setValue("MainWindow/state", self.saveState()); settings.sync()
        reply = QMessageBox.question(self, "Confirm Exit", "Are you sure you want to exit?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: event.accept() 
        else: event.ignore()

```

# app/ui/reports/__init__.py
```py
# app/ui/reports/__init__.py
from .reports_widget import ReportsWidget
from .trial_balance_table_model import TrialBalanceTableModel # New Export
from .general_ledger_table_model import GeneralLedgerTableModel # New Export

__all__ = [
    "ReportsWidget",
    "TrialBalanceTableModel", # New Export
    "GeneralLedgerTableModel", # New Export
]


```

# app/ui/reports/reports_widget.py
```py
# File: app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter,
    QStackedWidget, QTreeView, QTableView, 
    QAbstractItemView, QCheckBox 
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG, QStandardPaths
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont, QColor
from typing import Optional, Dict, Any, TYPE_CHECKING, List 

import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date, timedelta 

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData, GSTTransactionLineDetail, FiscalYearData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.account import Account 
from app.models.accounting.dimension import Dimension 
from app.models.accounting.fiscal_year import FiscalYear

from .trial_balance_table_model import TrialBalanceTableModel
from .general_ledger_table_model import GeneralLedgerTableModel

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice 

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None 
        self._saved_draft_gst_return_orm: Optional[GSTReturn] = None 
        self._current_financial_report_data: Optional[Dict[str, Any]] = None
        self._gl_accounts_cache: List[Dict[str, Any]] = [] 
        self._dimension_types_cache: List[str] = []
        self._dimension_codes_cache: Dict[str, List[Dict[str, Any]]] = {} 
        self._fiscal_years_cache: List[FiscalYearData] = []

        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self.main_layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self._create_gst_f5_tab()
        self._create_financial_statements_tab()
        
        self.setLayout(self.main_layout)
        # Load data required for filter combos
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_fs_combo_data()))

    def _format_decimal_for_display(self, value: Optional[Decimal], default_str: str = "0.00", show_blank_for_zero: bool = False) -> str:
        if value is None: return default_str if not show_blank_for_zero else ""
        try:
            d_value = Decimal(str(value)); 
            if show_blank_for_zero and d_value.is_zero(): return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError): return "Error" 

    def _create_gst_f5_tab(self):
        gst_f5_widget = QWidget(); gst_f5_main_layout = QVBoxLayout(gst_f5_widget); gst_f5_group = QGroupBox("GST F5 Return Data Preparation"); gst_f5_group_layout = QVBoxLayout(gst_f5_group) 
        date_selection_layout = QHBoxLayout(); date_form = QFormLayout()
        self.gst_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(-QDate.currentDate().day()+1)); self.gst_start_date_edit.setCalendarPopup(True); self.gst_start_date_edit.setDisplayFormat("dd/MM/yyyy"); date_form.addRow("Period Start Date:", self.gst_start_date_edit)
        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); 
        if self.gst_end_date_edit.date() < self.gst_start_date_edit.date(): self.gst_end_date_edit.setDate(self.gst_start_date_edit.date().addMonths(1).addDays(-1))
        self.gst_end_date_edit.setCalendarPopup(True); self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy"); date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form); prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data"); self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button); prepare_button_layout.addStretch(); date_selection_layout.addLayout(prepare_button_layout); date_selection_layout.addStretch(1); gst_f5_group_layout.addLayout(date_selection_layout)
        self.gst_display_form = QFormLayout(); self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True); self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True); self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True); self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;"); self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True); self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True); self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True); self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True); self.gst_net_payable_display = QLineEdit(); self.gst_net_payable_display.setReadOnly(True); self.gst_net_payable_display.setStyleSheet("font-weight: bold;"); self.gst_filing_due_date_display = QLineEdit(); self.gst_filing_due_date_display.setReadOnly(True)
        self.gst_display_form.addRow("1. Standard-Rated Supplies:", self.gst_std_rated_supplies_display); self.gst_display_form.addRow("2. Zero-Rated Supplies:", self.gst_zero_rated_supplies_display); self.gst_display_form.addRow("3. Exempt Supplies:", self.gst_exempt_supplies_display); self.gst_display_form.addRow("4. Total Supplies (1+2+3):", self.gst_total_supplies_display); self.gst_display_form.addRow("5. Taxable Purchases:", self.gst_taxable_purchases_display); self.gst_display_form.addRow("6. Output Tax Due:", self.gst_output_tax_display); self.gst_display_form.addRow("7. Input Tax and Refunds Claimed:", self.gst_input_tax_display); self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display); self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display); self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
        gst_f5_group_layout.addLayout(self.gst_display_form)
        
        gst_action_button_layout = QHBoxLayout()
        self.save_draft_gst_button = QPushButton("Save Draft GST Return"); self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked)
        self.finalize_gst_button = QPushButton("Finalize GST Return"); self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked)
        
        self.export_gst_detail_excel_button = QPushButton("Export Details (Excel)"); self.export_gst_detail_excel_button.setEnabled(False)
        self.export_gst_detail_excel_button.clicked.connect(self._on_export_gst_f5_details_excel_clicked)

        gst_action_button_layout.addStretch()
        gst_action_button_layout.addWidget(self.export_gst_detail_excel_button); gst_action_button_layout.addWidget(self.save_draft_gst_button); gst_action_button_layout.addWidget(self.finalize_gst_button)
        gst_f5_group_layout.addLayout(gst_action_button_layout)

        gst_f5_main_layout.addWidget(gst_f5_group); gst_f5_main_layout.addStretch(); self.tab_widget.addTab(gst_f5_widget, "GST F5 Preparation")

    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        start_date = self.gst_start_date_edit.date().toPython(); end_date = self.gst_end_date_edit.date().toPython()
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        if not self.app_core.gst_manager: QMessageBox.critical(self, "Error", "GST Manager not available."); return
        self.prepare_gst_button.setEnabled(False); self.prepare_gst_button.setText("Preparing...")
        self._saved_draft_gst_return_orm = None; self.finalize_gst_button.setEnabled(False); self.export_gst_detail_excel_button.setEnabled(False) 
        future = schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, self.app_core.current_user.id))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_handle_prepare_gst_f5_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule GST data preparation task."); self._handle_prepare_gst_f5_result(None) 

    @Slot(object)
    def _safe_handle_prepare_gst_f5_result_slot(self, future_arg):
        self._handle_prepare_gst_f5_result(future_arg)

    def _handle_prepare_gst_f5_result(self, future):
        self.prepare_gst_button.setEnabled(True); self.prepare_gst_button.setText("Prepare GST F5 Data"); self.export_gst_detail_excel_button.setEnabled(False) 
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST data preparation."); self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); return
        try:
            result: Result[GSTReturnData] = future.result()
            if result.is_success and result.value: 
                self._prepared_gst_data = result.value; self._update_gst_f5_display(self._prepared_gst_data)
                self.save_draft_gst_button.setEnabled(True); self.finalize_gst_button.setEnabled(False) 
                if self._prepared_gst_data and self._prepared_gst_data.detailed_breakdown: self.export_gst_detail_excel_button.setEnabled(True)
            else: self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e: self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True); QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")

    def _update_gst_f5_display(self, gst_data: GSTReturnData):
        self.gst_std_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.standard_rated_supplies)); self.gst_zero_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.zero_rated_supplies)); self.gst_exempt_supplies_display.setText(self._format_decimal_for_display(gst_data.exempt_supplies)); self.gst_total_supplies_display.setText(self._format_decimal_for_display(gst_data.total_supplies)); self.gst_taxable_purchases_display.setText(self._format_decimal_for_display(gst_data.taxable_purchases)); self.gst_output_tax_display.setText(self._format_decimal_for_display(gst_data.output_tax)); self.gst_input_tax_display.setText(self._format_decimal_for_display(gst_data.input_tax)); self.gst_adjustments_display.setText(self._format_decimal_for_display(gst_data.tax_adjustments)); self.gst_net_payable_display.setText(self._format_decimal_for_display(gst_data.tax_payable)); self.gst_filing_due_date_display.setText(gst_data.filing_due_date.strftime('%d/%m/%Y') if gst_data.filing_due_date else "")
    
    def _clear_gst_display_fields(self):
        for w in [self.gst_std_rated_supplies_display, self.gst_zero_rated_supplies_display, self.gst_exempt_supplies_display, self.gst_total_supplies_display, self.gst_taxable_purchases_display, self.gst_output_tax_display, self.gst_input_tax_display, self.gst_net_payable_display, self.gst_filing_due_date_display]: w.clear()
        self.gst_adjustments_display.setText("0.00"); self._prepared_gst_data = None; self._saved_draft_gst_return_orm = None; self.export_gst_detail_excel_button.setEnabled(False) 
    
    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        if not self._prepared_gst_data: QMessageBox.warning(self, "No Data", "Please prepare GST data first."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        self._prepared_gst_data.user_id = self.app_core.current_user.id
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.id: self._prepared_gst_data.id = self._saved_draft_gst_return_orm.id
        self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.setText("Saving Draft..."); self.finalize_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.save_gst_return(self._prepared_gst_data))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_handle_save_draft_gst_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule GST draft save task."); self._handle_save_draft_gst_result(None)

    @Slot(object)
    def _safe_handle_save_draft_gst_result_slot(self, future_arg):
        self._handle_save_draft_gst_result(future_arg)

    def _handle_save_draft_gst_result(self, future):
        self.save_draft_gst_button.setEnabled(True); self.save_draft_gst_button.setText("Save Draft GST Return")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST draft save."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                self._saved_draft_gst_return_orm = result.value
                if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id 
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id})."); self.finalize_gst_button.setEnabled(True); self.export_gst_detail_excel_button.setEnabled(bool(self._prepared_gst_data and self._prepared_gst_data.detailed_breakdown))
            else: QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}"); self.finalize_gst_button.setEnabled(False)
        except Exception as e: self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True); QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}"); self.finalize_gst_button.setEnabled(False)

    @Slot()
    def _on_finalize_gst_return_clicked(self):
        if not self._saved_draft_gst_return_orm or not self._saved_draft_gst_return_orm.id: QMessageBox.warning(self, "No Draft", "Please prepare and save a draft GST return first."); return
        if self._saved_draft_gst_return_orm.status != "Draft": QMessageBox.information(self, "Already Processed", f"This GST Return (ID: {self._saved_draft_gst_return_orm.id}) is already '{self._saved_draft_gst_return_orm.status}'."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        submission_ref, ok_ref = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Reference No.:")
        if not ok_ref or not submission_ref.strip(): QMessageBox.information(self, "Cancelled", "Submission reference not provided. Finalization cancelled."); return
        submission_date_str, ok_date = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Date (YYYY-MM-DD):", text=python_date.today().isoformat())
        if not ok_date or not submission_date_str.strip(): QMessageBox.information(self, "Cancelled", "Submission date not provided. Finalization cancelled."); return
        try: parsed_submission_date = python_date.fromisoformat(submission_date_str)
        except ValueError: QMessageBox.warning(self, "Invalid Date", "Submission date format is invalid. Please use YYYY-MM-DD."); return
        self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.setText("Finalizing..."); self.save_draft_gst_button.setEnabled(False); self.export_gst_detail_excel_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id=self._saved_draft_gst_return_orm.id, submission_reference=submission_ref.strip(), submission_date=parsed_submission_date, user_id=self.app_core.current_user.id))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_handle_finalize_gst_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule GST finalization task."); self._handle_finalize_gst_result(None)

    @Slot(object)
    def _safe_handle_finalize_gst_result_slot(self, future_arg):
        self._handle_finalize_gst_result(future_arg)

    def _handle_finalize_gst_result(self, future): 
        self.finalize_gst_button.setText("Finalize GST Return"); can_finalize_default = self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft"; can_save_draft_default = self._prepared_gst_data is not None and (not self._saved_draft_gst_return_orm or self._saved_draft_gst_return_orm.status == "Draft"); can_export_detail_default = bool(self._prepared_gst_data and self._prepared_gst_data.detailed_breakdown)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST finalization."); self.finalize_gst_button.setEnabled(can_finalize_default); self.save_draft_gst_button.setEnabled(can_save_draft_default); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                QMessageBox.information(self, "Success", f"GST Return (ID: {result.value.id}) finalized successfully.\nStatus: {result.value.status}.\nSettlement JE ID: {result.value.journal_entry_id or 'N/A'}"); self._saved_draft_gst_return_orm = result.value; self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default) 
                if self._prepared_gst_data: self._prepared_gst_data.status = result.value.status
            else: QMessageBox.warning(self, "Finalization Error", f"Failed to finalize GST Return:\n{', '.join(result.errors)}"); self.finalize_gst_button.setEnabled(can_finalize_default); self.save_draft_gst_button.setEnabled(can_save_draft_default); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default)
        except Exception as e: self.app_core.logger.error(f"Exception handling finalize GST result: {e}", exc_info=True); QMessageBox.critical(self, "Finalization Error", f"An unexpected error occurred: {str(e)}"); self.finalize_gst_button.setEnabled(can_finalize_default); self.save_draft_gst_button.setEnabled(can_save_draft_default); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default)

    @Slot()
    def _on_export_gst_f5_details_excel_clicked(self):
        if not self._prepared_gst_data or not self._prepared_gst_data.detailed_breakdown: QMessageBox.warning(self, "No Data", "Please prepare GST data with details first."); return
        default_filename = f"GST_F5_Details_{self._prepared_gst_data.start_date.strftime('%Y%m%d')}_{self._prepared_gst_data.end_date.strftime('%Y%m%d')}.xlsx"; documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        file_path, _ = QFileDialog.getSaveFileName(self, "Save GST F5 Detail Report (Excel)", os.path.join(documents_path, default_filename), "Excel Files (*.xlsx);;All Files (*)")
        if file_path: 
            self.export_gst_detail_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._prepared_gst_data, "gst_excel_detail"))
            if future: future.add_done_callback(lambda res, fp=file_path: QMetaObject.invokeMethod(self, "_safe_handle_gst_detail_export_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future), Q_ARG(str, fp)))
            else: self.app_core.logger.error("Failed to schedule GST detail export task."); self.export_gst_detail_excel_button.setEnabled(True) 

    @Slot(object, str)
    def _safe_handle_gst_detail_export_result_slot(self, future_arg, file_path_arg: str):
        self._handle_gst_detail_export_result(future_arg, file_path_arg)

    def _handle_gst_detail_export_result(self, future, file_path: str):
        self.export_gst_detail_excel_button.setEnabled(True) 
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST detail export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"GST F5 Detail Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", "Failed to generate GST F5 Detail report bytes.")
        except Exception as e: self.app_core.logger.error(f"Exception handling GST detail export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during GST detail export: {str(e)}")
    
    def _create_financial_statements_tab(self):
        fs_widget = QWidget(); fs_main_layout = QVBoxLayout(fs_widget); fs_group = QGroupBox("Financial Statements"); fs_group_layout = QVBoxLayout(fs_group) 
        controls_layout = QHBoxLayout(); self.fs_params_form = QFormLayout() 
        self.fs_report_type_combo = QComboBox(); self.fs_report_type_combo.addItems(["Balance Sheet", "Profit & Loss Statement", "Trial Balance", "General Ledger", "Income Tax Computation"]); self.fs_params_form.addRow("Report Type:", self.fs_report_type_combo)
        self.fs_fiscal_year_label = QLabel("Fiscal Year:"); self.fs_fiscal_year_combo = QComboBox(); self.fs_fiscal_year_combo.setMinimumWidth(200); self.fs_params_form.addRow(self.fs_fiscal_year_label, self.fs_fiscal_year_combo)
        self.fs_gl_account_label = QLabel("Account for GL:"); self.fs_gl_account_combo = QComboBox(); self.fs_gl_account_combo.setMinimumWidth(250); self.fs_gl_account_combo.setEditable(True)
        completer = QCompleter([f"{item.get('code')} - {item.get('name')}" for item in self._gl_accounts_cache]); completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion); completer.setFilterMode(Qt.MatchFlag.MatchContains); self.fs_gl_account_combo.setCompleter(completer); self.fs_params_form.addRow(self.fs_gl_account_label, self.fs_gl_account_combo)
        self.fs_as_of_date_edit = QDateEdit(QDate.currentDate()); self.fs_as_of_date_edit.setCalendarPopup(True); self.fs_as_of_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("As of Date:", self.fs_as_of_date_edit)
        self.fs_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_start_date_edit.setCalendarPopup(True); self.fs_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("Period Start Date:", self.fs_start_date_edit)
        self.fs_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); self.fs_end_date_edit.setCalendarPopup(True); self.fs_end_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("Period End Date:", self.fs_end_date_edit)
        self.fs_include_zero_balance_check = QCheckBox("Include Zero-Balance Accounts"); self.fs_params_form.addRow(self.fs_include_zero_balance_check) 
        self.fs_include_comparative_check = QCheckBox("Include Comparative Period"); self.fs_params_form.addRow(self.fs_include_comparative_check)
        self.fs_comparative_as_of_date_label = QLabel("Comparative As of Date:"); self.fs_comparative_as_of_date_edit = QDateEdit(QDate.currentDate().addYears(-1)); self.fs_comparative_as_of_date_edit.setCalendarPopup(True); self.fs_comparative_as_of_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_as_of_date_label, self.fs_comparative_as_of_date_edit)
        self.fs_comparative_start_date_label = QLabel("Comparative Start Date:"); self.fs_comparative_start_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_comparative_start_date_edit.setCalendarPopup(True); self.fs_comparative_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_start_date_label, self.fs_comparative_start_date_edit)
        self.fs_comparative_end_date_label = QLabel("Comparative End Date:"); self.fs_comparative_end_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addDays(-QDate.currentDate().day())); self.fs_comparative_end_date_edit.setCalendarPopup(True); self.fs_comparative_end_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_end_date_label, self.fs_comparative_end_date_edit)
        self.fs_dim1_type_label = QLabel("Dimension 1 Type:"); self.fs_dim1_type_combo = QComboBox(); self.fs_dim1_type_combo.addItem("All Types", None); self.fs_dim1_type_combo.setObjectName("fs_dim1_type_combo"); self.fs_params_form.addRow(self.fs_dim1_type_label, self.fs_dim1_type_combo)
        self.fs_dim1_code_label = QLabel("Dimension 1 Code:"); self.fs_dim1_code_combo = QComboBox(); self.fs_dim1_code_combo.addItem("All Codes", None); self.fs_dim1_code_combo.setObjectName("fs_dim1_code_combo"); self.fs_params_form.addRow(self.fs_dim1_code_label, self.fs_dim1_code_combo)
        self.fs_dim2_type_label = QLabel("Dimension 2 Type:"); self.fs_dim2_type_combo = QComboBox(); self.fs_dim2_type_combo.addItem("All Types", None); self.fs_dim2_type_combo.setObjectName("fs_dim2_type_combo"); self.fs_params_form.addRow(self.fs_dim2_type_label, self.fs_dim2_type_combo)
        self.fs_dim2_code_label = QLabel("Dimension 2 Code:"); self.fs_dim2_code_combo = QComboBox(); self.fs_dim2_code_combo.addItem("All Codes", None); self.fs_dim2_code_combo.setObjectName("fs_dim2_code_combo"); self.fs_params_form.addRow(self.fs_dim2_code_label, self.fs_dim2_code_combo)
        controls_layout.addLayout(self.fs_params_form)
        generate_fs_button_layout = QVBoxLayout(); self.generate_fs_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Generate Report"); self.generate_fs_button.clicked.connect(self._on_generate_financial_report_clicked)
        generate_fs_button_layout.addWidget(self.generate_fs_button); generate_fs_button_layout.addStretch(); controls_layout.addLayout(generate_fs_button_layout); controls_layout.addStretch(1); fs_group_layout.addLayout(controls_layout)
        self.fs_display_stack = QStackedWidget(); fs_group_layout.addWidget(self.fs_display_stack, 1)
        self.bs_tree_view = QTreeView(); self.bs_tree_view.setAlternatingRowColors(True); self.bs_tree_view.setHeaderHidden(False); self.bs_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.bs_model = QStandardItemModel(); self.bs_tree_view.setModel(self.bs_model); self.fs_display_stack.addWidget(self.bs_tree_view)
        self.pl_tree_view = QTreeView(); self.pl_tree_view.setAlternatingRowColors(True); self.pl_tree_view.setHeaderHidden(False); self.pl_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.pl_model = QStandardItemModel(); self.pl_tree_view.setModel(self.pl_model); self.fs_display_stack.addWidget(self.pl_tree_view)
        self.tb_table_view = QTableView(); self.tb_table_view.setAlternatingRowColors(True); self.tb_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.tb_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.tb_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tb_table_view.setSortingEnabled(True); self.tb_model = TrialBalanceTableModel(); self.tb_table_view.setModel(self.tb_model); self.fs_display_stack.addWidget(self.tb_table_view)
        gl_widget_container = QWidget(); gl_layout = QVBoxLayout(gl_widget_container); gl_layout.setContentsMargins(0,0,0,0)
        self.gl_summary_label_account = QLabel("Account: N/A"); self.gl_summary_label_account.setStyleSheet("font-weight: bold;"); self.gl_summary_label_period = QLabel("Period: N/A"); self.gl_summary_label_ob = QLabel("Opening Balance: 0.00"); gl_summary_header_layout = QHBoxLayout(); gl_summary_header_layout.addWidget(self.gl_summary_label_account); gl_summary_header_layout.addStretch(); gl_summary_header_layout.addWidget(self.gl_summary_label_period); gl_layout.addLayout(gl_summary_header_layout); gl_layout.addWidget(self.gl_summary_label_ob)
        self.gl_table_view = QTableView(); self.gl_table_view.setAlternatingRowColors(True); self.gl_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.gl_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.gl_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.gl_table_view.setSortingEnabled(True); self.gl_model = GeneralLedgerTableModel(); self.gl_table_view.setModel(self.gl_model); gl_layout.addWidget(self.gl_table_view)
        self.gl_summary_label_cb = QLabel("Closing Balance: 0.00"); self.gl_summary_label_cb.setAlignment(Qt.AlignmentFlag.AlignRight); gl_layout.addWidget(self.gl_summary_label_cb)
        self.fs_display_stack.addWidget(gl_widget_container); self.gl_widget_container = gl_widget_container 
        
        self.tax_comp_tree_view = QTreeView(); self.tax_comp_tree_view.setAlternatingRowColors(True); self.tax_comp_tree_view.setHeaderHidden(False); self.tax_comp_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tax_comp_model = QStandardItemModel(); self.tax_comp_tree_view.setModel(self.tax_comp_model); self.fs_display_stack.addWidget(self.tax_comp_tree_view)

        export_button_layout = QHBoxLayout(); self.export_pdf_button = QPushButton("Export to PDF"); self.export_pdf_button.setEnabled(False); self.export_pdf_button.clicked.connect(lambda: self._on_export_report_clicked("pdf")); self.export_excel_button = QPushButton("Export to Excel"); self.export_excel_button.setEnabled(False); self.export_excel_button.clicked.connect(lambda: self._on_export_report_clicked("excel")); export_button_layout.addStretch(); export_button_layout.addWidget(self.export_pdf_button); export_button_layout.addWidget(self.export_excel_button); fs_group_layout.addLayout(export_button_layout)
        fs_main_layout.addWidget(fs_group); self.tab_widget.addTab(fs_widget, "Financial Statements")
        self.fs_report_type_combo.currentTextChanged.connect(self._on_fs_report_type_changed)
        self.fs_include_comparative_check.stateChanged.connect(self._on_comparative_check_changed)
        self.fs_dim1_type_combo.currentIndexChanged.connect(lambda index, tc=self.fs_dim1_type_combo, cc=self.fs_dim1_code_combo: self._on_dimension_type_selected(tc, cc))
        self.fs_dim2_type_combo.currentIndexChanged.connect(lambda index, tc=self.fs_dim2_type_combo, cc=self.fs_dim2_code_combo: self._on_dimension_type_selected(tc, cc))
        self._on_fs_report_type_changed(self.fs_report_type_combo.currentText()) 

    async def _load_fs_combo_data(self):
        await self._load_gl_accounts_for_combo()
        await self._load_fiscal_years_for_combo()

    @Slot(str)
    def _on_fs_report_type_changed(self, report_type: str):
        is_bs = (report_type == "Balance Sheet"); is_pl = (report_type == "Profit & Loss Statement"); is_gl = (report_type == "General Ledger"); is_tb = (report_type == "Trial Balance"); is_tax = (report_type == "Income Tax Computation")
        self.fs_as_of_date_edit.setVisible(is_bs or is_tb); self.fs_start_date_edit.setVisible(is_pl or is_gl); self.fs_end_date_edit.setVisible(is_pl or is_gl)
        self.fs_fiscal_year_combo.setVisible(is_tax); self.fs_fiscal_year_label.setVisible(is_tax)
        self.fs_gl_account_combo.setVisible(is_gl); self.fs_gl_account_label.setVisible(is_gl); self.fs_include_zero_balance_check.setVisible(is_bs); self.fs_include_comparative_check.setVisible(is_bs or is_pl)
        for w in [self.fs_dim1_type_label, self.fs_dim1_type_combo, self.fs_dim1_code_label, self.fs_dim1_code_combo, self.fs_dim2_type_label, self.fs_dim2_type_combo, self.fs_dim2_code_label, self.fs_dim2_code_combo]: w.setVisible(is_gl)
        if is_gl and self.fs_dim1_type_combo.count() <= 1 : schedule_task_from_qt(self._load_dimension_types())
        self._on_comparative_check_changed(self.fs_include_comparative_check.checkState().value) 
        if is_gl: self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
        elif is_bs: self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
        elif is_pl: self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
        elif is_tb: self.fs_display_stack.setCurrentWidget(self.tb_table_view)
        elif is_tax: self.fs_display_stack.setCurrentWidget(self.tax_comp_tree_view)
        self._clear_current_financial_report_display(); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
    async def _load_dimension_types(self):
        if not self.app_core.dimension_service: self.app_core.logger.error("DimensionService not available."); return
        try:
            dim_types = await self.app_core.dimension_service.get_distinct_dimension_types(); json_data = json.dumps(dim_types)
            QMetaObject.invokeMethod(self, "_populate_dimension_types_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e: self.app_core.logger.error(f"Error loading dimension types: {e}", exc_info=True)
    @Slot(str)
    def _populate_dimension_types_slot(self, dim_types_json_str: str):
        try: dim_types = json.loads(dim_types_json_str)
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse dimension types JSON."); return
        self._dimension_types_cache = ["All Types"] + dim_types 
        for combo in [self.fs_dim1_type_combo, self.fs_dim2_type_combo]:
            current_data = combo.currentData(); combo.clear(); combo.addItem("All Types", None)
            for dt in dim_types: combo.addItem(dt, dt)
            idx = combo.findData(current_data); 
            if idx != -1: combo.setCurrentIndex(idx)
            else: combo.setCurrentIndex(0) 
        self._on_dimension_type_selected(self.fs_dim1_type_combo, self.fs_dim1_code_combo); self._on_dimension_type_selected(self.fs_dim2_type_combo, self.fs_dim2_code_combo)
    @Slot(QComboBox, QComboBox) 
    def _on_dimension_type_selected(self, type_combo: QComboBox, code_combo: QComboBox):
        selected_type_str = type_combo.currentData() 
        if selected_type_str: schedule_task_from_qt(self._load_dimension_codes_for_type(selected_type_str, code_combo.objectName() or ""))
        else: code_combo.clear(); code_combo.addItem("All Codes", None)
    async def _load_dimension_codes_for_type(self, dim_type_str: str, target_code_combo_name: str):
        if not self.app_core.dimension_service: self.app_core.logger.error("DimensionService not available."); return
        try:
            dimensions: List[Dimension] = await self.app_core.dimension_service.get_dimensions_by_type(dim_type_str)
            dim_codes_data = [{"id": d.id, "code": d.code, "name": d.name} for d in dimensions]; self._dimension_codes_cache[dim_type_str] = dim_codes_data
            json_data = json.dumps(dim_codes_data, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dimension_codes_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data), Q_ARG(str, target_code_combo_name))
        except Exception as e: self.app_core.logger.error(f"Error loading dimension codes for type '{dim_type_str}': {e}", exc_info=True)
    @Slot(str, str)
    def _populate_dimension_codes_slot(self, dim_codes_json_str: str, target_code_combo_name: str):
        target_combo: Optional[QComboBox] = self.findChild(QComboBox, target_code_combo_name)
        if not target_combo: self.app_core.logger.error(f"Target code combo '{target_code_combo_name}' not found."); return
        current_data = target_combo.currentData(); target_combo.clear(); target_combo.addItem("All Codes", None) 
        try:
            dim_codes = json.loads(dim_codes_json_str, object_hook=json_date_hook)
            for dc in dim_codes: target_combo.addItem(f"{dc['code']} - {dc['name']}", dc['id'])
            idx = target_combo.findData(current_data)
            if idx != -1: target_combo.setCurrentIndex(idx)
            else: target_combo.setCurrentIndex(0) 
        except json.JSONDecodeError: self.app_core.logger.error(f"Failed to parse dim codes JSON for {target_code_combo_name}")
    @Slot(int)
    def _on_comparative_check_changed(self, state: int):
        is_checked = (state == Qt.CheckState.Checked.value); report_type = self.fs_report_type_combo.currentText(); is_bs = (report_type == "Balance Sheet"); is_pl = (report_type == "Profit & Loss Statement")
        self.fs_comparative_as_of_date_label.setVisible(is_bs and is_checked); self.fs_comparative_as_of_date_edit.setVisible(is_bs and is_checked)
        self.fs_comparative_start_date_label.setVisible(is_pl and is_checked); self.fs_comparative_start_date_edit.setVisible(is_pl and is_checked)
        self.fs_comparative_end_date_label.setVisible(is_pl and is_checked); self.fs_comparative_end_date_edit.setVisible(is_pl and is_checked)
    async def _load_gl_accounts_for_combo(self):
        if not self.app_core.chart_of_accounts_manager: self.app_core.logger.error("ChartOfAccountsManager not available for GL account combo."); return
        try:
            accounts_orm: List[Account] = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            self._gl_accounts_cache = [{"id": acc.id, "code": acc.code, "name": acc.name} for acc in accounts_orm]
            accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_gl_account_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, accounts_json))
        except Exception as e: self.app_core.logger.error(f"Error loading accounts for GL combo: {e}", exc_info=True); QMessageBox.warning(self, "Account Load Error", "Could not load accounts for General Ledger selection.")
    @Slot(str)
    def _populate_gl_account_combo_slot(self, accounts_json_str: str):
        self.fs_gl_account_combo.clear()
        try:
            accounts_data = json.loads(accounts_json_str); self._gl_accounts_cache = accounts_data if accounts_data else []
            self.fs_gl_account_combo.addItem("-- Select Account --", 0) 
            for acc_data in self._gl_accounts_cache: self.fs_gl_account_combo.addItem(f"{acc_data['code']} - {acc_data['name']}", acc_data['id'])
            if isinstance(self.fs_gl_account_combo.completer(), QCompleter): self.fs_gl_account_combo.completer().setModel(self.fs_gl_account_combo.model())
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse accounts JSON for GL combo."); self.fs_gl_account_combo.addItem("Error loading accounts", 0)

    async def _load_fiscal_years_for_combo(self):
        if not self.app_core.fiscal_period_manager: self.app_core.logger.error("FiscalPeriodManager not available."); return
        try:
            fy_orms = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            self._fiscal_years_cache = [FiscalYearData.model_validate(fy) for fy in fy_orms]
            fy_json = json.dumps([fy.model_dump(mode='json') for fy in self._fiscal_years_cache])
            QMetaObject.invokeMethod(self, "_populate_fiscal_years_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, fy_json))
        except Exception as e: self.app_core.logger.error(f"Error loading fiscal years for combo: {e}", exc_info=True)

    @Slot(str)
    def _populate_fiscal_years_combo_slot(self, fy_json_str: str):
        self.fs_fiscal_year_combo.clear()
        try:
            fy_dicts = json.loads(fy_json_str, object_hook=json_date_hook)
            self._fiscal_years_cache = [FiscalYearData.model_validate(fy) for fy in fy_dicts]
            if not self._fiscal_years_cache: self.fs_fiscal_year_combo.addItem("No fiscal years found", 0); return
            for fy_data in sorted(self._fiscal_years_cache, key=lambda fy: fy.start_date, reverse=True):
                self.fs_fiscal_year_combo.addItem(f"{fy_data.year_name} ({fy_data.start_date.strftime('%d/%m/%Y')} - {fy_data.end_date.strftime('%d/%m/%Y')})", fy_data.id)
        except Exception as e: self.app_core.logger.error(f"Error parsing fiscal years for combo: {e}"); self.fs_fiscal_year_combo.addItem("Error loading", 0)

    def _clear_current_financial_report_display(self):
        self._current_financial_report_data = None; current_view = self.fs_display_stack.currentWidget()
        if isinstance(current_view, QTreeView): model = current_view.model(); 
        if isinstance(model, QStandardItemModel): model.clear() 
        elif isinstance(current_view, QTableView): model = current_view.model(); 
        if hasattr(model, 'update_data'): model.update_data([]) 
        elif current_view == self.gl_widget_container : self.gl_model.update_data({}); self.gl_summary_label_account.setText("Account: N/A"); self.gl_summary_label_period.setText("Period: N/A"); self.gl_summary_label_ob.setText("Opening Balance: 0.00"); self.gl_summary_label_cb.setText("Closing Balance: 0.00")
    
    @Slot()
    def _on_generate_financial_report_clicked(self):
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        self._clear_current_financial_report_display(); self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating..."); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
        coro: Optional[Any] = None; comparative_date_bs: Optional[python_date] = None; comparative_start_pl: Optional[python_date] = None; comparative_end_pl: Optional[python_date] = None; include_zero_bal_bs: bool = False
        dim1_id_val = self.fs_dim1_code_combo.currentData() if self.fs_dim1_type_label.isVisible() else None ; dim2_id_val = self.fs_dim2_code_combo.currentData() if self.fs_dim2_type_label.isVisible() else None
        dimension1_id = int(dim1_id_val) if dim1_id_val and dim1_id_val !=0 else None; dimension2_id = int(dim2_id_val) if dim2_id_val and dim2_id_val !=0 else None
        if self.fs_include_comparative_check.isVisible() and self.fs_include_comparative_check.isChecked():
            if report_type == "Balance Sheet": comparative_date_bs = self.fs_comparative_as_of_date_edit.date().toPython()
            elif report_type == "Profit & Loss Statement":
                comparative_start_pl = self.fs_comparative_start_date_edit.date().toPython(); comparative_end_pl = self.fs_comparative_end_date_edit.date().toPython()
                if comparative_start_pl and comparative_end_pl and comparative_start_pl > comparative_end_pl: QMessageBox.warning(self, "Date Error", "Comparative start date cannot be after comparative end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
        if report_type == "Balance Sheet": as_of_date_val = self.fs_as_of_date_edit.date().toPython(); include_zero_bal_bs = self.fs_include_zero_balance_check.isChecked() if self.fs_include_zero_balance_check.isVisible() else False; coro = self.app_core.financial_statement_generator.generate_balance_sheet(as_of_date_val, comparative_date=comparative_date_bs, include_zero_balances=include_zero_bal_bs)
        elif report_type == "Profit & Loss Statement": 
            start_date_val = self.fs_start_date_edit.date().toPython(); end_date_val = self.fs_end_date_edit.date().toPython()
            if start_date_val > end_date_val: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_profit_loss(start_date_val, end_date_val, comparative_start=comparative_start_pl, comparative_end=comparative_end_pl)
        elif report_type == "Trial Balance": as_of_date_val = self.fs_as_of_date_edit.date().toPython(); coro = self.app_core.financial_statement_generator.generate_trial_balance(as_of_date_val)
        elif report_type == "General Ledger":
            account_id = self.fs_gl_account_combo.currentData(); 
            if not isinstance(account_id, int) or account_id == 0: QMessageBox.warning(self, "Selection Error", "Please select a valid account for the General Ledger report."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            start_date_val = self.fs_start_date_edit.date().toPython(); end_date_val = self.fs_end_date_edit.date().toPython() 
            if start_date_val > end_date_val: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for General Ledger."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_general_ledger(account_id, start_date_val, end_date_val, dimension1_id, dimension2_id)
        elif report_type == "Income Tax Computation":
            fy_id = self.fs_fiscal_year_combo.currentData()
            if not isinstance(fy_id, int) or fy_id == 0: QMessageBox.warning(self, "Selection Error", "Please select a Fiscal Year for the Tax Computation report."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            fy_data_obj = next((fy for fy in self._fiscal_years_cache if fy.id == fy_id), None)
            if not fy_data_obj: QMessageBox.warning(self, "Data Error", f"Could not find data for selected fiscal year ID {fy_id}."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_income_tax_computation(fy_data_obj) # Pass DTO

        future_obj: Optional[Any] = None ; 
        if coro: future_obj = schedule_task_from_qt(coro)
        if future_obj: future_obj.add_done_callback( lambda res: QMetaObject.invokeMethod( self, "_safe_handle_financial_report_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future_obj)))
        else: self.app_core.logger.error(f"Failed to schedule report generation for {report_type}."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); self._handle_financial_report_result(None) 
    
    @Slot(object)
    def _safe_handle_financial_report_result_slot(self, future_arg): self._handle_financial_report_result(future_arg)
    
    def _handle_financial_report_result(self, future):
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); self.export_pdf_button.setEnabled(False) ; self.export_excel_button.setEnabled(False); self._current_financial_report_data = None
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try:
            report_data: Optional[Dict[str, Any]] = future.result()
            if report_data: self._current_financial_report_data = report_data; self._display_financial_report(report_data); self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
            else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e: self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True); QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")

    def _populate_balance_sheet_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); has_comparative = bool(report_data.get('comparative_date')); headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(f"Comparative ({report_data.get('comparative_date','Prev').strftime('%d/%m/%Y') if isinstance(report_data.get('comparative_date'), python_date) else 'Prev'})")
        model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}"); amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance'))); amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""; 
                    if comparative_accounts: comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None); comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str); comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)
        for section_key, section_title_display in [('assets', "Assets"), ('liabilities', "Liabilities"), ('equity', "Equity")]:
            section_data = report_data.get(section_key); 
            if not section_data or not isinstance(section_data, dict): continue
            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font); empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); header_row = [section_header_item, empty_amount_item]; 
            if has_comparative: header_row.append(QStandardItem("")); root_node.appendRow(header_row)
            add_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))
            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font); total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items = [total_desc_item, total_amount_item]; 
            if has_comparative: comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items); 
            if section_key != 'equity': root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else []))
        if 'total_liabilities_equity' in report_data:
            root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])); tle_desc = QStandardItem("Total Liabilities & Equity"); tle_desc.setFont(bold_font); tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('total_liabilities_equity'))); tle_amount.setFont(bold_font); tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); tle_row = [tle_desc, tle_amount]; 
            if has_comparative: comp_tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_total_liabilities_equity'))); comp_tle_amount.setFont(bold_font); comp_tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); tle_row.append(comp_tle_amount)
            root_node.appendRow(tle_row)
        if report_data.get('is_balanced') is False: warning_item = QStandardItem("Warning: Balance Sheet is out of balance!"); warning_item.setForeground(QColor("red")); warning_item.setFont(bold_font); warning_row = [warning_item, QStandardItem("")]; 
        if has_comparative: warning_row.append(QStandardItem("")); root_node.appendRow(warning_row)
    
    def _populate_profit_loss_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); has_comparative = bool(report_data.get('comparative_start')); comp_header_text = "Comparative"; 
        if has_comparative and report_data.get('comparative_start') and report_data.get('comparative_end'): comp_start_str = report_data['comparative_start'].strftime('%d/%m/%y'); comp_end_str = report_data['comparative_end'].strftime('%d/%m/%y'); comp_header_text = f"Comp. ({comp_start_str}-{comp_end_str})"
        headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(comp_header_text); 
        model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_pl_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}"); amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance'))); amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""; 
                    if comparative_accounts: comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None); comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str); comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)
        for section_key, section_title_display in [('revenue', "Revenue"), ('expenses', "Operating Expenses")]: 
            section_data = report_data.get(section_key); 
            if not section_data or not isinstance(section_data, dict): continue
            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font); empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); header_row = [section_header_item, empty_amount_item]; 
            if has_comparative: header_row.append(QStandardItem("")); root_node.appendRow(header_row)
            add_pl_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))
            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font); total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items = [total_desc_item, total_amount_item]; 
            if has_comparative: comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items); root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])) 
        if 'net_profit' in report_data:
            np_desc = QStandardItem("Net Profit / (Loss)"); np_desc.setFont(bold_font); np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('net_profit'))); np_amount.setFont(bold_font); np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); np_row = [np_desc, np_amount]; 
            if has_comparative: comp_np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_net_profit'))); comp_np_amount.setFont(bold_font); comp_np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); np_row.append(comp_np_amount)
            root_node.appendRow(np_row)

    def _populate_tax_computation_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); headers = ["Description", "Amount"]; model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_row(parent: QStandardItem, desc: str, amt: Optional[Decimal] = None, is_bold: bool = False, is_underline: bool = False):
            desc_item = QStandardItem(desc); amt_item = QStandardItem(self._format_decimal_for_display(amt) if amt is not None else ""); amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if is_bold: desc_item.setFont(bold_font); amt_item.setFont(bold_font)
            if is_underline: desc_item.setData(QColor('black'), Qt.ItemDataRole.ForegroundRole); amt_item.setData(QColor('black'), Qt.ItemDataRole.ForegroundRole) # This doesn't create underline, just for concept
            parent.appendRow([desc_item, amt_item])
        
        add_row(root_node, "Net Profit Before Tax", report_data.get('net_profit_before_tax'), is_bold=True)
        add_row(root_node, "") # Spacer
        
        add_row(root_node, "Add: Non-Deductible Expenses", is_bold=True)
        for adj in report_data.get('add_back_adjustments', []): add_row(root_node, f"  {adj['name']}", adj['amount'])
        add_row(root_node, "Total Additions", report_data.get('total_add_back'), is_underline=True)
        add_row(root_node, "") # Spacer
        
        add_row(root_node, "Less: Non-Taxable Income", is_bold=True)
        for adj in report_data.get('less_adjustments', []): add_row(root_node, f"  {adj['name']}", adj['amount'])
        add_row(root_node, "Total Subtractions", report_data.get('total_less'), is_underline=True)
        add_row(root_node, "") # Spacer

        add_row(root_node, "Chargeable Income", report_data.get('chargeable_income'), is_bold=True)
        add_row(root_node, f"Tax at {report_data.get('tax_rate', 0):.2f}%", is_bold=False) # Description only
        add_row(root_node, "Estimated Tax Payable", report_data.get('estimated_tax'), is_bold=True)


    def _display_financial_report(self, report_data: Dict[str, Any]):
        report_title = report_data.get('title', '')
        if report_title == "Balance Sheet":
            self.fs_display_stack.setCurrentWidget(self.bs_tree_view); self._populate_balance_sheet_model(self.bs_model, report_data)
            self.bs_tree_view.expandAll(); [self.bs_tree_view.resizeColumnToContents(i) for i in range(self.bs_model.columnCount())]
        elif report_title == "Profit & Loss Statement":
            self.fs_display_stack.setCurrentWidget(self.pl_tree_view); self._populate_profit_loss_model(self.pl_model, report_data)
            self.pl_tree_view.expandAll(); [self.pl_tree_view.resizeColumnToContents(i) for i in range(self.pl_model.columnCount())]
        elif report_title == "Trial Balance":
            self.fs_display_stack.setCurrentWidget(self.tb_table_view); self.tb_model.update_data(report_data)
            [self.tb_table_view.resizeColumnToContents(i) for i in range(self.tb_model.columnCount())]
        elif report_title == "General Ledger": 
            self.fs_display_stack.setCurrentWidget(self.gl_widget_container); self.gl_model.update_data(report_data)
            gl_summary_data = self.gl_model.get_report_summary(); self.gl_summary_label_account.setText(f"Account: {gl_summary_data['account_name']}"); self.gl_summary_label_period.setText(gl_summary_data['period_description'])
            self.gl_summary_label_ob.setText(f"Opening Balance: {self._format_decimal_for_display(gl_summary_data['opening_balance'], show_blank_for_zero=False)}"); self.gl_summary_label_cb.setText(f"Closing Balance: {self._format_decimal_for_display(gl_summary_data['closing_balance'], show_blank_for_zero=False)}")
            [self.gl_table_view.resizeColumnToContents(i) for i in range(self.gl_model.columnCount())]
        elif report_title == "Income Tax Computation":
            self.fs_display_stack.setCurrentWidget(self.tax_comp_tree_view); self._populate_tax_computation_model(self.tax_comp_model, report_data)
            self.tax_comp_tree_view.expandAll(); [self.tax_comp_tree_view.resizeColumnToContents(i) for i in range(self.tax_comp_model.columnCount())]
        else: self._clear_current_financial_report_display(); self.app_core.logger.warning(f"Unhandled report title '{report_title}' for specific display."); QMessageBox.warning(self, "Display Error", f"Display format for '{report_title}' is not fully implemented in this view.")

    @Slot(str)
    def _on_export_report_clicked(self, format_type: str):
        if not self._current_financial_report_data: QMessageBox.warning(self, "No Report", "Please generate a report first before exporting."); return
        report_title_str = self._current_financial_report_data.get('title', 'FinancialReport')
        if not isinstance(report_title_str, str): report_title_str = "FinancialReport"
        default_filename = f"{report_title_str.replace(' ', '_').replace('&', 'And').replace('/', '-').replace(':', '')}_{python_date.today().strftime('%Y%m%d')}.{format_type}"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation); 
        if not documents_path: documents_path = os.path.expanduser("~") 
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {format_type.upper()} Report", os.path.join(documents_path, default_filename), f"{format_type.upper()} Files (*.{format_type});;All Files (*)")
        if file_path: 
            self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._current_financial_report_data, format_type)); 
            if future: future.add_done_callback( lambda res, fp=file_path, ft=format_type: QMetaObject.invokeMethod( self, "_safe_handle_export_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future), Q_ARG(str, fp), Q_ARG(str, ft)))
            else: self.app_core.logger.error("Failed to schedule report export task."); self._handle_export_result(None, file_path, format_type) 
    @Slot(object, str, str)
    def _safe_handle_export_result_slot(self, future_arg, file_path_arg: str, format_type_arg: str): self._handle_export_result(future_arg, file_path_arg, format_type_arg)
    def _handle_export_result(self, future, file_path: str, format_type: str):
        self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", f"Failed to generate report bytes for {format_type.upper()}.")
        except Exception as e: self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")

```

# app/ui/reports/general_ledger_table_model.py
```py
# app/ui/reports/general_ledger_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date as python_date

class GeneralLedgerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]
        self._transactions: List[Dict[str, Any]] = []
        self._opening_balance = Decimal(0)
        self._closing_balance = Decimal(0)
        self._account_name = ""
        self._period_description = ""

        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +2 for opening and closing balance rows if we display them in table
        # For now, let's assume they are displayed outside the table by the widget
        return len(self._transactions)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal], show_zero_as_blank: bool = True) -> str:
        if value is None: return ""
        if show_zero_as_blank and value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._transactions)): return None
            
        txn = self._transactions[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: # Date
                raw_date = txn.get("date")
                return raw_date.strftime('%d/%m/%Y') if isinstance(raw_date, python_date) else str(raw_date)
            if col == 1: return txn.get("entry_no", "") # Entry No.
            if col == 2: # Description
                desc = txn.get("je_description", "")
                line_desc = txn.get("line_description", "")
                return f"{desc} // {line_desc}" if desc and line_desc else (desc or line_desc)
            if col == 3: return self._format_decimal_for_display(txn.get("debit"), True)  # Debit
            if col == 4: return self._format_decimal_for_display(txn.get("credit"), True) # Credit
            if col == 5: return self._format_decimal_for_display(txn.get("balance"), False) # Balance (show zero)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [3, 4, 5]: # Debit, Credit, Balance
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._transactions = report_data.get('transactions', [])
        self._opening_balance = report_data.get('opening_balance', Decimal(0))
        self._closing_balance = report_data.get('closing_balance', Decimal(0))
        self._account_name = f"{report_data.get('account_code','')} - {report_data.get('account_name','')}"
        start = report_data.get('start_date')
        end = report_data.get('end_date')
        self._period_description = f"For {start.strftime('%d/%m/%Y') if start else ''} to {end.strftime('%d/%m/%Y') if end else ''}"
        self.endResetModel()

    def get_report_summary(self) -> Dict[str, Any]:
        return {
            "account_name": self._account_name,
            "period_description": self._period_description,
            "opening_balance": self._opening_balance,
            "closing_balance": self._closing_balance
        }

```

# app/ui/reports/trial_balance_table_model.py
```py
# app/ui/reports/trial_balance_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal

class TrialBalanceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Account Code", "Account Name", "Debit", "Credit"]
        self._debit_accounts: List[Dict[str, Any]] = []
        self._credit_accounts: List[Dict[str, Any]] = []
        self._totals: Dict[str, Decimal] = {"debits": Decimal(0), "credits": Decimal(0)}
        self._is_balanced: bool = False
        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +1 for the totals row
        return len(self._debit_accounts) + len(self._credit_accounts) + 1 

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None or value == Decimal(0): return "" # Show blank for zero in TB lines
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        num_debit_accounts = len(self._debit_accounts)
        num_credit_accounts = len(self._credit_accounts)

        # Totals Row
        if row == num_debit_accounts + num_credit_accounts:
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 1: return "TOTALS"
                if col == 2: return f"{self._totals['debits']:,.2f}"
                if col == 3: return f"{self._totals['credits']:,.2f}"
                return ""
            elif role == Qt.ItemDataRole.FontRole:
                from PySide6.QtGui import QFont
                font = QFont(); font.setBold(True); return font
            elif role == Qt.ItemDataRole.TextAlignmentRole and col in [2,3]:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None

        # Debit Accounts
        if row < num_debit_accounts:
            account = self._debit_accounts[row]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return self._format_decimal_for_display(account.get("balance"))
                if col == 3: return "" # Credit column is blank for debit accounts
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 2:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
        
        # Credit Accounts
        credit_row_index = row - num_debit_accounts
        if credit_row_index < num_credit_accounts:
            account = self._credit_accounts[credit_row_index]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return "" # Debit column is blank for credit accounts
                if col == 3: return self._format_decimal_for_display(account.get("balance"))
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 3:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
            
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._debit_accounts = report_data.get('debit_accounts', [])
        self._credit_accounts = report_data.get('credit_accounts', [])
        self._totals["debits"] = report_data.get('total_debits', Decimal(0))
        self._totals["credits"] = report_data.get('total_credits', Decimal(0))
        self._is_balanced = report_data.get('is_balanced', False)
        self.endResetModel()

    def get_balance_status(self) -> str:
        return "Balanced" if self._is_balanced else f"Out of Balance by: {abs(self._totals['debits'] - self._totals['credits']):,.2f}"

```

# app/ui/shared/__init__.py
```py
# app/ui/shared/__init__.py
from .product_search_dialog import ProductSearchDialog 
    
__all__ = [
    "ProductSearchDialog",
]

```

# app/ui/shared/product_search_dialog.py
```py
# app/ui/shared/product_search_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QTableView, QHeaderView, QAbstractItemView, QComboBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG, QModelIndex
from PySide6.QtGui import QIcon # QAction not directly used here, but good to have common imports
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.products.product_table_model import ProductTableModel # Reusing existing model
from app.utils.pydantic_models import ProductSummaryData
from app.common.enums import ProductTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice


class ProductSearchDialog(QDialog):
    product_selected = Signal(object)  # Emits a ProductSummaryData dictionary

    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.setWindowTitle("Product/Service Search")
        self.setMinimumSize(800, 500)
        self.setModal(True)

        self.icon_path_prefix = "resources/icons/"
        try:
            import app.resources_rc
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self._init_ui()
        self._connect_signals()
        
        # Initial load with default filters (all active products/services)
        QTimer.singleShot(0, self._on_search_clicked)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Filter Area
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search Term:"))
        self.search_term_edit = QLineEdit()
        self.search_term_edit.setPlaceholderText("Code, Name, Description...")
        filter_layout.addWidget(self.search_term_edit)

        filter_layout.addWidget(QLabel("Type:"))
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItem("All Types", None) # User data is None
        for pt_enum in ProductTypeEnum:
            self.product_type_combo.addItem(pt_enum.value, pt_enum) # User data is the Enum member
        filter_layout.addWidget(self.product_type_combo)
        
        self.search_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Search")
        filter_layout.addWidget(self.search_button)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Results Table
        self.results_table = QTableView()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSortingEnabled(True)

        self.table_model = ProductTableModel() # Reusing the existing model
        self.results_table.setModel(self.table_model)
        
        # Hide ID column if present in model, adjust other columns
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.results_table.setColumnHidden(id_col_idx, True)
        
        header = self.results_table.horizontalHeader()
        for i in range(self.table_model.columnCount()): # Default to contents
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Stretch "Name" column
        if "Name" in self.table_model._headers:
            name_col_model_idx = self.table_model._headers.index("Name")
            visible_name_idx = name_col_model_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_model_idx and self.results_table.isColumnHidden(self.table_model._headers.index("ID")):
                 visible_name_idx -=1
            if not self.results_table.isColumnHidden(name_col_model_idx):
                header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)


        main_layout.addWidget(self.results_table)

        # Dialog Buttons
        self.button_box = QDialogButtonBox()
        self.select_button = self.button_box.addButton("Select Product", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.select_button.setEnabled(False) # Initially disabled
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.search_button.clicked.connect(self._on_search_clicked)
        self.search_term_edit.returnPressed.connect(self._on_search_clicked)
        self.product_type_combo.currentIndexChanged.connect(self._on_search_clicked) # Auto-search on type change

        self.results_table.selectionModel().selectionChanged.connect(self._update_select_button_state)
        self.results_table.doubleClicked.connect(self._on_accept_selection)
        
        self.select_button.clicked.connect(self._on_accept_selection)
        self.button_box.rejected.connect(self.reject)

    @Slot()
    def _on_search_clicked(self):
        # Disable search button while searching to prevent multiple clicks
        self.search_button.setEnabled(False)
        schedule_task_from_qt(self._perform_search()).add_done_callback(
            lambda _: self.search_button.setEnabled(True) # Re-enable after search completes
        )

    async def _perform_search(self):
        if not self.app_core.product_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Product Manager not available."))
            return

        search_term = self.search_term_edit.text().strip() or None
        product_type_filter_enum: Optional[ProductTypeEnum] = self.product_type_combo.currentData()

        try:
            result: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(
                active_only=True,  # Search dialog should only show active products
                product_type_filter=product_type_filter_enum,
                search_term=search_term,
                page=1,
                page_size=100  # Limit results in search dialog
            )
            if result.is_success:
                products_list = result.value if result.value is not None else []
                products_json = json.dumps([p.model_dump() for p in products_list], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, products_json))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Search Error"), Q_ARG(str, f"Failed to search products:\n{', '.join(result.errors)}"))
        except Exception as e:
            self.app_core.logger.error(f"Error performing product search: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Search Error"), Q_ARG(str, f"An unexpected error occurred: {e}"))


    @Slot(str)
    def _update_table_slot(self, products_json_str: str):
        try:
            products_dict_list = json.loads(products_json_str, object_hook=json_date_hook)
            product_summaries = [ProductSummaryData.model_validate(p) for p in products_dict_list]
            self.table_model.update_data(product_summaries)
            if not product_summaries:
                QMessageBox.information(self, "Search Results", "No products found matching your criteria.")
        except Exception as e:
            self.app_core.logger.error(f"Error updating product search table: {e}", exc_info=True)
            QMessageBox.critical(self, "Display Error", f"Could not display search results: {e}")
        finally:
            self._update_select_button_state()


    @Slot()
    def _update_select_button_state(self):
        self.select_button.setEnabled(self.results_table.selectionModel().hasSelection())

    @Slot()
    def _on_accept_selection(self):
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection Needed", "Please select a product from the list.")
            return

        selected_row_index = selected_rows[0].row()
        product_id = self.table_model.get_product_id_at_row(selected_row_index)
        
        if product_id is None:
            QMessageBox.warning(self, "Selection Error", "Could not retrieve product details for selection.")
            return

        # Find the full ProductSummaryData from the model's internal data
        selected_product_summary: Optional[ProductSummaryData] = None
        if 0 <= selected_row_index < len(self.table_model._data): # Access internal data (common pattern for table models)
            selected_product_summary = self.table_model._data[selected_row_index]
        
        if selected_product_summary:
            self.product_selected.emit(selected_product_summary.model_dump(mode='json')) # Emit as dict
            self.accept()
        else:
            QMessageBox.warning(self, "Selection Error", "Selected product data could not be fully retrieved.")

    def open(self) -> int:
        # Clear previous search results when opening
        self.table_model.update_data([])
        self.search_term_edit.clear()
        self.product_type_combo.setCurrentIndex(0) # "All Types"
        # Optionally trigger a default search or wait for user interaction
        # QTimer.singleShot(0, self._on_search_clicked) # If you want to load all active initially
        return super().open()


```

# app/ui/accounting/journal_entry_table_model.py
```py
# app/ui/accounting/journal_entry_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date # Alias to avoid conflict with Qt's QDate

class JournalEntryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None, parent=None):
        super().__init__(parent)
        # Headers match the expected dictionary keys from JournalEntryManager.get_journal_entries_for_listing
        self._headers = ["ID", "Entry No.", "Date", "Description", "Type", "Total", "Status"]
        self._data: List[Dict[str, Any]] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): # This model is flat, no children
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        entry_summary = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_') # "Entry No." -> "entry_no"
            
            if header_key == "id": return str(entry_summary.get("id", "")) # Display ID as string
            if header_key == "entry_no": return entry_summary.get("entry_no", "")
            if header_key == "date": 
                raw_date = entry_summary.get("date")
                if isinstance(raw_date, python_date): return raw_date.strftime('%d/%m/%Y')
                # Assuming date might come as string from JSON, ensure it's parsed if needed by json_date_hook earlier
                if isinstance(raw_date, str): # Should have been converted by json_date_hook
                     try: return python_date.fromisoformat(raw_date).strftime('%d/%m/%Y')
                     except ValueError: return raw_date # Fallback
                return ""
            if header_key == "description": return entry_summary.get("description", "")
            if header_key == "type": return entry_summary.get("type", "")
            if header_key == "total": # Corresponds to "total_amount" key in data dict
                val = entry_summary.get("total_amount")
                try: return f"{Decimal(str(val) if val is not None else '0'):,.2f}"
                except (InvalidOperation, TypeError): return str(val) if val is not None else "0.00"
            if header_key == "status": return entry_summary.get("status", "")
            
            # Fallback for any unhandled column, though all should be covered
            return entry_summary.get(header_key, "")

        elif role == Qt.ItemDataRole.UserRole: # Store complex data if needed, e.g., full object or just ID
            # Typically, for quick access to the ID without parsing display text
            if col == 0: # Store ID with the first column for convenience
                 return entry_summary.get("id")
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Total": # Align "Total" amount to the right
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def get_journal_entry_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Prefer UserRole if ID is stored there, otherwise parse from display data (less ideal)
            index = self.index(row, 0) # Assuming ID is in/associated with the first column
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole not used or ID not stored there, try from dict directly
            return self._data[row].get("id")
        return None
        
    def get_journal_entry_status_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].get("status")
        return None

    def update_data(self, new_data: List[Dict[str, Any]]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


```

# app/ui/accounting/__init__.py
```py
# File: app/ui/accounting/__init__.py
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog
from .fiscal_year_dialog import FiscalYearDialog 
from .journal_entry_dialog import JournalEntryDialog # Added
from .journal_entries_widget import JournalEntriesWidget # Added
from .journal_entry_table_model import JournalEntryTableModel # Added

__all__ = [
    "AccountingWidget", 
    "ChartOfAccountsWidget", 
    "AccountDialog",
    "FiscalYearDialog", 
    "JournalEntryDialog",
    "JournalEntriesWidget",
    "JournalEntryTableModel",
]

```

# app/ui/accounting/chart_of_accounts_widget.py
```py
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction, QColor
from decimal import Decimal, InvalidOperation
from datetime import date 
import asyncio 
import json # For JSON serialization
from typing import Optional, Dict, Any, List 

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
from app.utils.result import Result 
from app.main import schedule_task_from_qt 

# Helper for JSON serialization with Decimal and date
def json_converter(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class ChartOfAccountsWidget(QWidget):
    account_selected = Signal(int)
    
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.account_tree = QTreeView()
        self.account_tree.setAlternatingRowColors(True)
        self.account_tree.setUniformRowHeights(True)
        self.account_tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.account_tree.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.account_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_tree.customContextMenuRequested.connect(self.on_context_menu)
        self.account_tree.doubleClicked.connect(self.on_account_double_clicked)
        
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"]) 
        
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.account_model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.account_tree.setModel(self.proxy_model)
        
        header = self.account_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar) 

        self.main_layout.addWidget(self.account_tree) 
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        icon_path_prefix = "" 
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.add_button = QPushButton(QIcon(icon_path_prefix + "edit.svg"), "Add Account") 
        self.add_button.clicked.connect(self.on_add_account)
        self.button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton(QIcon(icon_path_prefix + "edit.svg"), "Edit Account")
        self.edit_button.clicked.connect(self.on_edit_account)
        self.button_layout.addWidget(self.edit_button)
        
        self.deactivate_button = QPushButton(QIcon(icon_path_prefix + "deactivate.svg"), "Toggle Active")
        self.deactivate_button.clicked.connect(self.on_toggle_active_status) 
        self.button_layout.addWidget(self.deactivate_button)
        
        self.button_layout.addStretch() 
        self.main_layout.addLayout(self.button_layout)

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_accounts()))

    def _create_toolbar(self):
        from PySide6.QtCore import QSize 
        self.toolbar = QToolBar("COA Toolbar") 
        self.toolbar.setObjectName("COAToolbar") 
        self.toolbar.setIconSize(QSize(16, 16))
        
        icon_path_prefix = ""
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.filter_action = QAction(QIcon(icon_path_prefix + "filter.svg"), "Filter", self)
        self.filter_action.setCheckable(True)
        self.filter_action.toggled.connect(self.on_filter_toggled)
        self.toolbar.addAction(self.filter_action)
        
        self.toolbar.addSeparator()

        self.expand_all_action = QAction(QIcon(icon_path_prefix + "expand_all.svg"), "Expand All", self)
        self.expand_all_action.triggered.connect(self.account_tree.expandAll)
        self.toolbar.addAction(self.expand_all_action)
        
        self.collapse_all_action = QAction(QIcon(icon_path_prefix + "collapse_all.svg"), "Collapse All", self)
        self.collapse_all_action.triggered.connect(self.account_tree.collapseAll)
        self.toolbar.addAction(self.collapse_all_action)
        
        self.toolbar.addSeparator()

        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_accounts()))
        self.toolbar.addAction(self.refresh_action)
        
    async def _load_accounts(self):
        try:
            manager = self.app_core.accounting_service 
            if not (manager and hasattr(manager, 'get_account_tree')):
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                    Q_ARG(str,"Accounting service (ChartOfAccountsManager) or get_account_tree method not available."))
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) 
            json_data = json.dumps(account_tree_data, default=json_converter)
            
            QMetaObject.invokeMethod(self, "_update_account_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data))
            
        except Exception as e:
            error_message = f"Failed to load accounts: {str(e)}"
            print(error_message) 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(str) 
    def _update_account_model_slot(self, account_tree_json_str: str):
        try:
            account_tree_data: List[Dict[str, Any]] = json.loads(account_tree_json_str)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Failed to parse account data: {e}")
            return

        self.account_model.clear() 
        self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
        root_item = self.account_model.invisibleRootItem()
        if account_tree_data: 
            for account_node in account_tree_data:
                self._add_account_to_model_item(account_node, root_item) 
        self.account_tree.expandToDepth(0) 

    def _add_account_to_model_item(self, account_data: dict, parent_item: QStandardItem):
        code_item = QStandardItem(account_data['code'])
        code_item.setData(account_data['id'], Qt.ItemDataRole.UserRole)
        name_item = QStandardItem(account_data['name'])
        type_text = account_data.get('sub_type') or account_data.get('account_type', '')
        type_item = QStandardItem(type_text)
        
        ob_str = account_data.get('opening_balance', "0.00")
        try:
            ob_val = Decimal(str(ob_str))
        except InvalidOperation:
            ob_val = Decimal(0)
        ob_item = QStandardItem(f"{ob_val:,.2f}")
        ob_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Handle opening_balance_date if it's in ISO format string
        ob_date_str = account_data.get('opening_balance_date')
        if ob_date_str:
            try:
                # Potentially store/display QDate.fromString(ob_date_str, Qt.DateFormat.ISODate)
                pass # For now, just displaying balance
            except Exception:
                pass


        is_active_item = QStandardItem("Yes" if account_data.get('is_active', False) else "No")
        parent_item.appendRow([code_item, name_item, type_item, ob_item, is_active_item])
        
        if 'children' in account_data:
            for child_data in account_data['children']:
                self._add_account_to_model_item(child_data, code_item) 
    
    @Slot()
    def on_add_account(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in. Cannot add account.")
            return
        dialog = AccountDialog(self.app_core, current_user_id=self.app_core.current_user.id, parent=self) 
        if dialog.exec() == QDialog.DialogCode.Accepted: 
            schedule_task_from_qt(self._load_accounts())
    
    @Slot()
    def on_edit_account(self):
        index = self.account_tree.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Please select an account to edit.")
            return
        source_index = self.proxy_model.mapToSource(index)
        item = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item: return
        account_id = item.data(Qt.ItemDataRole.UserRole)
        if not account_id: 
            QMessageBox.warning(self, "Warning", "Cannot edit this item. Please select an account.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in. Cannot edit account.")
            return
        dialog = AccountDialog(self.app_core, account_id=account_id, current_user_id=self.app_core.current_user.id, parent=self) 
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule_task_from_qt(self._load_accounts())
            
    @Slot()
    def on_toggle_active_status(self): 
        index = self.account_tree.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Please select an account.")
            return
        source_index = self.proxy_model.mapToSource(index)
        item_id_qstandarditem = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        account_id = item_id_qstandarditem.data(Qt.ItemDataRole.UserRole) if item_id_qstandarditem else None
        if not account_id:
            QMessageBox.warning(self, "Warning", "Cannot determine account. Please select a valid account.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        schedule_task_from_qt(self._perform_toggle_active_status_logic(account_id, self.app_core.current_user.id))

    async def _perform_toggle_active_status_logic(self, account_id: int, user_id: int):
        try:
            manager = self.app_core.accounting_service 
            if not manager: raise RuntimeError("Accounting service not available.")
            account = await manager.account_service.get_by_id(account_id) 
            if not account:
                 QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,f"Account ID {account_id} not found."))
                 return
            data_to_pass = {"id": account_id, "is_active": account.is_active, "code": account.code, "name": account.name, "user_id": user_id}
            json_data_to_pass = json.dumps(data_to_pass, default=json_converter)
            QMetaObject.invokeMethod(self, "_confirm_and_toggle_status_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data_to_pass))
        except Exception as e:
            error_message = f"Failed to prepare toggle account active status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(str) 
    def _confirm_and_toggle_status_slot(self, data_json_str: str):
        try:
            data: Dict[str, Any] = json.loads(data_json_str)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Failed to parse toggle status data: {e}")
            return

        account_id = data["id"]
        is_currently_active = data["is_active"]
        acc_code = data["code"]
        acc_name = data["name"]
        user_id = data["user_id"]

        action_verb_present = "deactivate" if is_currently_active else "activate"
        action_verb_past = "deactivated" if is_currently_active else "activated"
        confirm_msg = f"Are you sure you want to {action_verb_present} account '{acc_code} - {acc_name}'?"
        reply = QMessageBox.question(self, f"Confirm {action_verb_present.capitalize()}", confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            schedule_task_from_qt(self._finish_toggle_status(account_id, not is_currently_active, user_id, action_verb_past))

    async def _finish_toggle_status(self, account_id: int, new_active_status: bool, user_id: int, action_verb_past: str):
        try:
            manager = self.app_core.accounting_service
            account = await manager.account_service.get_by_id(account_id)
            if not account: return 

            result: Optional[Result] = None
            if not new_active_status: 
                result = await manager.deactivate_account(account_id, user_id)
            else: 
                account.is_active = True
                account.updated_by_user_id = user_id
                saved_acc = await manager.account_service.save(account)
                result = Result.success(saved_acc)

            if result and result.is_success:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str,f"Account {action_verb_past} successfully."))
                schedule_task_from_qt(self._load_accounts()) 
            elif result:
                error_str = f"Failed to {action_verb_past.replace('ed','e')} account:\n{', '.join(result.errors)}"
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_str))
        except Exception as e:
            error_message = f"Error finishing toggle status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(QModelIndex)
    def on_account_double_clicked(self, index: QModelIndex):
        if not index.isValid(): return
        source_index = self.proxy_model.mapToSource(index)
        item = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item: return
        account_id = item.data(Qt.ItemDataRole.UserRole)
        if account_id: self.account_selected.emit(account_id)
    
    @Slot(bool)
    def on_filter_toggled(self, checked: bool):
        if checked:
            QMessageBox.information(self, "Filter", "Filter functionality to be implemented.")
            self.filter_action.setChecked(False) 
        else:
            self.proxy_model.setFilterFixedString("") 
    
    @Slot(QPoint)
    def on_context_menu(self, pos: QPoint):
        index = self.account_tree.indexAt(pos)
        if not index.isValid(): return
        source_index = self.proxy_model.mapToSource(index)
        item_id_qstandarditem = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item_id_qstandarditem : return
        account_id = item_id_qstandarditem.data(Qt.ItemDataRole.UserRole)
        if not account_id: return 
        icon_path_prefix = ""
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"
        context_menu = QMenu(self)
        edit_action = QAction(QIcon(icon_path_prefix + "edit.svg"), "Edit Account", self)
        edit_action.triggered.connect(self.on_edit_account) 
        context_menu.addAction(edit_action)
        view_trans_action = QAction(QIcon(icon_path_prefix + "transactions.svg"), "View Transactions", self)
        view_trans_action.triggered.connect(lambda: self.on_view_transactions(account_id))
        context_menu.addAction(view_trans_action)
        toggle_active_action = QAction(QIcon(icon_path_prefix + "deactivate.svg"), "Toggle Active Status", self)
        toggle_active_action.triggered.connect(self.on_toggle_active_status)
        context_menu.addAction(toggle_active_action)
        context_menu.exec(self.account_tree.viewport().mapToGlobal(pos))
    
    @Slot(int)
    def on_view_transactions(self, account_id: int):
        QMessageBox.information(self, "View Transactions", f"View transactions for account ID {account_id} (To be implemented).")

```

# app/ui/accounting/journal_entries_widget.py
```py
# File: app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QDateEdit, QComboBox, QInputDialog, QLineEdit,
    QFormLayout 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QAction 
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json
from datetime import date as python_date 
from decimal import Decimal

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
from app.common.enums import JournalTypeEnum # Import for populating Journal Type filter
from app.main import schedule_task_from_qt
from app.models.accounting.journal_entry import JournalEntry 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for JournalEntriesWidget.")
        except ImportError:
            self.app_core.logger.info("JournalEntriesWidget: Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
            pass

        self._init_ui()
        QTimer.singleShot(0, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        filter_group_layout = QHBoxLayout()
        filter_layout_form = QFormLayout()
        filter_layout_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")

        self.entry_no_filter_edit = QLineEdit(); self.entry_no_filter_edit.setPlaceholderText("Filter by Entry No.")
        self.description_filter_edit = QLineEdit(); self.description_filter_edit.setPlaceholderText("Filter by Description")
        self.status_filter_combo = QComboBox(); self.status_filter_combo.addItems(["All", "Draft", "Posted"])
        
        self.journal_type_filter_combo = QComboBox() # New QComboBox for Journal Type
        self.journal_type_filter_combo.addItem("All Types", None) # User data None for all
        for jt_enum in JournalTypeEnum:
            self.journal_type_filter_combo.addItem(jt_enum.value, jt_enum.value) # Store enum value as data
        
        filter_layout_form.addRow("From Date:", self.start_date_filter_edit)
        filter_layout_form.addRow("To Date:", self.end_date_filter_edit)
        filter_layout_form.addRow("Entry No.:", self.entry_no_filter_edit)
        filter_layout_form.addRow("Description:", self.description_filter_edit)
        filter_layout_form.addRow("Status:", self.status_filter_combo)
        filter_layout_form.addRow("Journal Type:", self.journal_type_filter_combo) # Add to form
        
        filter_group_layout.addLayout(filter_layout_form)

        filter_button_layout = QVBoxLayout()
        self.apply_filter_button = QPushButton(
            QIcon.fromTheme("edit-find", QIcon(self.icon_path_prefix + "filter.svg")),
            "Apply Filter"
        )
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_entries()))
        
        self.clear_filter_button = QPushButton(
            QIcon.fromTheme("edit-clear", QIcon(self.icon_path_prefix + "refresh.svg")),
            "Clear Filters"
        )
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        
        filter_button_layout.addWidget(self.apply_filter_button)
        filter_button_layout.addWidget(self.clear_filter_button)
        filter_button_layout.addStretch()
        filter_group_layout.addLayout(filter_button_layout)
        filter_group_layout.addStretch(1)
        self.main_layout.addLayout(filter_group_layout)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True)

        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)

        header = self.entries_table.horizontalHeader()
        header.setStretchLastSection(False) 
        for i in range(self.table_model.columnCount()): 
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        id_column_model_index = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0
        self.entries_table.setColumnHidden(id_column_model_index, True)
        description_column_model_index = self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2
        visible_description_idx = description_column_model_index
        if id_column_model_index < description_column_model_index and self.entries_table.isColumnHidden(id_column_model_index):
            visible_description_idx -=1
        if not self.entries_table.isColumnHidden(description_column_model_index):
            header.setSectionResizeMode(visible_description_idx, QHeaderView.ResizeMode.Stretch)
        
        self._create_toolbar() 
        self.main_layout.addWidget(self.toolbar) 
        self.main_layout.addWidget(self.entries_table) 
        self.setLayout(self.main_layout)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _clear_filters_and_load(self):
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        self.entry_no_filter_edit.clear()
        self.description_filter_edit.clear()
        self.status_filter_combo.setCurrentText("All")
        self.journal_type_filter_combo.setCurrentIndex(0) # Reset to "All Types"
        schedule_task_from_qt(self._load_entries())

    def _create_toolbar(self):
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(16, 16)) 

        self.new_entry_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Entry", self) 
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Entry", self) 
        self.view_entry_action.triggered.connect(self.on_view_entry_toolbar) 
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Selected", self) 
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(self.icon_path_prefix + "reverse.svg"), "Reverse Selected", self) 
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        self.refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _update_action_states(self):
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False; is_posted = False; single_selection = len(selected_indexes) == 1

        if single_selection:
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            if status is not None: 
                is_draft = status == "Draft" 
                is_posted = status == "Posted"
        
        can_post_any_draft = False
        if has_selection: 
            for index in selected_indexes:
                if self.table_model.get_journal_entry_status_at_row(index.row()) == "Draft":
                    can_post_any_draft = True; break
        
        self.edit_entry_action.setEnabled(single_selection and is_draft)
        self.view_entry_action.setEnabled(single_selection)
        self.post_entry_action.setEnabled(can_post_any_draft) 
        self.reverse_entry_action.setEnabled(single_selection and is_posted)

    async def _load_entries(self):
        if not self.app_core.journal_entry_manager:
            error_msg = "Journal Entry Manager not available."
            self.app_core.logger.critical(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Critical Error"), Q_ARG(str, error_msg))
            return
        try:
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()
            status_text = self.status_filter_combo.currentText()
            status_filter = status_text if status_text != "All" else None
            entry_no_filter_text = self.entry_no_filter_edit.text().strip()
            description_filter_text = self.description_filter_edit.text().strip()
            journal_type_filter_val = self.journal_type_filter_combo.currentData() 

            filters = {"start_date": start_date, "end_date": end_date, "status": status_filter,
                       "entry_no": entry_no_filter_text or None, 
                       "description": description_filter_text or None,
                       "journal_type": journal_type_filter_val 
                       }
            
            result: Result[List[Dict[str, Any]]] = await self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters=filters)
            
            if result.is_success:
                entries_data_for_table = result.value if result.value is not None else []
                json_data = json.dumps(entries_data_for_table, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load journal entries: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading journal entries: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            entries_data: List[Dict[str, Any]] = json.loads(json_data_str, object_hook=json_date_hook)
            self.table_model.update_data(entries_data)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse journal entry data: {e}")
        self._update_action_states()

    @Slot()
    def on_new_entry(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to create a journal entry.")
            return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec() 

    def _get_selected_entry_id_and_status(self, require_single_selection: bool = True) -> tuple[Optional[int], Optional[str]]:
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        if not selected_indexes:
            if require_single_selection: QMessageBox.information(self, "Selection", "Please select a journal entry.")
            return None, None
        if require_single_selection and len(selected_indexes) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single journal entry for this action.")
            return None, None
        
        row = selected_indexes[0].row() 
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)
        return entry_id, entry_status

    @Slot()
    def on_edit_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        if entry_status != "Draft": QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to edit."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot(QModelIndex) 
    def on_view_entry_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    @Slot()
    def on_view_entry_toolbar(self): 
        entry_id, _ = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    def _show_view_entry_dialog(self, entry_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, view_only=True, parent=self)
        dialog.exec()

    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "Selection", "Please select draft journal entries to post."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to post entries."); return
        entries_to_post_ids = []
        for index in selected_rows:
            entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
            entry_status = self.table_model.get_journal_entry_status_at_row(index.row())
            if entry_id and entry_status == "Draft": entries_to_post_ids.append(entry_id)
        if not entries_to_post_ids: QMessageBox.information(self, "Selection", "No draft entries selected for posting."); return
        schedule_task_from_qt(self._perform_post_entries(entries_to_post_ids, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        if not self.app_core.journal_entry_manager: 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        success_count = 0; errors = []
        for entry_id_to_post in entry_ids:
            result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(entry_id_to_post, user_id)
            if result.is_success: success_count += 1
            else:
                je_no_str = f"ID {entry_id_to_post}" 
                try:
                    temp_je = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(entry_id_to_post)
                    if temp_je: je_no_str = temp_je.entry_no
                except Exception: pass
                errors.append(f"Entry {je_no_str}: {', '.join(result.errors)}")
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors: message += "\n\nErrors:\n" + "\n".join(errors)
        msg_box_method = QMessageBox.information if not errors and success_count > 0 else QMessageBox.warning
        title = "Posting Complete" if not errors and success_count > 0 else ("Posting Failed" if success_count == 0 else "Posting Partially Failed")
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, message))
        if success_count > 0: schedule_task_from_qt(self._load_entries())


    @Slot()
    def on_reverse_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None or entry_status != "Posted": QMessageBox.warning(self, "Reverse Error", "Only single, posted entries can be reversed."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to reverse entries."); return
        reply = QMessageBox.question(self, "Confirm Reversal", 
                                     f"Are you sure you want to reverse journal entry ID {entry_id}?\nA new counter-entry will be created as a DRAFT.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        reversal_date_str, ok_date = QInputDialog.getText(self, "Reversal Date", "Enter reversal date (YYYY-MM-DD):", QLineEdit.EchoMode.Normal, python_date.today().isoformat())
        if ok_date and reversal_date_str:
            try:
                parsed_reversal_date = python_date.fromisoformat(reversal_date_str)
                reversal_desc_str, ok_desc = QInputDialog.getText(self, "Reversal Description", "Enter description for reversal entry (optional):", QLineEdit.EchoMode.Normal, f"Reversal of JE {entry_id}")
                if ok_desc: 
                    schedule_task_from_qt(self._perform_reverse_entry(entry_id, parsed_reversal_date, reversal_desc_str, self.app_core.current_user.id))
                else: QMessageBox.information(self, "Cancelled", "Reversal description input cancelled.")
            except ValueError: QMessageBox.warning(self, "Invalid Date", "Reversal date format is invalid. Please use YYYY-MM-DD.")
        else: QMessageBox.information(self, "Cancelled", "Reversal date input cancelled.")

    async def _perform_reverse_entry(self, entry_id: int, reversal_date: python_date, description: str, user_id: int):
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        result: Result[JournalEntry] = await self.app_core.journal_entry_manager.reverse_journal_entry(entry_id, reversal_date, description, user_id)
        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Journal entry ID {entry_id} reversed. New reversal entry: {result.value.entry_no} (Draft)."))
            schedule_task_from_qt(self._load_entries())
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Reversal Error"), Q_ARG(str, f"Failed to reverse journal entry:\n{', '.join(result.errors)}"))

```

# app/ui/accounting/fiscal_year_dialog.py
```py
# File: app/ui/accounting/fiscal_year_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import date as python_date # Alias to avoid conflict with QDate

from app.utils.pydantic_models import FiscalYearCreateData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class FiscalYearDialog(QDialog):
    def __init__(self, app_core: "ApplicationCore", current_user_id: int, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self._fiscal_year_data: Optional[FiscalYearCreateData] = None
        self._previous_start_date: Optional[QDate] = None # For default end date logic

        self.setWindowTitle("Add New Fiscal Year")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()
        self._set_initial_dates() # Set initial default dates

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.year_name_edit = QLineEdit()
        self.year_name_edit.setPlaceholderText("e.g., FY2024 or Y/E 31 Dec 2024")
        form_layout.addRow("Fiscal Year Name*:", self.year_name_edit)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Start Date*:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("End Date*:", self.end_date_edit)
        
        self.start_date_edit.dateChanged.connect(self._update_default_end_date)

        self.auto_generate_periods_combo = QComboBox()
        self.auto_generate_periods_combo.addItems(["Monthly", "Quarterly", "None"])
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        form_layout.addRow("Auto-generate Periods:", self.auto_generate_periods_combo)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _set_initial_dates(self):
        today = QDate.currentDate()
        # Default start: first day of current month, or Jan 1st if typical
        default_start = QDate(today.year(), 1, 1) # Default to Jan 1st of current year
        # If current date is past June, suggest starting next year's FY
        if today.month() > 6:
            default_start = QDate(today.year() + 1, 1, 1)
        
        default_end = default_start.addYears(1).addDays(-1)
        
        self.start_date_edit.setDate(default_start)
        self.end_date_edit.setDate(default_end) 
        self._previous_start_date = default_start


    @Slot(QDate)
    def _update_default_end_date(self, new_start_date: QDate):
        # Only update if the end date seems to be following the start date automatically
        # or if it's the initial setup.
        if self._previous_start_date is None: # Initial setup
            self._previous_start_date = self.start_date_edit.date() # Could be different from new_start_date if called by setDate initially
        
        # Calculate expected end based on previous start
        expected_end_from_prev_start = self._previous_start_date.addYears(1).addDays(-1)
        
        # If current end date matches the old default, then update it based on new start date
        if self.end_date_edit.date() == expected_end_from_prev_start:
            self.end_date_edit.setDate(new_start_date.addYears(1).addDays(-1))
        
        self._previous_start_date = new_start_date


    @Slot()
    def accept_data(self):
        """Validate and store data before accepting the dialog."""
        year_name = self.year_name_edit.text().strip()
        start_date_py: python_date = self.start_date_edit.date().toPython() 
        end_date_py: python_date = self.end_date_edit.date().toPython()
        auto_generate_str = self.auto_generate_periods_combo.currentText()
        auto_generate_periods = auto_generate_str if auto_generate_str != "None" else None

        errors = []
        if not year_name:
            errors.append("Fiscal Year Name is required.")
        if start_date_py >= end_date_py:
            errors.append("End Date must be after Start Date.")
        
        days_in_year = (end_date_py - start_date_py).days + 1
        if not (300 < days_in_year < 400): # Heuristic for typical year length
             errors.append("Fiscal year duration seems unusual (typically around 365 days). Please verify dates.")

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return # Do not accept

        try:
            self._fiscal_year_data = FiscalYearCreateData(
                year_name=year_name,
                start_date=start_date_py,
                end_date=end_date_py,
                auto_generate_periods=auto_generate_periods,
                user_id=self.current_user_id # Passed in from calling widget
            )
            super().accept() 
        except Exception as e: 
            QMessageBox.warning(self, "Data Error", f"Invalid data: {str(e)}")


    def get_fiscal_year_data(self) -> Optional[FiscalYearCreateData]:
        return self._fiscal_year_data

    def open(self) -> int: 
        self._fiscal_year_data = None
        self.year_name_edit.clear()
        self._set_initial_dates() # Reset dates to default for a new entry
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        self.year_name_edit.setFocus()
        return super().open()

```

# app/ui/accounting/accounting_widget.py
```py
# File: app/ui/accounting/accounting_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from app.ui.accounting.chart_of_accounts_widget import ChartOfAccountsWidget
from app.ui.accounting.journal_entries_widget import JournalEntriesWidget # Import new widget
from app.core.application_core import ApplicationCore 

class AccountingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None): 
        super().__init__(parent)
        self.app_core = app_core
        
        self.layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.coa_widget = ChartOfAccountsWidget(self.app_core)
        self.tab_widget.addTab(self.coa_widget, "Chart of Accounts")
        
        self.journal_entries_widget = JournalEntriesWidget(self.app_core) # Create instance
        self.tab_widget.addTab(self.journal_entries_widget, "Journal Entries") # Add as tab
        
        other_label = QLabel("Other Accounting Features (e.g., Fiscal Periods, Budgets)")
        self.tab_widget.addTab(other_label, "More...")

        self.setLayout(self.layout)

```

# app/ui/accounting/journal_entry_dialog.py
```py
# File: app/ui/accounting/journal_entry_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDoubleSpinBox, QApplication, QStyledItemDelegate,
    QAbstractSpinBox # For QDoubleSpinBox.NoButtons
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QKeySequence, QColor, QPalette # QKeySequence not used here, but kept from original for consistency
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast

from decimal import Decimal, InvalidOperation
import json
from datetime import date as python_date

from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
# from app.models.accounting.currency import Currency # Not directly used for line combos
from app.models.accounting.journal_entry import JournalEntry 
from app.common.enums import JournalTypeEnum 
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook 
from app.utils.result import Result 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from PySide6.QtGui import QPaintDevice # For QWidget type hint

class JournalEntryDialog(QDialog):
    journal_entry_saved = Signal(int) # Emits the ID of the saved/updated JE

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 journal_entry_id: Optional[int] = None, 
                 view_only: bool = False, 
                 parent: Optional["QWidget"] = None): # QWidget type hint
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.journal_entry_id = journal_entry_id
        self.view_only_mode = view_only 
        self.loaded_journal_entry_orm: Optional[JournalEntry] = None 
        self.existing_journal_entry_data_dict: Optional[Dict[str, Any]] = None

        self._accounts_cache: List[Account] = []
        self._tax_codes_cache: List[TaxCode] = []
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(900, 700)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.journal_entry_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_journal_entry()))
        elif not self.view_only_mode: 
            self._add_new_line() 
            self._add_new_line() 

    def _get_window_title(self) -> str:
        if self.view_only_mode: return "View Journal Entry"
        if self.journal_entry_id: return "Edit Journal Entry"
        return "New Journal Entry"

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        self.header_form = QFormLayout() # Made it an instance variable for disabling fields
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.entry_date_edit = QDateEdit(QDate.currentDate())
        self.entry_date_edit.setCalendarPopup(True)
        self.entry_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.header_form.addRow("Entry Date*:", self.entry_date_edit)

        self.journal_type_combo = QComboBox()
        for jt_enum_member in JournalTypeEnum: self.journal_type_combo.addItem(jt_enum_member.value, jt_enum_member.value)
        self.journal_type_combo.setCurrentText(JournalTypeEnum.GENERAL.value)
        self.header_form.addRow("Journal Type:", self.journal_type_combo)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Overall description for the journal entry")
        self.header_form.addRow("Description:", self.description_edit)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("e.g., Invoice #, Check #, Source Document ID")
        self.header_form.addRow("Reference:", self.reference_edit)
        
        main_layout.addLayout(self.header_form)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(7) 
        self.lines_table.setHorizontalHeaderLabels([
            "Account*", "Description", "Debit*", "Credit*", 
            "Tax Code", "Tax Amt", "" 
        ])
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed) 
        self.lines_table.setColumnWidth(2, 130); self.lines_table.setColumnWidth(3, 130)
        self.lines_table.setColumnWidth(4, 160); self.lines_table.setColumnWidth(5, 110)
        self.lines_table.setColumnWidth(6, 30) 
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.lines_table)

        lines_button_layout = QHBoxLayout()
        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self.add_line_button = QPushButton(QIcon(icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(icon_path_prefix + "remove.svg"), "Remove Selected Line")
        lines_button_layout.addWidget(self.add_line_button)
        lines_button_layout.addWidget(self.remove_line_button)
        lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.debits_label = QLabel("Debits: 0.00")
        self.credits_label = QLabel("Credits: 0.00")
        self.balance_label = QLabel("Balance: OK")
        self.balance_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.debits_label); totals_layout.addWidget(QLabel("  |  "));
        totals_layout.addWidget(self.credits_label); totals_layout.addWidget(QLabel("  |  "));
        totals_layout.addWidget(self.balance_label)
        main_layout.addLayout(totals_layout)

        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_post_button = self.button_box.addButton("Save & Post", QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_line)
        self.remove_line_button.clicked.connect(self._remove_selected_line)
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_post_button.clicked.connect(self.on_save_and_post)
        
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if close_button: # In view_only_mode
            close_button.clicked.connect(self.reject)
        if cancel_button: # In edit/new mode
            cancel_button.clicked.connect(self.reject)


    async def _load_initial_combo_data(self):
        # ... (same as previous version)
        try:
            if self.app_core.chart_of_accounts_manager:
                 self._accounts_cache = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            if self.app_core.tax_code_service:
                 self._tax_codes_cache = await self.app_core.tax_code_service.get_all()
            QMetaObject.invokeMethod(self, "_update_combos_in_all_lines_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading initial combo data for JE Dialog: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Data Load Error"), Q_ARG(str, f"Could not load all data for dropdowns: {e}"))

    @Slot()
    def _update_combos_in_all_lines_slot(self):
        # ... (same as previous version)
        for r in range(self.lines_table.rowCount()):
            line_data_to_use = None
            if self.existing_journal_entry_data_dict and r < len(self.existing_journal_entry_data_dict.get("lines",[])):
                line_data_to_use = self.existing_journal_entry_data_dict["lines"][r]
            self._populate_combos_for_row(r, line_data_to_use)

    async def _load_existing_journal_entry(self):
        # ... (same as previous version)
        if not self.journal_entry_id or not self.app_core.journal_entry_manager: return
        
        self.loaded_journal_entry_orm = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(self.journal_entry_id)
        if self.loaded_journal_entry_orm:
            json_data_str = self._serialize_je_for_ui(self.loaded_journal_entry_orm)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data_str))
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Journal Entry ID {self.journal_entry_id} not found."))
            self.reject()


    def _serialize_je_for_ui(self, je: JournalEntry) -> str: # Converts ORM to JSON string for cross-thread
        # ... (same as previous version)
        data = {
            "entry_date": je.entry_date, "journal_type": je.journal_type,
            "description": je.description, "reference": je.reference,
            "is_posted": je.is_posted, "source_type": je.source_type, "source_id": je.source_id,
            "lines": [
                { "account_id": line.account_id, "description": line.description,
                  "debit_amount": line.debit_amount, "credit_amount": line.credit_amount,
                  "currency_code": line.currency_code, "exchange_rate": line.exchange_rate,
                  "tax_code": line.tax_code, "tax_amount": line.tax_amount,
                  "dimension1_id": line.dimension1_id, "dimension2_id": line.dimension2_id,
                } for line in je.lines ]}
        return json.dumps(data, default=json_converter)

    @Slot(str)
    def _populate_dialog_from_data_slot(self, json_data_str: str): # Parses JSON and populates UI
        # ... (same as previous version, including read-only logic)
        try:
            data = json.loads(json_data_str, object_hook=json_date_hook)
            self.existing_journal_entry_data_dict = data 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing journal entry data."); return

        if data.get("entry_date"): self.entry_date_edit.setDate(QDate(data["entry_date"]))
        type_idx = self.journal_type_combo.findText(data.get("journal_type", JournalTypeEnum.GENERAL.value))
        if type_idx != -1: self.journal_type_combo.setCurrentIndex(type_idx)
        self.description_edit.setText(data.get("description", ""))
        self.reference_edit.setText(data.get("reference", ""))

        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_line(); self._add_new_line()
        self._calculate_totals()

        is_read_only = self.view_only_mode or data.get("is_posted", False)
        if is_read_only:
            self.save_draft_button.setVisible(False) 
            self.save_post_button.setVisible(False)
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
            # Iterate through form layout items to set read-only
            for i in range(self.header_form.rowCount()):
                label_item = self.header_form.itemAt(i, QFormLayout.ItemRole.LabelRole)
                field_item = self.header_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if field_item:
                    widget = field_item.widget()
                    if isinstance(widget, (QLineEdit, QDateEdit)): widget.setReadOnly(True)
                    elif isinstance(widget, QComboBox): widget.setEnabled(False)
            
            self.add_line_button.setEnabled(False); self.remove_line_button.setEnabled(False)
            for r in range(self.lines_table.rowCount()): 
                del_btn_widget = self.lines_table.cellWidget(r, 6)
                if del_btn_widget : del_btn_widget.setVisible(False)


    def _populate_combos_for_row(self, row: int, line_data_for_this_row: Optional[Dict[str, Any]] = None):
        # ... (same as previous version, but ensure cast is imported)
        acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
        if not acc_combo: acc_combo = QComboBox(); self.lines_table.setCellWidget(row, 0, acc_combo)
        acc_combo.clear()
        acc_combo.setEditable(True); acc_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        current_acc_id = line_data_for_this_row.get("account_id") if line_data_for_this_row else None
        selected_acc_idx = -1
        for i, acc_orm in enumerate(self._accounts_cache):
            acc_combo.addItem(f"{acc_orm.code} - {acc_orm.name}", acc_orm.id)
            if acc_orm.id == current_acc_id: selected_acc_idx = i
        
        if selected_acc_idx != -1: acc_combo.setCurrentIndex(selected_acc_idx)
        elif current_acc_id and self.loaded_journal_entry_orm: 
            orig_line_orm = next((l for l in self.loaded_journal_entry_orm.lines if l.account_id == current_acc_id), None)
            if orig_line_orm and orig_line_orm.account:
                acc_combo.addItem(f"{orig_line_orm.account.code} - {orig_line_orm.account.name} (Loaded)", current_acc_id) # Indicate it's from loaded data
                acc_combo.setCurrentIndex(acc_combo.count() -1)
            else: 
                acc_combo.addItem(f"ID: {current_acc_id} (Unknown/Not Found)", current_acc_id)
                acc_combo.setCurrentIndex(acc_combo.count() -1)
        elif current_acc_id : # If no ORM loaded but ID exists (e.g. error case)
             acc_combo.addItem(f"ID: {current_acc_id} (Not in cache)", current_acc_id)
             acc_combo.setCurrentIndex(acc_combo.count() -1)


        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
        if not tax_combo: tax_combo = QComboBox(); self.lines_table.setCellWidget(row, 4, tax_combo)
        tax_combo.clear()
        tax_combo.addItem("None", "") 
        current_tax_code_str = line_data_for_this_row.get("tax_code") if line_data_for_this_row else None
        selected_tax_idx = 0 
        for i, tc_orm in enumerate(self._tax_codes_cache):
            tax_combo.addItem(f"{tc_orm.code} ({tc_orm.rate}%)", tc_orm.code)
            if tc_orm.code == current_tax_code_str: selected_tax_idx = i + 1
        
        tax_combo.setCurrentIndex(selected_tax_idx)
        if selected_tax_idx == 0 and current_tax_code_str : # Loaded tax code not in cache
             tax_combo.addItem(f"{current_tax_code_str} (Not in cache)", current_tax_code_str)
             tax_combo.setCurrentIndex(tax_combo.count()-1)


    def _add_new_line(self, line_data: Optional[Dict[str, Any]] = None):
        # ... (same as previous, ensure icon path fallback)
        row_position = self.lines_table.rowCount()
        self.lines_table.insertRow(row_position)

        acc_combo = QComboBox(); self.lines_table.setCellWidget(row_position, 0, acc_combo)
        
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row_position, 1, desc_item)

        debit_spin = QDoubleSpinBox(); debit_spin.setRange(0, 999999999999.99); debit_spin.setDecimals(2); debit_spin.setGroupSeparatorShown(True); debit_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        credit_spin = QDoubleSpinBox(); credit_spin.setRange(0, 999999999999.99); credit_spin.setDecimals(2); credit_spin.setGroupSeparatorShown(True); credit_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        if line_data:
            debit_spin.setValue(float(Decimal(str(line_data.get("debit_amount", "0")))))
            credit_spin.setValue(float(Decimal(str(line_data.get("credit_amount", "0")))))
        self.lines_table.setCellWidget(row_position, 2, debit_spin)
        self.lines_table.setCellWidget(row_position, 3, credit_spin)
        
        debit_spin.valueChanged.connect(lambda val, r=row_position, cs=credit_spin: cs.setValue(0.00) if val > 0.001 else None)
        credit_spin.valueChanged.connect(lambda val, r=row_position, ds=debit_spin: ds.setValue(0.00) if val > 0.001 else None)
        debit_spin.valueChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))
        credit_spin.valueChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))

        tax_combo = QComboBox(); self.lines_table.setCellWidget(row_position, 4, tax_combo)
        tax_combo.currentIndexChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position)) # Ensure it triggers recalc chain

        initial_tax_amt_str = "0.00"
        if line_data and line_data.get("tax_amount") is not None:
            initial_tax_amt_str = str(Decimal(str(line_data.get("tax_amount"))).quantize(Decimal("0.01")))
        tax_amt_item = QTableWidgetItem(initial_tax_amt_str)
        tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lines_table.setItem(row_position, 5, tax_amt_item)
        
        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/"
        except ImportError: pass
        del_button = QPushButton(QIcon(icon_path_prefix + "remove.svg"))
        del_button.setToolTip("Remove this line"); del_button.setFixedSize(24,24)
        del_button.clicked.connect(lambda _, r=row_position: self._remove_specific_line(r))
        self.lines_table.setCellWidget(row_position, 6, del_button)

        self._populate_combos_for_row(row_position, line_data) 
        self._recalculate_tax_for_line(row_position) 
        self._calculate_totals() 


    def _calculate_totals_and_tax_for_row_slot(self, row: int):
        # ... (same as previous)
        return lambda: self._chain_recalculate_tax_and_totals(row)

    def _chain_recalculate_tax_and_totals(self, row: int):
        # ... (same as previous)
        self._recalculate_tax_for_line(row)

    def _remove_selected_line(self):
        # ... (same as previous)
        current_row = self.lines_table.currentRow()
        if current_row >= 0: self._remove_specific_line(current_row)

    def _remove_specific_line(self, row_to_remove: int):
        # ... (same as previous)
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted): return
        if self.lines_table.rowCount() > 0 : 
            self.lines_table.removeRow(row_to_remove)
            self._calculate_totals()


    @Slot() 
    def _calculate_totals_from_signal(self): 
        # ... (same as previous)
        self._calculate_totals()

    def _calculate_totals(self):
        # ... (same as previous, ensure Decimal used)
        total_debits = Decimal(0); total_credits = Decimal(0)
        for row in range(self.lines_table.rowCount()):
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            if debit_spin: total_debits += Decimal(str(debit_spin.value()))
            if credit_spin: total_credits += Decimal(str(credit_spin.value()))
        
        self.debits_label.setText(f"Debits: {total_debits:,.2f}")
        self.credits_label.setText(f"Credits: {total_credits:,.2f}")

        if abs(total_debits - total_credits) < Decimal("0.005"): 
            self.balance_label.setText("Balance: OK"); self.balance_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            diff = total_debits - total_credits
            self.balance_label.setText(f"Balance: {diff:,.2f}"); self.balance_label.setStyleSheet("font-weight: bold; color: red;")

    def _recalculate_tax_for_line(self, row: int):
        # ... (same as previous, ensure Decimal used)
        try:
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
            tax_amt_item = self.lines_table.item(row, 5)

            if not all([debit_spin, credit_spin, tax_combo]): return 
            if not tax_amt_item: 
                tax_amt_item = QTableWidgetItem("0.00")
                tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.lines_table.setItem(row, 5, tax_amt_item)

            base_amount = Decimal(str(debit_spin.value())) if debit_spin.value() > 0 else Decimal(str(credit_spin.value()))
            tax_code_str = tax_combo.currentData() if tax_combo.currentIndex() > 0 else None # Handles "None" item
            
            calculated_tax = Decimal(0)
            if tax_code_str and base_amount != Decimal(0):
                tc_obj = next((tc for tc in self._tax_codes_cache if tc.code == tax_code_str), None)
                if tc_obj and tc_obj.tax_type == "GST" and tc_obj.rate is not None:
                    tax_rate = tc_obj.rate / Decimal(100)
                    calculated_tax = (base_amount * tax_rate).quantize(Decimal("0.01"))
            
            tax_amt_item.setText(f"{calculated_tax:,.2f}")
        except Exception as e:
            self.app_core.logger.error(f"Error recalculating tax for row {row}: {e}", exc_info=True)
            if tax_amt_item: tax_amt_item.setText("Error")
        finally:
            self._calculate_totals() 


    def _collect_data(self) -> Optional[JournalEntryData]:
        # ... (same as previous, but ensure use of self.loaded_journal_entry_orm for source_type/id)
        lines_data: List[JournalEntryLineData] = []
        total_debits = Decimal(0); total_credits = Decimal(0)

        for row in range(self.lines_table.rowCount()):
            try:
                acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
                desc_item_widget = self.lines_table.item(row, 1)
                debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
                credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
                tax_amt_item_widget = self.lines_table.item(row, 5)

                account_id = acc_combo.currentData() if acc_combo else None
                line_debit = Decimal(str(debit_spin.value())) if debit_spin else Decimal(0)
                line_credit = Decimal(str(credit_spin.value())) if credit_spin else Decimal(0)

                if account_id is None and (line_debit != Decimal(0) or line_credit != Decimal(0)):
                    QMessageBox.warning(self, "Validation Error", f"Account not selected for line {row + 1} which has amounts.")
                    return None
                if account_id is None: continue 

                line_dto = JournalEntryLineData(
                    account_id=int(account_id),
                    description=desc_item_widget.text() if desc_item_widget else "",
                    debit_amount=line_debit, credit_amount=line_credit,
                    tax_code=tax_combo.currentData() if tax_combo and tax_combo.currentData() else None, 
                    tax_amount=Decimal(tax_amt_item_widget.text().replace(',', '')) if tax_amt_item_widget and tax_amt_item_widget.text() else Decimal(0),
                    currency_code="SGD", exchange_rate=Decimal(1), # Defaults for now
                    dimension1_id=None, dimension2_id=None 
                )
                lines_data.append(line_dto)
                total_debits += line_debit; total_credits += line_credit
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Error processing line {row + 1}: {e}"); return None
        
        if not lines_data:
             QMessageBox.warning(self, "Input Error", "Journal entry must have at least one valid line."); return None
        if abs(total_debits - total_credits) > Decimal("0.01"):
            QMessageBox.warning(self, "Balance Error", f"Journal entry is not balanced. Debits: {total_debits:,.2f}, Credits: {total_credits:,.2f}."); return None

        try:
            # Get source_type/id from loaded ORM if editing, otherwise None for new.
            # self.loaded_journal_entry_orm is set in _load_existing_journal_entry
            source_type = self.loaded_journal_entry_orm.source_type if self.journal_entry_id and self.loaded_journal_entry_orm else None
            source_id = self.loaded_journal_entry_orm.source_id if self.journal_entry_id and self.loaded_journal_entry_orm else None
            
            entry_data = JournalEntryData(
                journal_type=self.journal_type_combo.currentText(),
                entry_date=self.entry_date_edit.date().toPython(),
                description=self.description_edit.text().strip() or None,
                reference=self.reference_edit.text().strip() or None,
                user_id=self.current_user_id, lines=lines_data,
                source_type=source_type, source_id=source_id
                # is_recurring, recurring_pattern_id are not set by this generic dialog directly.
            )
            return entry_data
        except ValueError as e: 
            QMessageBox.warning(self, "Validation Error", str(e)); return None

    @Slot()
    def on_save_draft(self):
        # ... (same as previous version)
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted):
            QMessageBox.information(self, "Info", "Cannot save. Entry is posted or in view-only mode.")
            return
        entry_data = self._collect_data()
        if entry_data: schedule_task_from_qt(self._perform_save(entry_data, post_after_save=False))

    @Slot()
    def on_save_and_post(self):
        # ... (same as previous version)
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted):
            QMessageBox.information(self, "Info", "Cannot save and post. Entry is already posted or in view-only mode.")
            return
        entry_data = self._collect_data()
        if entry_data: schedule_task_from_qt(self._perform_save(entry_data, post_after_save=True))

    async def _perform_save(self, entry_data: JournalEntryData, post_after_save: bool):
        # ... (same as previous version, ensuring Result type hint)
        manager = self.app_core.journal_entry_manager
        if not manager:
             QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
             return

        result: Result[JournalEntry] # Explicit type hint
        if self.journal_entry_id and self.loaded_journal_entry_orm: 
            result = await manager.update_journal_entry(self.journal_entry_id, entry_data)
        else: 
            result = await manager.create_journal_entry(entry_data)

        if result.is_success:
            saved_je = result.value
            assert saved_je is not None
            if post_after_save:
                post_result: Result[JournalEntry] = await manager.post_journal_entry(saved_je.id, self.current_user_id)
                if post_result.is_success:
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved and posted successfully."))
                    self.journal_entry_saved.emit(saved_je.id)
                    QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
                else:
                    error_msg = f"Journal entry saved as draft (ID: {saved_je.id}), but failed to post:\n{', '.join(post_result.errors)}"
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Posting Error"), Q_ARG(str, error_msg))
                    self.journal_entry_saved.emit(saved_je.id) 
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved as draft successfully."))
                self.journal_entry_saved.emit(saved_je.id)
                QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save journal entry:\n{', '.join(result.errors)}"))


    def open(self) -> int: 
        # ... (same as previous version, with more thorough reset)
        if not self.journal_entry_id and not self.view_only_mode : 
            self.setWindowTitle("New Journal Entry") # Reset title
            self.entry_date_edit.setDate(QDate.currentDate()); self.entry_date_edit.setReadOnly(False)
            self.journal_type_combo.setCurrentText(JournalTypeEnum.GENERAL.value); self.journal_type_combo.setEnabled(True)
            self.description_edit.clear(); self.description_edit.setReadOnly(False)
            self.reference_edit.clear(); self.reference_edit.setReadOnly(False)
            self.lines_table.setRowCount(0)
            self._add_new_line()
            self._add_new_line()
            self._calculate_totals()
            self.save_draft_button.setVisible(True); self.save_draft_button.setEnabled(True)
            self.save_post_button.setVisible(True); self.save_post_button.setEnabled(True)
            self.save_post_button.setText("Save & Post")
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.add_line_button.setEnabled(True); self.remove_line_button.setEnabled(True)
            
            # Ensure form layout fields are re-enabled
            for i in range(self.header_form.rowCount()):
                field_item = self.header_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if field_item:
                    widget = field_item.widget()
                    if isinstance(widget, (QLineEdit, QDateEdit)): widget.setReadOnly(False)
                    elif isinstance(widget, QComboBox): widget.setEnabled(True)
            
            # Ensure line delete buttons are visible if any rows exist
            for r in range(self.lines_table.rowCount()):
                del_btn_widget = self.lines_table.cellWidget(r, 6)
                if del_btn_widget: del_btn_widget.setVisible(True)

        return super().open()

```

# app/ui/accounting/account_dialog.py
```py
# File: app/ui/accounting/account_dialog.py
# (Content as previously updated and verified)
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QFormLayout, QMessageBox, QCheckBox, QDateEdit, QComboBox, 
                               QSpinBox, QHBoxLayout) 
from PySide6.QtCore import Slot, QDate, QTimer 
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData
from app.models.accounting.account import Account 
from app.core.application_core import ApplicationCore
from decimal import Decimal, InvalidOperation 
import asyncio 
from typing import Optional, cast 

class AccountDialog(QDialog):
    def __init__(self, app_core: ApplicationCore, current_user_id: int, account_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.account_id = account_id
        self.current_user_id = current_user_id 
        self.account: Optional[Account] = None 

        self.setWindowTitle("Add Account" if not account_id else "Edit Account")
        self.setMinimumWidth(450) 

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.code_edit = QLineEdit()
        self.name_edit = QLineEdit()
        
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(['Asset', 'Liability', 'Equity', 'Revenue', 'Expense'])
        
        self.sub_type_edit = QLineEdit() 
        self.description_edit = QLineEdit() 
        self.parent_id_spin = QSpinBox() 
        self.parent_id_spin.setRange(0, 999999) 
        self.parent_id_spin.setSpecialValueText("None (Root Account)")


        self.opening_balance_edit = QLineEdit("0.00") 
        self.opening_balance_date_edit = QDateEdit(QDate.currentDate())
        self.opening_balance_date_edit.setCalendarPopup(True)
        self.opening_balance_date_edit.setEnabled(False) 

        self.report_group_edit = QLineEdit()
        self.gst_applicable_check = QCheckBox()
        self.tax_treatment_edit = QLineEdit() 
        self.is_active_check = QCheckBox("Is Active")
        self.is_active_check.setChecked(True)
        self.is_control_account_check = QCheckBox("Is Control Account")
        self.is_bank_account_check = QCheckBox("Is Bank Account")
        
        self.form_layout.addRow("Code:", self.code_edit)
        self.form_layout.addRow("Name:", self.name_edit)
        self.form_layout.addRow("Account Type:", self.account_type_combo)
        self.form_layout.addRow("Sub Type:", self.sub_type_edit)
        self.form_layout.addRow("Parent Account ID:", self.parent_id_spin) 
        self.form_layout.addRow("Description:", self.description_edit)
        self.form_layout.addRow("Opening Balance:", self.opening_balance_edit)
        self.form_layout.addRow("OB Date:", self.opening_balance_date_edit)
        self.form_layout.addRow("Report Group:", self.report_group_edit)
        self.form_layout.addRow("GST Applicable:", self.gst_applicable_check)
        self.form_layout.addRow("Tax Treatment:", self.tax_treatment_edit)
        self.form_layout.addRow(self.is_active_check)
        self.form_layout.addRow(self.is_control_account_check)
        self.form_layout.addRow(self.is_bank_account_check)
        
        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.button_layout_bottom = QHBoxLayout() 
        self.button_layout_bottom.addStretch()
        self.button_layout_bottom.addWidget(self.save_button)
        self.button_layout_bottom.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout_bottom)

        self.save_button.clicked.connect(self.on_save)
        self.cancel_button.clicked.connect(self.reject)
        self.opening_balance_edit.textChanged.connect(self._on_ob_changed)

        if self.account_id:
            QTimer.singleShot(0, lambda: asyncio.ensure_future(self.load_account_data()))

    def _on_ob_changed(self, text: str):
        try:
            ob_val = Decimal(text)
            self.opening_balance_date_edit.setEnabled(ob_val != Decimal(0))
        except InvalidOperation: 
            self.opening_balance_date_edit.setEnabled(False)


    async def load_account_data(self):
        manager = self.app_core.accounting_service 
        if not manager or not hasattr(manager, 'account_service'): 
            QMessageBox.critical(self, "Error", "Accounting service or account_service attribute not available.")
            self.reject(); return

        self.account = await manager.account_service.get_by_id(self.account_id) # type: ignore
        if self.account:
            self.code_edit.setText(self.account.code)
            self.name_edit.setText(self.account.name)
            self.account_type_combo.setCurrentText(self.account.account_type)
            self.sub_type_edit.setText(self.account.sub_type or "")
            self.description_edit.setText(self.account.description or "")
            self.parent_id_spin.setValue(self.account.parent_id or 0)
            
            self.opening_balance_edit.setText(f"{self.account.opening_balance:.2f}")
            if self.account.opening_balance_date:
                self.opening_balance_date_edit.setDate(QDate.fromString(str(self.account.opening_balance_date), "yyyy-MM-dd"))
                self.opening_balance_date_edit.setEnabled(True)
            else:
                self.opening_balance_date_edit.setEnabled(False)
                self.opening_balance_date_edit.setDate(QDate.currentDate())


            self.report_group_edit.setText(self.account.report_group or "")
            self.gst_applicable_check.setChecked(self.account.gst_applicable)
            self.tax_treatment_edit.setText(self.account.tax_treatment or "")
            self.is_active_check.setChecked(self.account.is_active)
            self.is_control_account_check.setChecked(self.account.is_control_account)
            self.is_bank_account_check.setChecked(self.account.is_bank_account)
        else:
            QMessageBox.warning(self, "Error", f"Account ID {self.account_id} not found.")
            self.reject()

    @Slot()
    def on_save(self):
        try:
            ob_decimal = Decimal(self.opening_balance_edit.text())
        except InvalidOperation:
            QMessageBox.warning(self, "Input Error", "Invalid opening balance format. Please enter a valid number.")
            return

        parent_id_val = self.parent_id_spin.value()
        parent_id = parent_id_val if parent_id_val > 0 else None

        common_data = {
            "code": self.code_edit.text(),
            "name": self.name_edit.text(),
            "account_type": self.account_type_combo.currentText(),
            "sub_type": self.sub_type_edit.text() or None,
            "description": self.description_edit.text() or None,
            "parent_id": parent_id,
            "opening_balance": ob_decimal,
            "opening_balance_date": self.opening_balance_date_edit.date().toPython() if self.opening_balance_date_edit.isEnabled() else None,
            "report_group": self.report_group_edit.text() or None,
            "gst_applicable": self.gst_applicable_check.isChecked(),
            "tax_treatment": self.tax_treatment_edit.text() or None,
            "is_active": self.is_active_check.isChecked(),
            "is_control_account": self.is_control_account_check.isChecked(),
            "is_bank_account": self.is_bank_account_check.isChecked(),
            "user_id": self.current_user_id
        }

        try:
            if self.account_id:
                update_dto = AccountUpdateData(id=self.account_id, **common_data)
                asyncio.ensure_future(self._perform_update(update_dto))
            else:
                create_dto = AccountCreateData(**common_data)
                asyncio.ensure_future(self._perform_create(create_dto))
        except Exception as pydantic_error: 
             QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{pydantic_error}")


    async def _perform_create(self, data: AccountCreateData):
        manager = self.app_core.accounting_service 
        if not (manager and hasattr(manager, 'create_account')): 
            QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) not available.")
            return
        
        result = await manager.create_account(data) # type: ignore
        if result.is_success:
            QMessageBox.information(self, "Success", "Account created successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to create account:\n{', '.join(result.errors)}")

    async def _perform_update(self, data: AccountUpdateData):
        manager = self.app_core.accounting_service 
        if not (manager and hasattr(manager, 'update_account')):
            QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) not available.")
            return

        result = await manager.update_account(data) # type: ignore
        if result.is_success:
            QMessageBox.information(self, "Success", "Account updated successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to update account:\n{', '.join(result.errors)}")

```

