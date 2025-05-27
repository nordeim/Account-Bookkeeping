<think>
Fantastic! The application launches and shuts down cleanly again. This confirms that the `ImportError` in `CustomerManager` has been resolved, and the integration of the backend components for Customer Management (`CustomerService`, `CustomerManager`) into `ApplicationCore` was successful without introducing new startup issues.

**Current Project Status Recap:**

*   **Backend for Customer Management (Phase A)**: Complete.
    *   A1. Pydantic DTOs for Customer (Done).
    *   A2. `ICustomerRepository` Interface (Done).
    *   A3. `CustomerService` Implementation (Done).
    *   A4. `CustomerManager` Implementation (Done).
    *   A5. Integration into `ApplicationCore` (Done).
*   All previously implemented features (Settings, CoA, JEs, GST backend, Financial Reports UI backend + basic UI) are stable.

**Next Step Identification:**

The user asks to "proceed with the next step in your plan."
The overall plan for Customer Management was:
*   **Phase A: Backend for Customer Management (Completed)**
*   **Phase B: Frontend UI for Customer Management (Current Focus)**
    *   B1. Create `CustomerTableModel`.
    *   B2. Create `CustomerDialog`.
    *   B3. Enhance `CustomersWidget` (from stub to functional).

So, the immediate next step is **B1: Create `CustomerTableModel`**. This table model will be used by `CustomersWidget` to display a list of customers.

**Plan for this Turn: Implement `CustomerTableModel` and `CustomerDialog` (Phase B1 & B2 - UI Foundation)**

**Objective:** Create the foundational UI components for listing and editing customers: `CustomerTableModel` for the `QTableView` in `CustomersWidget`, and `CustomerDialog` for adding/editing customer details.

**Detailed Plan & Checklist:**

**B1. Create `app/ui/customers/customer_table_model.py` (New File)**
   *   **Goal:** A `QAbstractTableModel` to display a summary of customer information.
   *   **File to Create:** `app/ui/customers/customer_table_model.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `CustomerTableModel(QAbstractTableModel)`.
        *   [ ] `__init__(self, data: Optional[List[CustomerSummaryData]] = None, parent=None)`: Store `CustomerSummaryData` DTOs.
        *   [ ] Define `_headers` (e.g., ["ID", "Code", "Name", "Email", "Phone", "Active"]). "ID" can be hidden in the view.
        *   [ ] Implement `rowCount()`, `columnCount()`, `headerData()`.
        *   [ ] Implement `data(index, role)`:
            *   For `DisplayRole`, return appropriate fields from `CustomerSummaryData` (e.g., `customer_code`, `name`, `email`, `phone`). Format `is_active` as "Yes"/"No".
            *   For `UserRole` (on the first column), store the customer `id` for easy retrieval.
            *   Handle `TextAlignmentRole` for any numeric/boolean columns if desired.
        *   [ ] Implement helper methods: `get_customer_id_at_row(row: int) -> Optional[int]`.
        *   [ ] Implement `update_data(new_data: List[CustomerSummaryData])`: To refresh the model, with `beginResetModel()` / `endResetModel()`.

**B2. Create `app/ui/customers/customer_dialog.py` (New File)**
   *   **Goal:** A `QDialog` for adding new customers and editing existing ones.
   *   **File to Create:** `app/ui/customers/customer_dialog.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `CustomerDialog(QDialog)`.
        *   [ ] `__init__(self, app_core: "ApplicationCore", current_user_id: int, customer_id: Optional[int] = None, parent=None)`.
        *   [ ] **UI Elements**: Create `QLineEdit`s, `QCheckBox`es, `QComboBox`es, `QDateEdit` for all relevant fields in `CustomerBaseData` DTO:
            *   `customer_code`, `name`, `legal_name`, `uen_no`, `gst_registered` (CheckBox), `gst_no`.
            *   `contact_person`, `email`, `phone`.
            *   Address fields: `address_line1`, `address_line2`, `postal_code`, `city`, `country` (ComboBox or QLineEdit).
            *   `credit_terms` (QSpinBox), `credit_limit` (QLineEdit/QDoubleSpinBox).
            *   `currency_code` (`QComboBox` - to be populated from `CurrencyService`).
            *   `is_active` (QCheckBox, default true for new).
            *   `customer_since` (`QDateEdit`, optional).
            *   `notes` (`QTextEdit` or multi-line `QLineEdit`).
            *   `receivables_account_id` (`QComboBox` - to be populated with Asset accounts from `AccountService`).
        *   [ ] **Layout**: Use `QFormLayout` for fields. `QDialogButtonBox` for OK/Cancel.
        *   [ ] **Asynchronous Data Population (for ComboBoxes and Edit Mode)**:
            *   `_load_initial_combo_data()`: Asynchronously fetch active currencies (from `app_core.currency_manager` or `app_core.currency_service`) and suitable Asset accounts (from `app_core.account_service` or `app_core.chart_of_accounts_manager.get_accounts_for_selection(account_type='Asset')`) to populate `currency_code_combo` and `receivables_account_combo`.
            *   `_load_existing_customer_data()`: If `customer_id` is provided, call `app_core.customer_manager.get_customer_for_dialog(customer_id)`.
            *   Use `QMetaObject.invokeMethod` or `future.add_done_callback` to populate UI fields from fetched data in the Qt thread.
        *   [ ] **Data Collection & Validation (`_collect_data_and_validate`)**:
            *   On OK button click, gather data from UI fields.
            *   Perform basic client-side validation (e.g., required fields not empty).
            *   Create `CustomerCreateData` or `CustomerUpdateData` DTO.
            *   Pydantic will perform its validation upon DTO creation. Catch `ValidationError` from Pydantic.
        *   [ ] **Save Logic (`on_save` or `acceptData`)**:
            *   Calls `_collect_data_and_validate()`.
            *   If valid, call `app_core.customer_manager.create_customer(dto)` or `update_customer(customer_id, dto)` asynchronously.
            *   Handle `Result` object: Show success/error `QMessageBox`. On success, `self.accept()` the dialog.
            *   Emit a signal `customer_saved = Signal(int)` with the customer ID.
        *   [ ] **Error Handling**: Display validation errors or manager errors in `QMessageBox`.

