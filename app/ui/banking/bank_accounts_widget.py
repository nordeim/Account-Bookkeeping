# File: app/ui/banking/bank_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.bank_account_table_model import BankAccountTableModel
from app.ui.banking.bank_account_dialog import BankAccountDialog
from app.utils.pydantic_models import BankAccountSummaryData
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.bank_account import BankAccount # For Result type hint

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankAccountsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger())

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addLayout(self.filter_layout) 

        self.bank_accounts_table = QTableView()
        self.bank_accounts_table.setAlternatingRowColors(True)
        self.bank_accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bank_accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bank_accounts_table.horizontalHeader().setStretchLastSection(False)
        self.bank_accounts_table.doubleClicked.connect(self._on_edit_bank_account_double_click) 
        self.bank_accounts_table.setSortingEnabled(True)

        self.table_model = BankAccountTableModel()
        self.bank_accounts_table.setModel(self.table_model)
        
        header = self.bank_accounts_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.bank_accounts_table.setColumnHidden(id_col_idx, True)
        
        if "Account Name" in self.table_model._headers:
            name_col_idx = self.table_model._headers.index("Account Name")
            visible_name_idx = name_col_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_idx and self.bank_accounts_table.isColumnHidden(self.table_model._headers.index("ID")):
                visible_name_idx -=1
            if not self.bank_accounts_table.isColumnHidden(name_col_idx):
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 1: # Fallback
            header.setSectionResizeMode(0 if self.bank_accounts_table.isColumnHidden(0) else 1, QHeaderView.ResizeMode.Stretch)

        self.main_layout.addWidget(self.bank_accounts_table)
        self.setLayout(self.main_layout)

        if self.bank_accounts_table.selectionModel():
            self.bank_accounts_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Bank Accounts Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Bank Account", self)
        self.toolbar_add_action.triggered.connect(self._on_add_bank_account)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Bank Account", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_bank_account)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_bank_accounts()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout()
        self.filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All", None)
        self.status_filter_combo.addItem("Active", True)
        self.status_filter_combo.addItem("Inactive", False)
        self.status_filter_combo.currentIndexChanged.connect(self.toolbar_refresh_action.trigger)
        self.filter_layout.addWidget(self.status_filter_combo)
        self.filter_layout.addStretch()


    @Slot()
    def _update_action_states(self):
        selected_rows = self.bank_accounts_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_bank_accounts(self):
        if not self.app_core.bank_account_manager:
            self.app_core.logger.error("BankAccountManager not available.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Bank Account Manager not available."))
            return
        try:
            active_filter_data = self.status_filter_combo.currentData() # True, False, or None
            
            result: Result[List[BankAccountSummaryData]] = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(
                active_only=active_filter_data if isinstance(active_filter_data, bool) else None, # Pass None if "All"
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load bank accounts: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            summaries = [BankAccountSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate bank account data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_bank_account(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = BankAccountDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.bank_account_saved.connect(lambda _id: schedule_task_from_qt(self._load_bank_accounts()))
        dialog.exec()

    def _get_selected_bank_account_id(self) -> Optional[int]:
        selected_rows = self.bank_accounts_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1: return None
        return self.table_model.get_bank_account_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_bank_account(self):
        bank_account_id = self._get_selected_bank_account_id()
        if bank_account_id is None: QMessageBox.information(self, "Selection", "Please select a bank account."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = BankAccountDialog(self.app_core, self.app_core.current_user.id, bank_account_id=bank_account_id, parent=self)
        dialog.bank_account_saved.connect(lambda _id: schedule_task_from_qt(self._load_bank_accounts()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_edit_bank_account_double_click(self, index: QModelIndex): 
        if not index.isValid(): return
        bank_account_id = self.table_model.get_bank_account_id_at_row(index.row())
        if bank_account_id is None: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = BankAccountDialog(self.app_core, self.app_core.current_user.id, bank_account_id=bank_account_id, parent=self)
        dialog.bank_account_saved.connect(lambda _id: schedule_task_from_qt(self._load_bank_accounts()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        bank_account_id = self._get_selected_bank_account_id()
        if bank_account_id is None: QMessageBox.information(self, "Selection", "Please select a bank account."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
            
        is_currently_active = self.table_model.get_bank_account_status_at_row(self.bank_accounts_table.currentIndex().row())
        action_verb = "deactivate" if is_currently_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this bank account?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.bank_account_manager.toggle_bank_account_active_status(bank_account_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule status toggle."); return
        try:
            result: Result[BankAccount] = future.result()
            if result.is_success:
                QMessageBox.information(self, "Success", f"Bank account status changed successfully.")
                schedule_task_from_qt(self._load_bank_accounts()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle status:\n{', '.join(result.errors)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