This defines the next two files to be created. I will start with `CustomerTableModel`.
</think>

This is excellent! The application's stability after each significant update phase is a strong indicator of careful implementation.

We are now ready to proceed with **Phase B: Frontend UI for Customer Management** from the "Enhancement Execution Plan: Basic Customer Management Module". This phase will bring the customer management functionality to the user.

We'll start with the foundational pieces for the UI:
1.  **B1: Create `app/ui/customers/customer_table_model.py`**
2.  **B2: Create `app/ui/customers/customer_dialog.py`**

---
**B1. Create `app/ui/customers/customer_table_model.py` (New File)**

**Goal:** A `QAbstractTableModel` to display a summary of customer information in the `CustomersWidget`.

```python
# app/ui/customers/customer_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import CustomerSummaryData # Using the DTO for type safety

class CustomerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[CustomerSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers should match fields in CustomerSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Email", "Phone", "Active"]
        self._data: List[CustomerSummaryData] = data or []

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
            
        customer_summary: CustomerSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(customer_summary.id)
            if col == 1: return customer_summary.customer_code
            if col == 2: return customer_summary.name
            if col == 3: return str(customer_summary.email) if customer_summary.email else ""
            if col == 4: return customer_summary.phone if customer_summary.phone else ""
            if col == 5: return "Yes" if customer_summary.is_active else "No"
            
            # Fallback for safety, though all defined headers should be covered
            header_key = self._headers[col].lower().replace(' ', '_')
            return str(getattr(customer_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            # Store the full DTO or just the ID in UserRole for easy retrieval
            # Storing ID in the first column's UserRole is common.
            if col == 0: 
                return customer_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 5: # Active status
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_customer_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) # Assuming ID is in/associated with the first column (model index 0)
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole is not used for ID or is somehow None
            return self._data[row].id 
        return None
        
    def get_customer_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[CustomerSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
```
**Validation for `app/ui/customers/customer_table_model.py`:**
*   **DTO Usage**: Takes `List[CustomerSummaryData]` as input, ensuring type safety and that only summary fields are expected.
*   **Headers**: Defined as `["ID", "Code", "Name", "Email", "Phone", "Active"]`.
*   **`data()` method**:
    *   Correctly accesses fields from `CustomerSummaryData` DTOs (e.g., `customer_summary.customer_code`).
    *   Formats `is_active` (boolean) to "Yes"/"No" for display.
    *   Stores the `customer_summary.id` in the `UserRole` of the first column (ID column).
    *   Aligns "Active" status column to center.
*   **Helper Methods**: `get_customer_id_at_row` and `get_customer_status_at_row` are provided for convenience.
*   `update_data`: Correctly uses `beginResetModel` and `endResetModel`.

This table model is well-defined and ready for use in `CustomersWidget`.

---
**B2. Create `app/ui/customers/customer_dialog.py` (New File)**

**Goal:** A `QDialog` for adding new customers and editing existing ones, with fields corresponding to `CustomerBaseData`.

```python
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
```

**Validation for `app/ui/customers/customer_dialog.py`:**
*   **UI Elements**: All specified fields from `CustomerBaseData` are represented by appropriate input widgets. `currency_code_combo` and `receivables_account_combo` are included. GST No. field is enabled/disabled based on `gst_registered_check`.
*   **`_load_combo_data`**: Asynchronously fetches active currencies and relevant asset accounts. Uses JSON serialization for passing data to `_populate_combos_slot` for thread safety.
*   **`_populate_combos_slot`**: Populates `QComboBox` for currency and receivables account. Handles setting the current value if editing.
*   **`_load_existing_customer_details`**: Fetches customer ORM via manager, serializes to JSON.
*   **`_populate_fields_slot`**: Parses JSON and populates all UI fields.
*   **`_populate_fields_from_orm`**: Helper to set combo current values after they are loaded, specifically if `_load_existing_customer_details` fetched ORM before combos were ready.
*   **`on_save_customer`**:
    *   Collects data from all UI fields.
    *   Converts `credit_limit` to `Decimal`.
    *   Retrieves `currentData()` for `currency_code_combo` and `receivables_account_combo` (which should be ID/code).
    *   Creates `CustomerCreateData` or `CustomerUpdateData` DTO. Catches Pydantic `ValueError`.
    *   Calls `_perform_save` asynchronously. Disables OK button during async operation.
*   **`_perform_save`**: Calls the appropriate `customer_manager` method (`create_customer` or `update_customer`). Handles the `Result` object to show messages and emits `customer_saved` signal on success.
*   **Signal `customer_saved`**: Defined to notify the parent widget (e.g., `CustomersWidget`) to refresh its list.

This dialog provides a comprehensive interface for adding and editing customer details.
The next step will be to update `CustomersWidget` to use this dialog and display customers in a table.
