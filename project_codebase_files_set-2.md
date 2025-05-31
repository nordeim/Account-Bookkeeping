# app/ui/__init__.py
```py
# File: app/ui/__init__.py
# (Content as previously generated)
from .main_window import MainWindow

__all__ = ["MainWindow"]

```

# app/ui/settings/user_management_widget.py
```py
# File: app/ui/settings/user_management_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.settings.user_table_model import UserTableModel
from app.ui.settings.user_dialog import UserDialog 
from app.ui.settings.user_password_dialog import UserPasswordDialog # New import
from app.utils.pydantic_models import UserSummaryData
from app.utils.json_helpers import json_converter, json_date_hook 
from app.utils.result import Result
from app.models.core.user import User 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserManagementWidget(QWidget):
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
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_users()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.users_table = QTableView()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.users_table.horizontalHeader().setStretchLastSection(True) 
        self.users_table.setSortingEnabled(True)
        self.users_table.doubleClicked.connect(self._on_edit_user_double_click)


        self.table_model = UserTableModel()
        self.users_table.setModel(self.table_model)
        
        header = self.users_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.users_table.setColumnHidden(id_col_idx, True)
        
        fn_col_idx = self.table_model._headers.index("Full Name") if "Full Name" in self.table_model._headers else -1
        email_col_idx = self.table_model._headers.index("Email") if "Email" in self.table_model._headers else -1

        if fn_col_idx != -1 and not self.users_table.isColumnHidden(fn_col_idx) :
            header.setSectionResizeMode(fn_col_idx, QHeaderView.ResizeMode.Stretch)
        elif email_col_idx != -1 and not self.users_table.isColumnHidden(email_col_idx):
             header.setSectionResizeMode(email_col_idx, QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.users_table)
        self.setLayout(self.main_layout)

        if self.users_table.selectionModel():
            self.users_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("User Management Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add User", self)
        self.toolbar_add_action.triggered.connect(self._on_add_user)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit User", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_user)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar_change_password_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Change Password", self)
        self.toolbar_change_password_action.triggered.connect(self._on_change_password)
        self.toolbar.addAction(self.toolbar_change_password_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_users()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _update_action_states(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_modify = False
        is_current_user_selected = False
        is_system_init_user_selected = False

        if single_selection:
            can_modify = True
            row = selected_rows[0].row()
            user_id = self.table_model.get_user_id_at_row(row)
            username = self.table_model.get_username_at_row(row)

            if self.app_core.current_user and user_id == self.app_core.current_user.id:
                is_current_user_selected = True
            if username == "system_init_user": 
                is_system_init_user_selected = True
        
        self.toolbar_edit_action.setEnabled(can_modify and not is_system_init_user_selected)
        self.toolbar_toggle_active_action.setEnabled(can_modify and not is_current_user_selected and not is_system_init_user_selected)
        self.toolbar_change_password_action.setEnabled(can_modify and not is_system_init_user_selected)

    async def _load_users(self):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Security Manager component not available."))
            return
        try:
            summaries: List[UserSummaryData] = await self.app_core.security_manager.get_all_users_summary()
            json_data = json.dumps([s.model_dump(mode='json') for s in summaries])
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e:
            self.app_core.logger.error(f"Unexpected error loading users: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading users: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            user_summaries: List[UserSummaryData] = [UserSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(user_summaries)
        except Exception as e: 
            self.app_core.logger.error(f"Failed to parse/validate user data for table: {e}", exc_info=True)
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate user data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_user(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = UserDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.user_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_user_id_and_username(self) -> tuple[Optional[int], Optional[str]]: # Modified to return username too
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None, None
        row_index = selected_rows[0].row()
        user_id = self.table_model.get_user_id_at_row(row_index)
        username = self.table_model.get_username_at_row(row_index)
        return user_id, username


    @Slot()
    def _on_edit_user(self):
        user_id, username = self._get_selected_user_id_and_username()
        if user_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single user to edit.")
            return
        
        if username == "system_init_user":
            QMessageBox.warning(self, "Action Denied", "The 'system_init_user' cannot be edited from the UI.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = UserDialog(self.app_core, self.app_core.current_user.id, user_id_to_edit=user_id, parent=self)
        dialog.user_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot(QModelIndex)
    def _on_edit_user_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        user_id = self.table_model.get_user_id_at_row(index.row())
        username = self.table_model.get_username_at_row(index.row())
        if user_id is None: return
        
        if username == "system_init_user":
            QMessageBox.warning(self, "Action Denied", "The 'system_init_user' cannot be edited from the UI.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = UserDialog(self.app_core, self.app_core.current_user.id, user_id_to_edit=user_id, parent=self)
        dialog.user_saved.connect(self._refresh_list_after_save)
        dialog.exec()


    @Slot()
    def _on_toggle_active_status(self):
        user_id, username = self._get_selected_user_id_and_username()
        if user_id is None: QMessageBox.information(self, "Selection", "Please select a single user to toggle status."); return
        
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if user_id == self.app_core.current_user.id:
            QMessageBox.warning(self, "Action Denied", "You cannot change the active status of your own account.")
            return
            
        if username == "system_init_user":
             QMessageBox.warning(self, "Action Denied", "The 'system_init_user' status cannot be modified from the UI.")
             return

        current_row_idx = self.users_table.currentIndex().row()
        is_currently_active = self.table_model.get_user_active_status_at_row(current_row_idx)
        action_verb = "deactivate" if is_currently_active else "activate"
        
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} user account '{username}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.security_manager.toggle_user_active_status(user_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None) 

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule user status toggle."); return
        try:
            result: Result[User] = future.result()
            if result.is_success and result.value:
                action_verb_past = "activated" if result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"User account '{result.value.username}' {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_users()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle user status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for user: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    @Slot()
    def _on_change_password(self):
        user_id, username = self._get_selected_user_id_and_username()
        if user_id is None: 
            QMessageBox.information(self, "Selection", "Please select a user to change password.")
            return
        
        if username == "system_init_user":
            QMessageBox.warning(self, "Action Denied", "Password for 'system_init_user' cannot be changed from the UI.")
            return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in.")
            return

        dialog = UserPasswordDialog(
            self.app_core, 
            self.app_core.current_user.id, # User performing the change
            user_id_to_change=user_id,
            username_to_change=username if username else "Selected User", # Fallback for username
            parent=self
        )
        # password_changed signal doesn't strictly need connection if just a success msg is enough
        # If list needs refresh due to some password related field, connect it.
        # dialog.password_changed.connect(lambda changed_user_id: self.app_core.logger.info(f"Password changed for user {changed_user_id}"))
        dialog.exec()
    
    @Slot(int)
    def _refresh_list_after_save(self, user_id: int): # Renamed from on_user_saved
        self.app_core.logger.info(f"UserDialog reported save for User ID: {user_id}. Refreshing user list.")
        schedule_task_from_qt(self._load_users())

```

# app/ui/settings/__init__.py
```py
# File: app/ui/settings/__init__.py
from .settings_widget import SettingsWidget
from .user_management_widget import UserManagementWidget 
from .user_table_model import UserTableModel 
from .user_dialog import UserDialog 
from .user_password_dialog import UserPasswordDialog 
from .role_management_widget import RoleManagementWidget # New export
from .role_table_model import RoleTableModel # New export
from .role_dialog import RoleDialog # New export


__all__ = [
    "SettingsWidget",
    "UserManagementWidget", 
    "UserTableModel",       
    "UserDialog", 
    "UserPasswordDialog",
    "RoleManagementWidget", # New export
    "RoleTableModel",       # New export
    "RoleDialog",           # New export
]

```

# app/ui/settings/role_table_model.py
```py
# File: app/ui/settings/role_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any

from app.utils.pydantic_models import RoleData # Use RoleData DTO

class RoleTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[RoleData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Name", "Description"]
        self._data: List[RoleData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            # Allow UserRole for ID retrieval
            if role == Qt.ItemDataRole.UserRole and index.column() == 0 and 0 <= index.row() < len(self._data):
                return self._data[index.row()].id
            return None
        
        row = index.row(); col = index.column()
        if not (0 <= row < len(self._data)): return None
            
        role_data: RoleData = self._data[row]

        if col == 0: return str(role_data.id)
        if col == 1: return role_data.name
        if col == 2: return role_data.description or ""
            
        return None

    def get_role_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Try UserRole first for consistency if data() method is updated to store it
            idx = self.index(row, 0)
            role_id = self.data(idx, Qt.ItemDataRole.UserRole)
            if role_id is not None: return int(role_id)
            return self._data[row].id 
        return None
        
    def get_role_name_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].name
        return None

    def update_data(self, new_data: List[RoleData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/settings/user_password_dialog.py
```py
# File: app/ui/settings/user_password_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, TYPE_CHECKING

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import UserPasswordChangeData
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserPasswordDialog(QDialog):
    password_changed = Signal(int) # Emits user_id_to_change

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int,
                 user_id_to_change: int,
                 username_to_change: str,
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.user_id_to_change = user_id_to_change
        self.username_to_change = username_to_change

        self.setWindowTitle(f"Change Password for {self.username_to_change}")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        info_label = QLabel(f"Changing password for user: <b>{self.username_to_change}</b> (ID: {self.user_id_to_change})")
        main_layout.addWidget(info_label)

        form_layout = QFormLayout()
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit.setPlaceholderText("Enter new password (min 8 characters)")
        form_layout.addRow("New Password*:", self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm new password")
        form_layout.addRow("Confirm New Password*:", self.confirm_password_edit)
        
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)
        
        self.new_password_edit.setFocus()


    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_ok_clicked)
        self.button_box.rejected.connect(self.reject)

    def _collect_data(self) -> Optional[UserPasswordChangeData]:
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not new_password:
            QMessageBox.warning(self, "Validation Error", "New Password cannot be empty.")
            return None
        
        # Pydantic DTO will handle min_length and password match via its validator
        try:
            dto = UserPasswordChangeData(
                user_id_to_change=self.user_id_to_change,
                new_password=new_password,
                confirm_new_password=confirm_password,
                user_id=self.current_admin_user_id # User performing the change
            )
            return dto
        except ValueError as e: # Catches Pydantic validation errors
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(e)}")
            return None

    @Slot()
    def on_ok_clicked(self):
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_password_change(dto))
            if future:
                future.add_done_callback(
                    # Re-enable button regardless of outcome unless dialog is closed
                    lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
                )
            else: # Handle scheduling failure
                if ok_button: ok_button.setEnabled(True)
                QMessageBox.critical(self, "Task Error", "Failed to schedule password change operation.")


    async def _perform_password_change(self, dto: UserPasswordChangeData):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[None] = await self.app_core.security_manager.change_user_password(dto)

        if result.is_success:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self.parentWidget() if self.parentWidget() else self), # Show on parent if possible
                Q_ARG(str, "Success"), 
                Q_ARG(str, f"Password for user '{self.username_to_change}' changed successfully."))
            self.password_changed.emit(self.user_id_to_change)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Password Change Error"), 
                Q_ARG(str, f"Failed to change password:\n{', '.join(result.errors)}"))
            # Button re-enabled by callback in on_ok_clicked

```

# app/ui/settings/settings_widget.py
```py
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView,
                               QHBoxLayout, QTabWidget 
                               ) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QAbstractTableModel, QModelIndex 
from PySide6.QtGui import QColor, QFont 
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData, FiscalYearCreateData, FiscalYearData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from app.models.accounting.fiscal_year import FiscalYear 
from app.ui.accounting.fiscal_year_dialog import FiscalYearDialog 
from app.ui.settings.user_management_widget import UserManagementWidget 
from app.ui.settings.role_management_widget import RoleManagementWidget 
from decimal import Decimal, InvalidOperation
import asyncio
import json 
from typing import Optional, List, Any, Dict 
from app.main import schedule_task_from_qt 
from datetime import date as python_date, datetime 
from app.utils.json_helpers import json_converter, json_date_hook 

class FiscalYearTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[FiscalYearData]] = None, parent=None): 
        super().__init__(parent)
        self._headers = ["Name", "Start Date", "End Date", "Status"]
        self._data: List[FiscalYearData] = data or []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): 
            return None
        
        try:
            fy = self._data[index.row()]
            column = index.column()

            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0: return fy.year_name
                if column == 1: return fy.start_date.strftime('%d/%m/%Y') if isinstance(fy.start_date, python_date) else str(fy.start_date)
                if column == 2: return fy.end_date.strftime('%d/%m/%Y') if isinstance(fy.end_date, python_date) else str(fy.end_date)
                if column == 3: return "Closed" if fy.is_closed else "Open"
            elif role == Qt.ItemDataRole.FontRole:
                if column == 3: 
                    font = QFont()
                    if fy.is_closed:
                        pass 
                    else: 
                        font.setBold(True)
                    return font
            elif role == Qt.ItemDataRole.ForegroundRole:
                 if column == 3 and not fy.is_closed: 
                    return QColor("green")
        except IndexError:
            return None 
        return None

    def get_fiscal_year_at_row(self, row: int) -> Optional[FiscalYearData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
        
    def update_data(self, new_data: List[FiscalYearData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._loaded_settings_obj: Optional[CompanySetting] = None 
        
        self.main_layout = QVBoxLayout(self) 
        self.tab_widget = QTabWidget() 
        self.main_layout.addWidget(self.tab_widget)

        # --- Company Settings Tab ---
        self.company_settings_tab = QWidget()
        company_tab_layout = QVBoxLayout(self.company_settings_tab) 

        company_settings_group = QGroupBox("Company Information")
        company_settings_form_layout = QFormLayout(company_settings_group) 

        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        self.base_currency_combo = QComboBox() 
        self.address_line1_edit = QLineEdit()
        self.address_line2_edit = QLineEdit()
        self.postal_code_edit = QLineEdit()
        self.city_edit = QLineEdit()
        self.country_edit = QLineEdit()
        self.contact_person_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.website_edit = QLineEdit()
        self.fiscal_year_start_month_spin = QSpinBox()
        self.fiscal_year_start_month_spin.setRange(1, 12)
        self.fiscal_year_start_day_spin = QSpinBox()
        self.fiscal_year_start_day_spin.setRange(1,31)
        self.tax_id_label_edit = QLineEdit()
        self.date_format_combo = QComboBox() 
        self.date_format_combo.addItems(["dd/MM/yyyy", "yyyy-MM-dd", "MM/dd/yyyy"])

        company_settings_form_layout.addRow("Company Name*:", self.company_name_edit)
        company_settings_form_layout.addRow("Legal Name:", self.legal_name_edit)
        company_settings_form_layout.addRow("UEN No:", self.uen_edit)
        company_settings_form_layout.addRow("GST Reg. No:", self.gst_reg_edit)
        company_settings_form_layout.addRow(self.gst_registered_check)
        company_settings_form_layout.addRow("Base Currency:", self.base_currency_combo)
        company_settings_form_layout.addRow("Address Line 1:", self.address_line1_edit)
        company_settings_form_layout.addRow("Address Line 2:", self.address_line2_edit)
        company_settings_form_layout.addRow("Postal Code:", self.postal_code_edit)
        company_settings_form_layout.addRow("City:", self.city_edit)
        company_settings_form_layout.addRow("Country:", self.country_edit)
        company_settings_form_layout.addRow("Contact Person:", self.contact_person_edit)
        company_settings_form_layout.addRow("Phone:", self.phone_edit)
        company_settings_form_layout.addRow("Email:", self.email_edit)
        company_settings_form_layout.addRow("Website:", self.website_edit)
        company_settings_form_layout.addRow("Fiscal Year Start Month:", self.fiscal_year_start_month_spin)
        company_settings_form_layout.addRow("Fiscal Year Start Day:", self.fiscal_year_start_day_spin)
        company_settings_form_layout.addRow("Tax ID Label:", self.tax_id_label_edit)
        company_settings_form_layout.addRow("Date Format:", self.date_format_combo)
        
        self.save_company_settings_button = QPushButton("Save Company Settings")
        self.save_company_settings_button.clicked.connect(self.on_save_company_settings)
        company_settings_form_layout.addRow(self.save_company_settings_button)
        
        company_tab_layout.addWidget(company_settings_group)
        company_tab_layout.addStretch() 
        self.tab_widget.addTab(self.company_settings_tab, "Company")

        # --- Fiscal Year Management Tab ---
        self.fiscal_year_tab = QWidget()
        fiscal_tab_main_layout = QVBoxLayout(self.fiscal_year_tab)
        
        fiscal_year_group = QGroupBox("Fiscal Year Management")
        fiscal_year_group_layout = QVBoxLayout(fiscal_year_group) 

        self.fiscal_years_table = QTableView()
        self.fiscal_years_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fiscal_years_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.fiscal_years_table.horizontalHeader().setStretchLastSection(True)
        self.fiscal_years_table.setMinimumHeight(150) 
        self.fiscal_year_model = FiscalYearTableModel() 
        self.fiscal_years_table.setModel(self.fiscal_year_model)
        fiscal_year_group_layout.addWidget(self.fiscal_years_table)

        fy_button_layout = QHBoxLayout() 
        self.add_fy_button = QPushButton("Add New Fiscal Year...")
        self.add_fy_button.clicked.connect(self.on_add_fiscal_year)
        fy_button_layout.addWidget(self.add_fy_button)
        fy_button_layout.addStretch()
        fiscal_year_group_layout.addLayout(fy_button_layout)
        
        fiscal_tab_main_layout.addWidget(fiscal_year_group)
        fiscal_tab_main_layout.addStretch() 
        self.tab_widget.addTab(self.fiscal_year_tab, "Fiscal Years")

        # --- User Management Tab ---
        self.user_management_widget = UserManagementWidget(self.app_core)
        self.tab_widget.addTab(self.user_management_widget, "Users")

        # --- Role Management Tab ---
        self.role_management_widget = RoleManagementWidget(self.app_core)
        self.tab_widget.addTab(self.role_management_widget, "Roles & Permissions")
        
        self.setLayout(self.main_layout) 

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_initial_data()))

    async def load_initial_data(self):
        await self.load_company_settings()
        await self._load_fiscal_years() 

    async def load_company_settings(self):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        
        currencies_loaded_successfully = False
        active_currencies_data: List[Dict[str, str]] = [] 
        if self.app_core.currency_manager:
            try:
                active_currencies_orm: List[Currency] = await self.app_core.currency_manager.get_active_currencies()
                for curr in active_currencies_orm:
                    active_currencies_data.append({"code": curr.code, "name": curr.name})
                QMetaObject.invokeMethod(self, "_populate_currency_combo_slot", Qt.ConnectionType.QueuedConnection, 
                                         Q_ARG(str, json.dumps(active_currencies_data)))
                currencies_loaded_successfully = True
            except Exception as e:
                error_msg = f"Error loading currencies for settings: {e}"
                self.app_core.logger.error(error_msg, exc_info=True) 
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Currency Load Error"), Q_ARG(str, error_msg))
        
        if not currencies_loaded_successfully: 
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        self._loaded_settings_obj = settings_obj 
        
        settings_data_for_ui_json: Optional[str] = None
        if settings_obj:
            settings_dict = { col.name: getattr(settings_obj, col.name) for col in CompanySetting.__table__.columns }
            settings_data_for_ui_json = json.dumps(settings_dict, default=json_converter)
        
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, settings_data_for_ui_json if settings_data_for_ui_json else ""))

    @Slot(str) 
    def _populate_currency_combo_slot(self, currencies_json_str: str): 
        try: currencies_data: List[Dict[str,str]] = json.loads(currencies_json_str)
        except json.JSONDecodeError: currencies_data = [{"code": "SGD", "name": "Singapore Dollar"}] 
            
        current_selection = self.base_currency_combo.currentData()
        self.base_currency_combo.clear()
        if currencies_data: 
            for curr_data in currencies_data: self.base_currency_combo.addItem(f"{curr_data['code']} - {curr_data['name']}", curr_data['code']) 
        
        target_currency_code = current_selection
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj and self._loaded_settings_obj.base_currency:
            target_currency_code = self._loaded_settings_obj.base_currency
        
        if target_currency_code:
            idx = self.base_currency_combo.findData(target_currency_code) 
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD") 
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        elif self.base_currency_combo.count() > 0: self.base_currency_combo.setCurrentIndex(0)

    @Slot(str) 
    def _update_ui_from_settings_slot(self, settings_json_str: str):
        settings_data: Optional[Dict[str, Any]] = None
        if settings_json_str:
            try:
                settings_data = json.loads(settings_json_str, object_hook=json_date_hook)
            except json.JSONDecodeError: 
                QMessageBox.critical(self, "Error", "Failed to parse settings data."); settings_data = None

        if settings_data:
            self.company_name_edit.setText(settings_data.get("company_name", ""))
            self.legal_name_edit.setText(settings_data.get("legal_name", "") or "")
            self.uen_edit.setText(settings_data.get("uen_no", "") or "")
            self.gst_reg_edit.setText(settings_data.get("gst_registration_no", "") or "")
            self.gst_registered_check.setChecked(settings_data.get("gst_registered", False))
            self.address_line1_edit.setText(settings_data.get("address_line1", "") or "")
            self.address_line2_edit.setText(settings_data.get("address_line2", "") or "")
            self.postal_code_edit.setText(settings_data.get("postal_code", "") or "")
            self.city_edit.setText(settings_data.get("city", "Singapore") or "Singapore")
            self.country_edit.setText(settings_data.get("country", "Singapore") or "Singapore")
            self.contact_person_edit.setText(settings_data.get("contact_person", "") or "")
            self.phone_edit.setText(settings_data.get("phone", "") or "")
            self.email_edit.setText(settings_data.get("email", "") or "")
            self.website_edit.setText(settings_data.get("website", "") or "")
            self.fiscal_year_start_month_spin.setValue(settings_data.get("fiscal_year_start_month", 1))
            self.fiscal_year_start_day_spin.setValue(settings_data.get("fiscal_year_start_day", 1))
            self.tax_id_label_edit.setText(settings_data.get("tax_id_label", "UEN") or "UEN")
            
            date_fmt = settings_data.get("date_format", "dd/MM/yyyy") 
            date_fmt_idx = self.date_format_combo.findText(date_fmt, Qt.MatchFlag.MatchFixedString)
            if date_fmt_idx != -1: self.date_format_combo.setCurrentIndex(date_fmt_idx)
            else: self.date_format_combo.setCurrentIndex(0) 

            if self.base_currency_combo.count() > 0: 
                base_currency = settings_data.get("base_currency")
                if base_currency:
                    idx = self.base_currency_combo.findData(base_currency) 
                    if idx != -1: 
                        self.base_currency_combo.setCurrentIndex(idx)
                    else: 
                        idx_sgd = self.base_currency_combo.findData("SGD")
                        if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        else:
            if not self._loaded_settings_obj : 
                 QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")

    @Slot()
    def on_save_company_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return
        selected_currency_code = self.base_currency_combo.currentData() or "SGD"
        dto = CompanySettingData(
            id=1, 
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None, uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None, gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            address_line1=self.address_line1_edit.text() or None, address_line2=self.address_line2_edit.text() or None,
            postal_code=self.postal_code_edit.text() or None, city=self.city_edit.text() or "Singapore",
            country=self.country_edit.text() or "Singapore", contact_person=self.contact_person_edit.text() or None,
            phone=self.phone_edit.text() or None, email=self.email_edit.text() or None, 
            website=self.website_edit.text() or None,
            fiscal_year_start_month=self.fiscal_year_start_month_spin.value(), 
            fiscal_year_start_day=self.fiscal_year_start_day_spin.value(),  
            base_currency=selected_currency_code, 
            tax_id_label=self.tax_id_label_edit.text() or "UEN",       
            date_format=self.date_format_combo.currentText() or "dd/MM/yyyy", 
            logo=None 
        )
        schedule_task_from_qt(self.perform_save_company_settings(dto))

    async def perform_save_company_settings(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            update_dict = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            for field_name, field_value in update_dict.items():
                if hasattr(orm_obj_to_save, field_name): 
                    if field_name == 'email' and field_value is not None: 
                        setattr(orm_obj_to_save, field_name, str(field_value))
                    else:
                        setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            if 'email' in dict_data and dict_data['email'] is not None: dict_data['email'] = str(dict_data['email'])
            orm_obj_to_save = CompanySetting(**dict_data) # type: ignore
            if settings_data.id: orm_obj_to_save.id = settings_data.id 
        
        if self.app_core.current_user: orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 
        result_orm = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        message_title = "Success" if result_orm else "Error"
        message_text = "Company settings saved successfully." if result_orm else "Failed to save company settings."
        msg_box_method = QMessageBox.information if result_orm else QMessageBox.warning
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))

    async def _load_fiscal_years(self):
        if not self.app_core.fiscal_period_manager:
            self.app_core.logger.error("FiscalPeriodManager not available in SettingsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Service Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return
        try:
            fy_orms: List[FiscalYear] = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            fy_dtos_for_table: List[FiscalYearData] = []
            for fy_orm in fy_orms:
                fy_dtos_for_table.append(FiscalYearData(
                    id=fy_orm.id, year_name=fy_orm.year_name, start_date=fy_orm.start_date,
                    end_date=fy_orm.end_date, is_closed=fy_orm.is_closed, closed_date=fy_orm.closed_date,
                    periods=[] 
                ))
            
            fy_json_data = json.dumps([dto.model_dump(mode='json') for dto in fy_dtos_for_table])
            QMetaObject.invokeMethod(self, "_update_fiscal_years_table_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, fy_json_data))
        except Exception as e:
            error_msg = f"Error loading fiscal years: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Fiscal Year Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_fiscal_years_table_slot(self, fy_json_list_str: str):
        try:
            fy_dict_list = json.loads(fy_json_list_str, object_hook=json_date_hook) 
            fy_dtos: List[FiscalYearData] = [FiscalYearData.model_validate(item_dict) for item_dict in fy_dict_list]
            self.fiscal_year_model.update_data(fy_dtos)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse fiscal year data: {e}")
        except Exception as e_val: 
            QMessageBox.critical(self, "Data Error", f"Invalid fiscal year data format: {e_val}")

    @Slot()
    def on_add_fiscal_year(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        
        dialog = FiscalYearDialog(self.app_core, self.app_core.current_user.id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fy_create_data = dialog.get_fiscal_year_data()
            if fy_create_data:
                schedule_task_from_qt(self._perform_add_fiscal_year(fy_create_data))

    async def _perform_add_fiscal_year(self, fy_data: FiscalYearCreateData):
        if not self.app_core.fiscal_period_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return

        result: Result[FiscalYear] = await self.app_core.fiscal_period_manager.create_fiscal_year_and_periods(fy_data)

        if result.is_success:
            assert result.value is not None
            msg = f"Fiscal Year '{result.value.year_name}' created successfully."
            if fy_data.auto_generate_periods:
                msg += f" {fy_data.auto_generate_periods} periods generated."
            
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, msg))
            schedule_task_from_qt(self._load_fiscal_years()) 
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Failed to create fiscal year:\n{', '.join(result.errors)}"))

```

# app/ui/settings/user_table_model.py
```py
# File: app/ui/settings/user_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.utils.pydantic_models import UserSummaryData

class UserTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[UserSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Username", "Full Name", "Email", "Roles", "Active", "Last Login"]
        self._data: List[UserSummaryData] = data or []

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
            
        user_summary: UserSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_')
            
            if col == 0: return str(user_summary.id)
            if col == 1: return user_summary.username
            if col == 2: return user_summary.full_name or ""
            if col == 3: return str(user_summary.email) if user_summary.email else ""
            if col == 4: return ", ".join(user_summary.roles) if user_summary.roles else "N/A"
            if col == 5: return "Yes" if user_summary.is_active else "No"
            if col == 6: 
                # Ensure last_login is datetime before formatting
                last_login_val = user_summary.last_login
                if isinstance(last_login_val, str): # It might come as ISO string from JSON
                    try:
                        last_login_val = datetime.fromisoformat(last_login_val.replace('Z', '+00:00'))
                    except ValueError:
                        return "Invalid Date" # Or keep original string
                
                return last_login_val.strftime('%d/%m/%Y %H:%M') if isinstance(last_login_val, datetime) else "Never"
            
            return str(getattr(user_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: # Store ID with the first column
                return user_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_user_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None: return int(id_val)
            return self._data[row].id 
        return None
        
    def get_user_active_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None
        
    def get_username_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].username
        return None

    def update_data(self, new_data: List[UserSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/settings/role_management_widget.py
```py
# File: app/ui/settings/role_management_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QPushButton, QToolBar, 
    QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.settings.role_table_model import RoleTableModel
from app.ui.settings.role_dialog import RoleDialog # Import RoleDialog
from app.utils.pydantic_models import RoleData
from app.utils.json_helpers import json_converter
from app.utils.result import Result
from app.models.core.user import Role 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class RoleManagementWidget(QWidget):
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
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_roles()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.roles_table = QTableView()
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.roles_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.roles_table.horizontalHeader().setStretchLastSection(True) 
        self.roles_table.setSortingEnabled(True)
        self.roles_table.doubleClicked.connect(self._on_edit_role_double_click)

        self.table_model = RoleTableModel()
        self.roles_table.setModel(self.table_model)
        
        header = self.roles_table.horizontalHeader()
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.roles_table.setColumnHidden(id_col_idx, True)
        
        header.setSectionResizeMode(self.table_model._headers.index("Name"), QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.table_model._headers.index("Description"), QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.roles_table)
        self.setLayout(self.main_layout)

        if self.roles_table.selectionModel():
            self.roles_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Role Management Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Role", self)
        self.toolbar_add_action.triggered.connect(self._on_add_role)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Role", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_role)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_delete_action = QAction(QIcon(self.icon_path_prefix + "remove.svg"), "Delete Role", self)
        self.toolbar_delete_action.triggered.connect(self._on_delete_role)
        self.toolbar.addAction(self.toolbar_delete_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_roles()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _update_action_states(self):
        selected_rows = self.roles_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_modify = False
        is_admin_role_selected = False

        if single_selection:
            can_modify = True
            row_idx = selected_rows[0].row()
            role_name = self.table_model.get_role_name_at_row(row_idx)
            if role_name == "Administrator":
                is_admin_role_selected = True
        
        self.toolbar_edit_action.setEnabled(can_modify) 
        self.toolbar_delete_action.setEnabled(can_modify and not is_admin_role_selected)

    async def _load_roles(self):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Security Manager component not available."))
            return
        try:
            roles_orm: List[Role] = await self.app_core.security_manager.get_all_roles()
            roles_dto: List[RoleData] = [RoleData.model_validate(r) for r in roles_orm]
            json_data = json.dumps([r.model_dump() for r in roles_dto], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e:
            self.app_core.logger.error(f"Unexpected error loading roles: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading roles: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str) 
            role_dtos: List[RoleData] = [RoleData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(role_dtos)
        except Exception as e: 
            self.app_core.logger.error(f"Failed to parse/validate role data for table: {e}", exc_info=True)
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate role data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_role(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_role_id(self) -> Optional[int]:
        selected_rows = self.roles_table.selectionModel().selectedRows()
        if not selected_rows: return None
        if len(selected_rows) > 1: return None # Only operate on single selection for edit/delete
        return self.table_model.get_role_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_role(self):
        role_id = self._get_selected_role_id()
        if role_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single role to edit.")
            return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        role_name = self.table_model.get_role_name_at_row(self.roles_table.currentIndex().row())
        if role_name == "Administrator" and self.name_edit.text().strip() != "Administrator": # self.name_edit does not exist here. This check is in RoleDialog.
             # This check is better placed within RoleDialog or SecurityManager. For now, allow opening.
             pass

        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, role_id_to_edit=role_id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot(QModelIndex)
    def _on_edit_role_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        role_id = self.table_model.get_role_id_at_row(index.row())
        if role_id is None: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, role_id_to_edit=role_id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_delete_role(self):
        role_id = self._get_selected_role_id()
        if role_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single role to delete.")
            return
        
        role_name = self.table_model.get_role_name_at_row(self.roles_table.currentIndex().row())
        if role_name == "Administrator":
            QMessageBox.warning(self, "Action Denied", "The 'Administrator' role cannot be deleted.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete the role '{role_name}' (ID: {role_id})?\nThis action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.security_manager.delete_role(role_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_delete_role_result)
        else: self._handle_delete_role_result(None)

    def _handle_delete_role_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule role deletion."); return
        try:
            result: Result[None] = future.result()
            if result.is_success:
                QMessageBox.information(self, "Success", "Role deleted successfully.")
                schedule_task_from_qt(self._load_roles()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete role:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling role deletion result: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during role deletion: {str(e)}")
        finally:
            self._update_action_states() 

    @Slot(int)
    def _refresh_list_after_save(self, role_id: int):
        self.app_core.logger.info(f"RoleDialog reported save for Role ID: {role_id}. Refreshing role list.")
        schedule_task_from_qt(self._load_roles())

```

# app/ui/settings/role_dialog.py
```py
# app/ui/settings/role_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QLabel, QTextEdit, QListWidget, QListWidgetItem, QAbstractItemView,
    QGroupBox 
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import RoleCreateData, RoleUpdateData, RoleData, PermissionData
from app.models.core.user import Role # ORM for loading
from app.utils.result import Result
from app.utils.json_helpers import json_converter

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class RoleDialog(QDialog):
    role_saved = Signal(int) # Emits role ID

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int, 
                 role_id_to_edit: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.role_id_to_edit = role_id_to_edit
        self.loaded_role_orm: Optional[Role] = None
        self._all_permissions_cache: List[PermissionData] = []


        self.is_new_role = self.role_id_to_edit is None
        self.setWindowTitle("Add New Role" if self.is_new_role else "Edit Role")
        self.setMinimumWidth(500) 
        self.setMinimumHeight(450)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_data()))

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        details_group = QGroupBox("Role Details")
        form_layout = QFormLayout(details_group)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter role name (e.g., Sales Manager)")
        form_layout.addRow("Role Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter a brief description for this role.")
        self.description_edit.setFixedHeight(60) 
        form_layout.addRow("Description:", self.description_edit)
        main_layout.addWidget(details_group)
        
        permissions_group = QGroupBox("Assign Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        self.permissions_list_widget = QListWidget()
        self.permissions_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        permissions_layout.addWidget(self.permissions_list_widget)
        main_layout.addWidget(permissions_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)
        
    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save)
        self.button_box.rejected.connect(self.reject)

    async def _load_initial_data(self):
        """Load all available permissions and role data if editing."""
        perms_loaded_successfully = False
        try:
            if self.app_core.security_manager:
                # Fetch all permissions for the list widget
                self._all_permissions_cache = await self.app_core.security_manager.get_all_permissions()
                perms_json = json.dumps([p.model_dump() for p in self._all_permissions_cache]) # Use model_dump for Pydantic v2
                QMetaObject.invokeMethod(self, "_populate_permissions_list_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, perms_json))
                perms_loaded_successfully = True
        except Exception as e:
            self.app_core.logger.error(f"Error loading permissions for RoleDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load permissions: {str(e)}")
        
        if not perms_loaded_successfully:
            self.permissions_list_widget.addItem("Error loading permissions.")
            self.permissions_list_widget.setEnabled(False)

        # If editing, load the specific role's data (which includes its assigned permissions)
        if self.role_id_to_edit:
            try:
                if self.app_core.security_manager:
                    # get_role_by_id should eager load role.permissions
                    self.loaded_role_orm = await self.app_core.security_manager.get_role_by_id(self.role_id_to_edit)
                    if self.loaded_role_orm:
                        assigned_perm_ids = [p.id for p in self.loaded_role_orm.permissions]
                        role_dict = {
                            "id": self.loaded_role_orm.id, "name": self.loaded_role_orm.name,
                            "description": self.loaded_role_orm.description,
                            "assigned_permission_ids": assigned_perm_ids
                        }
                        role_json_str = json.dumps(role_dict, default=json_converter)
                        # This slot will populate fields and then call _select_assigned_permissions
                        QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, role_json_str))
                    else:
                        QMessageBox.warning(self, "Load Error", f"Role ID {self.role_id_to_edit} not found.")
                        self.reject()
            except Exception as e:
                 self.app_core.logger.error(f"Error loading role (ID: {self.role_id_to_edit}) for edit: {e}", exc_info=True)
                 QMessageBox.warning(self, "Load Error", f"Could not load role details: {str(e)}"); self.reject()
        elif self.is_new_role : # New role
            self.name_edit.setFocus()


    @Slot(str)
    def _populate_permissions_list_slot(self, permissions_json_str: str):
        self.permissions_list_widget.clear()
        try:
            permissions_data_list = json.loads(permissions_json_str)
            # Cache already updated in _load_initial_data, or update it here if preferred
            self._all_permissions_cache = [PermissionData.model_validate(p_dict) for p_dict in permissions_data_list]
            for perm_dto in self._all_permissions_cache:
                item_text = f"{perm_dto.module}: {perm_dto.code}"
                if perm_dto.description: item_text += f" - {perm_dto.description}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, perm_dto.id) 
                self.permissions_list_widget.addItem(item)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing permissions JSON for RoleDialog: {e}")
            self.permissions_list_widget.addItem("Error parsing permissions.")
        
        # If editing and role data was already loaded (which triggered field population),
        # and field population triggered _select_assigned_permissions, this re-selection might be redundant
        # or necessary if permissions list is populated after fields.
        # This is generally safe.
        if self.role_id_to_edit and self.loaded_role_orm:
            self._select_assigned_permissions([p.id for p in self.loaded_role_orm.permissions])


    @Slot(str)
    def _populate_fields_slot(self, role_json_str: str):
        try:
            role_data = json.loads(role_json_str) 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse role data for editing."); return

        self.name_edit.setText(role_data.get("name", ""))
        self.description_edit.setText(role_data.get("description", "") or "")

        is_admin_role = (role_data.get("name") == "Administrator")
        self.name_edit.setReadOnly(is_admin_role)
        self.name_edit.setToolTip("The 'Administrator' role name cannot be changed." if is_admin_role else "")
        
        # For Admin role, all permissions should be selected and the list disabled.
        if is_admin_role:
            for i in range(self.permissions_list_widget.count()):
                self.permissions_list_widget.item(i).setSelected(True)
            self.permissions_list_widget.setEnabled(False) 
            self.permissions_list_widget.setToolTip("Administrator role has all permissions by default and cannot be modified here.")
        else:
            self.permissions_list_widget.setEnabled(True)
            assigned_permission_ids = role_data.get("assigned_permission_ids", [])
            self._select_assigned_permissions(assigned_permission_ids)


    def _select_assigned_permissions(self, assigned_ids: List[int]):
        # Ensure this is called after permissions_list_widget is populated
        if self.permissions_list_widget.count() == 0 and self._all_permissions_cache:
             # Permissions list might not be populated yet if this is called too early from _populate_fields_slot
             # _load_initial_data should ensure permissions are populated first then calls _populate_fields_slot
             # which then calls this.
             self.app_core.logger.warning("_select_assigned_permissions called before permissions list populated.")
             return

        for i in range(self.permissions_list_widget.count()):
            item = self.permissions_list_widget.item(i)
            permission_id_in_item = item.data(Qt.ItemDataRole.UserRole)
            if permission_id_in_item in assigned_ids:
                item.setSelected(True)
            else:
                item.setSelected(False) 

    def _collect_data(self) -> Optional[Union[RoleCreateData, RoleUpdateData]]:
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip() or None
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Role Name is required.")
            return None
        
        # Cannot change name of Administrator role if editing it (already handled by read-only)
        if self.loaded_role_orm and self.loaded_role_orm.name == "Administrator" and name != "Administrator":
             QMessageBox.warning(self, "Validation Error", "Cannot change the name of 'Administrator' role.")
             self.name_edit.setText("Administrator") # Reset
             return None

        selected_permission_ids: List[int] = []
        if self.permissions_list_widget.isEnabled(): # Only collect if list is enabled (not admin role)
            for item in self.permissions_list_widget.selectedItems():
                perm_id = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(perm_id, int):
                    selected_permission_ids.append(perm_id)
        elif self.loaded_role_orm and self.loaded_role_orm.name == "Administrator":
            # For admin, all permissions are implicitly assigned if list is disabled
            selected_permission_ids = [p.id for p in self._all_permissions_cache]


        common_data = {"name": name, "description": description, "permission_ids": selected_permission_ids}

        try:
            if self.is_new_role:
                return RoleCreateData(**common_data) 
            else:
                assert self.role_id_to_edit is not None
                return RoleUpdateData(id=self.role_id_to_edit, **common_data) 
        except ValueError as pydantic_error: 
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
            return None

    @Slot()
    def on_save(self):
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_save(dto))
            if future:
                future.add_done_callback(
                    lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
                )
            else: 
                if ok_button: ok_button.setEnabled(True)

    async def _perform_save(self, dto: Union[RoleCreateData, RoleUpdateData]):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[Role]
        action_verb_present = "update" if isinstance(dto, RoleUpdateData) else "create"
        action_verb_past = "updated" if isinstance(dto, RoleUpdateData) else "created"

        if isinstance(dto, RoleUpdateData):
            result = await self.app_core.security_manager.update_role(dto, self.current_admin_user_id)
        else: 
            result = await self.app_core.security_manager.create_role(dto, self.current_admin_user_id)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self.parentWidget() if self.parentWidget() else self), 
                Q_ARG(str, "Success"), 
                Q_ARG(str, f"Role '{result.value.name}' {action_verb_past} successfully."))
            self.role_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to {action_verb_present} role:\n{', '.join(result.errors)}"))


```

# app/ui/settings/user_dialog.py
```py
# File: app/ui/settings/user_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QListWidget, QListWidgetItem, QAbstractItemView,
    QLabel
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union, cast

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import UserCreateData, UserUpdateData, RoleData
from app.models.core.user import User, Role # For ORM type hints
from app.utils.result import Result
from app.utils.json_helpers import json_converter # For serializing roles if needed

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserDialog(QDialog):
    user_saved = Signal(int) # Emits user ID

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int, 
                 user_id_to_edit: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.user_id_to_edit = user_id_to_edit
        self.loaded_user_orm: Optional[User] = None
        self._all_roles_cache: List[RoleData] = []

        self.is_new_user = self.user_id_to_edit is None
        self.setWindowTitle("Add New User" if self.is_new_user else "Edit User")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_data()))

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.username_edit = QLineEdit()
        form_layout.addRow("Username*:", self.username_edit)

        self.full_name_edit = QLineEdit()
        form_layout.addRow("Full Name:", self.full_name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("user@example.com")
        form_layout.addRow("Email:", self.email_edit)

        self.password_label = QLabel("Password*:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(self.password_label, self.password_edit)

        self.confirm_password_label = QLabel("Confirm Password*:")
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(self.confirm_password_label, self.confirm_password_edit)

        self.is_active_check = QCheckBox("User is Active")
        self.is_active_check.setChecked(True)
        form_layout.addRow(self.is_active_check)
        
        form_layout.addRow(QLabel("Assign Roles:"))
        self.roles_list_widget = QListWidget()
        self.roles_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.roles_list_widget.setFixedHeight(120) # Adjust height as needed
        form_layout.addRow(self.roles_list_widget)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        if not self.is_new_user: # Editing existing user
            self.password_label.setVisible(False)
            self.password_edit.setVisible(False)
            self.confirm_password_label.setVisible(False)
            self.confirm_password_edit.setVisible(False)
            # Username might be non-editable for existing users for simplicity, or based on permissions
            # self.username_edit.setReadOnly(True) 


    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save)
        self.button_box.rejected.connect(self.reject)

    async def _load_initial_data(self):
        """Load all available roles and user data if editing."""
        roles_loaded_successfully = False
        try:
            if self.app_core.security_manager:
                roles_orm: List[Role] = await self.app_core.security_manager.get_all_roles()
                self._all_roles_cache = [RoleData.model_validate(r) for r in roles_orm]
                roles_json = json.dumps([r.model_dump() for r in self._all_roles_cache], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_roles_list_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, roles_json))
                roles_loaded_successfully = True
        except Exception as e:
            self.app_core.logger.error(f"Error loading roles for UserDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load roles: {str(e)}")

        if not roles_loaded_successfully:
            self.roles_list_widget.addItem("Error loading roles.")
            self.roles_list_widget.setEnabled(False)

        if self.user_id_to_edit:
            try:
                if self.app_core.security_manager:
                    self.loaded_user_orm = await self.app_core.security_manager.get_user_by_id_for_edit(self.user_id_to_edit)
                    if self.loaded_user_orm:
                        # Serialize user data for thread-safe UI update
                        user_dict = {
                            "id": self.loaded_user_orm.id,
                            "username": self.loaded_user_orm.username,
                            "full_name": self.loaded_user_orm.full_name,
                            "email": self.loaded_user_orm.email,
                            "is_active": self.loaded_user_orm.is_active,
                            "assigned_role_ids": [role.id for role in self.loaded_user_orm.roles]
                        }
                        user_json_str = json.dumps(user_dict, default=json_converter)
                        QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, user_json_str))
                    else:
                        QMessageBox.warning(self, "Load Error", f"User ID {self.user_id_to_edit} not found.")
                        self.reject() # Close dialog if user not found
            except Exception as e:
                 self.app_core.logger.error(f"Error loading user (ID: {self.user_id_to_edit}) for edit: {e}", exc_info=True)
                 QMessageBox.warning(self, "Load Error", f"Could not load user details: {str(e)}")
                 self.reject()


    @Slot(str)
    def _populate_roles_list_slot(self, roles_json_str: str):
        self.roles_list_widget.clear()
        try:
            roles_data_list = json.loads(roles_json_str)
            self._all_roles_cache = [RoleData.model_validate(r_dict) for r_dict in roles_data_list]
            for role_dto in self._all_roles_cache:
                item = QListWidgetItem(f"{role_dto.name} ({role_dto.description or 'No description'})")
                item.setData(Qt.ItemDataRole.UserRole, role_dto.id) # Store role ID
                self.roles_list_widget.addItem(item)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing roles JSON for UserDialog: {e}")
            self.roles_list_widget.addItem("Error parsing roles.")
        
        # If editing, and user data already loaded, re-select roles
        if self.user_id_to_edit and self.loaded_user_orm:
            self._select_assigned_roles([role.id for role in self.loaded_user_orm.roles])


    @Slot(str)
    def _populate_fields_slot(self, user_json_str: str):
        try:
            user_data = json.loads(user_json_str) # No json_date_hook needed for UserSummaryData fields
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse user data for editing."); return

        self.username_edit.setText(user_data.get("username", ""))
        self.full_name_edit.setText(user_data.get("full_name", "") or "")
        self.email_edit.setText(user_data.get("email", "") or "")
        self.is_active_check.setChecked(user_data.get("is_active", True))
        
        assigned_role_ids = user_data.get("assigned_role_ids", [])
        self._select_assigned_roles(assigned_role_ids)

        if self.loaded_user_orm and self.loaded_user_orm.username == "system_init_user":
            self._set_read_only_for_system_user()

    def _select_assigned_roles(self, assigned_role_ids: List[int]):
        for i in range(self.roles_list_widget.count()):
            item = self.roles_list_widget.item(i)
            role_id_in_item = item.data(Qt.ItemDataRole.UserRole)
            if role_id_in_item in assigned_role_ids:
                item.setSelected(True)
            else:
                item.setSelected(False)
    
    def _set_read_only_for_system_user(self):
        self.username_edit.setReadOnly(True)
        self.full_name_edit.setReadOnly(True)
        self.email_edit.setReadOnly(True)
        self.is_active_check.setEnabled(False) # Cannot deactivate system_init
        self.roles_list_widget.setEnabled(False) # Cannot change roles of system_init
        # Password fields are already hidden for edit mode
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False) # Prevent saving changes


    def _collect_data(self) -> Optional[Union[UserCreateData, UserUpdateData]]:
        username = self.username_edit.text().strip()
        full_name = self.full_name_edit.text().strip() or None
        email_str = self.email_edit.text().strip() or None
        is_active = self.is_active_check.isChecked()
        
        selected_role_ids: List[int] = []
        for item in self.roles_list_widget.selectedItems():
            role_id = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(role_id, int):
                selected_role_ids.append(role_id)
        
        common_data = {
            "username": username, "full_name": full_name, "email": email_str,
            "is_active": is_active, "assigned_role_ids": selected_role_ids,
            "user_id": self.current_admin_user_id # The user performing the action
        }

        try:
            if self.is_new_user:
                password = self.password_edit.text()
                confirm_password = self.confirm_password_edit.text()
                if not password: # Basic check, Pydantic handles min_length
                     QMessageBox.warning(self, "Validation Error", "Password is required for new users.")
                     return None
                return UserCreateData(password=password, confirm_password=confirm_password, **common_data) # type: ignore
            else:
                assert self.user_id_to_edit is not None
                return UserUpdateData(id=self.user_id_to_edit, **common_data) # type: ignore
        except ValueError as pydantic_error: # Catches Pydantic validation errors
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
            return None

    @Slot()
    def on_save(self):
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_save(dto))
            if future:
                future.add_done_callback(
                    lambda _: ok_button.setEnabled(True) if ok_button else None
                )
            else: # Handle scheduling failure
                if ok_button: ok_button.setEnabled(True)


    async def _perform_save(self, dto: Union[UserCreateData, UserUpdateData]):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[User]
        if isinstance(dto, UserCreateData):
            result = await self.app_core.security_manager.create_user_with_roles(dto)
        elif isinstance(dto, UserUpdateData):
            result = await self.app_core.security_manager.update_user_from_dto(dto)
        else: # Should not happen
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Invalid DTO type for save."))
            return

        if result.is_success and result.value:
            action = "updated" if self.user_id_to_edit else "created"
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"User '{result.value.username}' {action} successfully."))
            self.user_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save user:\n{', '.join(result.errors)}"))

```

# app/ui/banking/__init__.py
```py
# File: app/ui/banking/__init__.py
# (Content as previously generated)
from .banking_widget import BankingWidget

__all__ = ["BankingWidget"]

```

# app/ui/banking/banking_widget.py
```py
# File: app/ui/banking/banking_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore

class BankingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Banking Operations Widget (Bank Accounts, Reconciliation - To be implemented)")
        self.setLayout(self.layout)

```

# app/ui/products/__init__.py
```py
# app/ui/products/__init__.py
from .product_table_model import ProductTableModel
from .product_dialog import ProductDialog
from .products_widget import ProductsWidget # New export

__all__ = [
    "ProductTableModel",
    "ProductDialog",
    "ProductsWidget", # Added to __all__
]


```

# app/ui/products/product_table_model.py
```py
# app/ui/products/product_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation

from app.utils.pydantic_models import ProductSummaryData # Using the DTO for type safety
from app.common.enums import ProductTypeEnum # For displaying enum value

class ProductTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[ProductSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers match fields in ProductSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Type", "Sales Price", "Purchase Price", "Active"]
        self._data: List[ProductSummaryData] = data or []

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
        if value is None: return ""
        try:
            return f"{Decimal(str(value)):,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) # Fallback

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        product_summary: ProductSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_') # e.g. "Sales Price" -> "sales_price"
            
            if col == 0: return str(product_summary.id)
            if col == 1: return product_summary.product_code
            if col == 2: return product_summary.name
            if col == 3: return product_summary.product_type.value if isinstance(product_summary.product_type, ProductTypeEnum) else str(product_summary.product_type)
            if col == 4: return self._format_decimal_for_table(product_summary.sales_price)
            if col == 5: return self._format_decimal_for_table(product_summary.purchase_price)
            if col == 6: return "Yes" if product_summary.is_active else "No"
            
            # Fallback for safety (should be covered by above)
            return str(getattr(product_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: 
                return product_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Sales Price", "Purchase Price"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_product_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_product_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[ProductSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/products/products_widget.py
```py
# app/ui/products/products_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.products.product_table_model import ProductTableModel 
from app.ui.products.product_dialog import ProductDialog 
from app.utils.pydantic_models import ProductSummaryData 
from app.common.enums import ProductTypeEnum 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.product import Product 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class ProductsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for ProductsWidget.")
        except ImportError:
            self.app_core.logger.info("ProductsWidget: Compiled Qt resources not found. Using direct file paths.")
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_products()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Code, Name, Description...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.search_edit)

        filter_layout.addWidget(QLabel("Type:"))
        self.product_type_filter_combo = QComboBox()
        self.product_type_filter_combo.addItem("All Types", None) 
        for pt_enum in ProductTypeEnum:
            self.product_type_filter_combo.addItem(pt_enum.value, pt_enum) 
        self.product_type_filter_combo.currentIndexChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.product_type_filter_combo)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"),"Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        self.products_table = QTableView()
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(False)
        self.products_table.doubleClicked.connect(self._on_edit_product_double_click) 
        self.products_table.setSortingEnabled(True)

        self.table_model = ProductTableModel()
        self.products_table.setModel(self.table_model)
        
        header = self.products_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.products_table.setColumnHidden(id_col_idx, True)
        
        name_col_idx = self.table_model._headers.index("Name") if "Name" in self.table_model._headers else -1
        if name_col_idx != -1:
            visible_name_idx = name_col_idx
            if id_col_idx != -1 and id_col_idx < name_col_idx and self.products_table.isColumnHidden(id_col_idx): # Check if ID column is actually hidden
                visible_name_idx -=1
            
            # Check if the model column corresponding to name_col_idx is not hidden before stretching
            if not self.products_table.isColumnHidden(name_col_idx): # Use model index for isColumnHidden
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 2 : 
            # Fallback: if ID (model index 0) is hidden, stretch second visible column (model index 2 -> visible 1)
            # This assumes "Code" is model index 1 (visible 0) and "Name" is model index 2 (visible 1)
            # If headers are ["ID", "Code", "Name", ...], and ID is hidden, visible Name is index 1.
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.products_table)
        self.setLayout(self.main_layout)

        if self.products_table.selectionModel():
            self.products_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Product/Service Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Product/Service", self)
        self.toolbar_add_action.triggered.connect(self._on_add_product)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Product/Service", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_product)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_products()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.product_type_filter_combo.setCurrentIndex(0) 
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_products())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_products(self):
        if not self.app_core.product_manager:
            self.app_core.logger.error("ProductManager not available in ProductsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Product Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            product_type_enum_filter: Optional[ProductTypeEnum] = self.product_type_filter_combo.currentData()
            
            result: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(
                active_only=active_only, 
                product_type_filter=product_type_enum_filter,
                search_term=search_term,
                page=1, 
                page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load products/services: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading products/services: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            product_summaries: List[ProductSummaryData] = [ProductSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(product_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse product/service data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid product/service data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_product(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a product/service.")
            return
        
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    def _get_selected_product_id(self) -> Optional[int]:
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None
        return self.table_model.get_product_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_product(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a product/service.")
            return
            
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_edit_product_double_click(self, index: QModelIndex): 
        if not index.isValid(): return
        product_id = self.table_model.get_product_id_at_row(index.row())
        if product_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit product/service.")
            return
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change product/service status.")
            return
            
        current_row = self.products_table.currentIndex().row()
        if current_row < 0: # Should not happen if product_id is not None
            return

        product_status_active = self.table_model.get_product_status_at_row(current_row)
        action_verb = "deactivate" if product_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this product/service?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.product_manager.toggle_product_active_status(product_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule product/service status toggle."); return
        try:
            result: Result[Product] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Product/Service {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_products()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle product/service status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for product/service: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/products/product_dialog.py
```py
# app/ui/products/product_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QCompleter
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import ProductCreateData, ProductUpdateData
from app.models.business.product import Product
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.common.enums import ProductTypeEnum # Enum for product type
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class ProductDialog(QDialog):
    product_saved = Signal(int) # Emits product ID on successful save

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 product_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.product_id = product_id
        self.loaded_product_data: Optional[Product] = None 

        self._sales_accounts_cache: List[Account] = []
        self._purchase_accounts_cache: List[Account] = []
        self._inventory_accounts_cache: List[Account] = []
        self._tax_codes_cache: List[TaxCode] = []
        
        self.setWindowTitle("Edit Product/Service" if self.product_id else "Add New Product/Service")
        self.setMinimumWidth(600)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        if self.product_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_product_details()))
        else: # For new product, trigger initial UI state based on default product type
            self._on_product_type_changed(self.product_type_combo.currentData().value if self.product_type_combo.currentData() else ProductTypeEnum.SERVICE.value)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.product_code_edit = QLineEdit(); form_layout.addRow("Code*:", self.product_code_edit)
        self.name_edit = QLineEdit(); form_layout.addRow("Name*:", self.name_edit)
        self.description_edit = QTextEdit(); self.description_edit.setFixedHeight(60); form_layout.addRow("Description:", self.description_edit)

        self.product_type_combo = QComboBox()
        for pt_enum in ProductTypeEnum: self.product_type_combo.addItem(pt_enum.value, pt_enum) # Store Enum member as data
        form_layout.addRow("Product Type*:", self.product_type_combo)

        self.category_edit = QLineEdit(); form_layout.addRow("Category:", self.category_edit)
        self.unit_of_measure_edit = QLineEdit(); form_layout.addRow("Unit of Measure:", self.unit_of_measure_edit)
        self.barcode_edit = QLineEdit(); form_layout.addRow("Barcode:", self.barcode_edit)
        
        self.sales_price_spin = QDoubleSpinBox(); self.sales_price_spin.setDecimals(2); self.sales_price_spin.setRange(0, 99999999.99); self.sales_price_spin.setGroupSeparatorShown(True); form_layout.addRow("Sales Price:", self.sales_price_spin)
        self.purchase_price_spin = QDoubleSpinBox(); self.purchase_price_spin.setDecimals(2); self.purchase_price_spin.setRange(0, 99999999.99); self.purchase_price_spin.setGroupSeparatorShown(True); form_layout.addRow("Purchase Price:", self.purchase_price_spin)
        
        self.sales_account_combo = QComboBox(); self.sales_account_combo.setMinimumWidth(200); form_layout.addRow("Sales Account:", self.sales_account_combo)
        self.purchase_account_combo = QComboBox(); self.purchase_account_combo.setMinimumWidth(200); form_layout.addRow("Purchase Account:", self.purchase_account_combo)
        
        self.inventory_account_label = QLabel("Inventory Account*:") # For toggling visibility
        self.inventory_account_combo = QComboBox(); self.inventory_account_combo.setMinimumWidth(200)
        form_layout.addRow(self.inventory_account_label, self.inventory_account_combo)
        
        self.tax_code_combo = QComboBox(); self.tax_code_combo.setMinimumWidth(150); form_layout.addRow("Default Tax Code:", self.tax_code_combo)
        
        stock_group = QGroupBox("Inventory Details (for 'Inventory' type products)")
        stock_layout = QFormLayout(stock_group)
        self.min_stock_level_spin = QDoubleSpinBox(); self.min_stock_level_spin.setDecimals(2); self.min_stock_level_spin.setRange(0, 999999.99); stock_layout.addRow("Min. Stock Level:", self.min_stock_level_spin)
        self.reorder_point_spin = QDoubleSpinBox(); self.reorder_point_spin.setDecimals(2); self.reorder_point_spin.setRange(0, 999999.99); stock_layout.addRow("Reorder Point:", self.reorder_point_spin)
        form_layout.addRow(stock_group)
        self.stock_details_group_box = stock_group # Store reference to toggle visibility

        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True); form_layout.addRow(self.is_active_check)
        
        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_product)
        self.button_box.rejected.connect(self.reject)
        self.product_type_combo.currentDataChanged.connect(self._on_product_type_changed_enum) # Use currentDataChanged for Enums

    @Slot(ProductTypeEnum) # Slot to receive the Enum member directly
    def _on_product_type_changed_enum(self, product_type_enum: Optional[ProductTypeEnum]):
        if product_type_enum:
            self._on_product_type_changed(product_type_enum.value)

    def _on_product_type_changed(self, product_type_value: str):
        is_inventory_type = (product_type_value == ProductTypeEnum.INVENTORY.value)
        self.inventory_account_label.setVisible(is_inventory_type)
        self.inventory_account_combo.setVisible(is_inventory_type)
        self.stock_details_group_box.setVisible(is_inventory_type)
        if not is_inventory_type: # Clear inventory specific fields if not applicable
            self.inventory_account_combo.setCurrentIndex(-1) # Or find "None" if added
            self.min_stock_level_spin.setValue(0)
            self.reorder_point_spin.setValue(0)


    async def _load_combo_data(self):
        try:
            coa_manager = self.app_core.chart_of_accounts_manager
            if coa_manager:
                self._sales_accounts_cache = await coa_manager.get_accounts_for_selection(account_type="Revenue", active_only=True)
                self._purchase_accounts_cache = await coa_manager.get_accounts_for_selection(account_type="Expense", active_only=True) # Could also be Asset
                self._inventory_accounts_cache = await coa_manager.get_accounts_for_selection(account_type="Asset", active_only=True)
            if self.app_core.tax_code_service:
                self._tax_codes_cache = await self.app_core.tax_code_service.get_all() # Assumes active

            # Serialize for thread-safe UI update
            def acc_to_dict(acc: Account): return {"id": acc.id, "code": acc.code, "name": acc.name}
            sales_acc_json = json.dumps(list(map(acc_to_dict, self._sales_accounts_cache)))
            purch_acc_json = json.dumps(list(map(acc_to_dict, self._purchase_accounts_cache)))
            inv_acc_json = json.dumps(list(map(acc_to_dict, self._inventory_accounts_cache)))
            tax_codes_json = json.dumps([{"code": tc.code, "description": f"{tc.code} ({tc.rate}%)"} for tc in self._tax_codes_cache])

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, sales_acc_json), Q_ARG(str, purch_acc_json),
                                     Q_ARG(str, inv_acc_json), Q_ARG(str, tax_codes_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for ProductDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str, str, str)
    def _populate_combos_slot(self, sales_acc_json: str, purch_acc_json: str, inv_acc_json: str, tax_codes_json: str):
        def populate_combo(combo: QComboBox, json_str: str, data_key: str = "id", name_format="{code} - {name}", add_none=True):
            combo.clear()
            if add_none: combo.addItem("None", 0) # Using 0 as data for "None"
            try:
                items = json.loads(json_str)
                for item in items: combo.addItem(name_format.format(**item), item[data_key])
            except json.JSONDecodeError: self.app_core.logger.error(f"Error parsing JSON for {combo.objectName()}")

        populate_combo(self.sales_account_combo, sales_acc_json, add_none=True)
        populate_combo(self.purchase_account_combo, purch_acc_json, add_none=True)
        populate_combo(self.inventory_account_combo, inv_acc_json, add_none=True)
        populate_combo(self.tax_code_combo, tax_codes_json, data_key="code", name_format="{description}", add_none=True) # tax_code stores code string
        
        if self.loaded_product_data: # If editing, set current values after combos are populated
            self._populate_fields_from_orm(self.loaded_product_data)


    async def _load_existing_product_details(self):
        if not self.product_id or not self.app_core.product_manager: return
        self.loaded_product_data = await self.app_core.product_manager.get_product_for_dialog(self.product_id)
        if self.loaded_product_data:
            product_dict = {col.name: getattr(self.loaded_product_data, col.name) for col in Product.__table__.columns}
            product_json_str = json.dumps(product_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, product_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Product/Service ID {self.product_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, product_json_str: str):
        try:
            data = json.loads(product_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse product data for editing."); return
        self._populate_fields_from_dict(data)

    def _populate_fields_from_orm(self, product_orm: Product): # Called after combos populated, if editing
        def set_combo_by_data(combo: QComboBox, data_value: Any):
            if data_value is None and combo.itemData(0) == 0 : combo.setCurrentIndex(0); return # Select "None"
            idx = combo.findData(data_value)
            if idx != -1: combo.setCurrentIndex(idx)
            else: self.app_core.logger.warning(f"Value '{data_value}' for combo '{combo.objectName()}' not found.")
        
        set_combo_by_data(self.sales_account_combo, product_orm.sales_account_id)
        set_combo_by_data(self.purchase_account_combo, product_orm.purchase_account_id)
        set_combo_by_data(self.inventory_account_combo, product_orm.inventory_account_id)
        set_combo_by_data(self.tax_code_combo, product_orm.tax_code) # tax_code is string

    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.product_code_edit.setText(data.get("product_code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.description_edit.setText(data.get("description", "") or "")
        
        pt_enum_val = data.get("product_type") # This will be string value from DB
        pt_idx = self.product_type_combo.findData(ProductTypeEnum(pt_enum_val) if pt_enum_val else ProductTypeEnum.SERVICE, Qt.ItemDataRole.UserRole) # Find by Enum member
        if pt_idx != -1: self.product_type_combo.setCurrentIndex(pt_idx)
        self._on_product_type_changed(pt_enum_val if pt_enum_val else ProductTypeEnum.SERVICE.value) # Trigger UI update based on type

        self.category_edit.setText(data.get("category", "") or "")
        self.unit_of_measure_edit.setText(data.get("unit_of_measure", "") or "")
        self.barcode_edit.setText(data.get("barcode", "") or "")
        self.sales_price_spin.setValue(float(data.get("sales_price", 0.0) or 0.0))
        self.purchase_price_spin.setValue(float(data.get("purchase_price", 0.0) or 0.0))
        self.min_stock_level_spin.setValue(float(data.get("min_stock_level", 0.0) or 0.0))
        self.reorder_point_spin.setValue(float(data.get("reorder_point", 0.0) or 0.0))
        
        self.is_active_check.setChecked(data.get("is_active", True))
        
        # Combos are set by _populate_fields_from_orm if data was from ORM,
        # or if self.loaded_product_data is None (new entry), they will be default.
        # This call might be redundant if _populate_combos_slot already called _populate_fields_from_orm.
        if self.loaded_product_data: self._populate_fields_from_orm(self.loaded_product_data)


    @Slot()
    def on_save_product(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        sales_acc_id = self.sales_account_combo.currentData()
        purch_acc_id = self.purchase_account_combo.currentData()
        inv_acc_id = self.inventory_account_combo.currentData()
        tax_code_val = self.tax_code_combo.currentData()

        selected_product_type_enum = self.product_type_combo.currentData()
        if not isinstance(selected_product_type_enum, ProductTypeEnum):
            QMessageBox.warning(self, "Input Error", "Invalid product type selected."); return


        data_dict = {
            "product_code": self.product_code_edit.text().strip(), "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "product_type": selected_product_type_enum, # Pass the enum member
            "category": self.category_edit.text().strip() or None,
            "unit_of_measure": self.unit_of_measure_edit.text().strip() or None,
            "barcode": self.barcode_edit.text().strip() or None,
            "sales_price": Decimal(str(self.sales_price_spin.value())),
            "purchase_price": Decimal(str(self.purchase_price_spin.value())),
            "sales_account_id": int(sales_acc_id) if sales_acc_id and sales_acc_id !=0 else None,
            "purchase_account_id": int(purch_acc_id) if purch_acc_id and purch_acc_id !=0 else None,
            "inventory_account_id": int(inv_acc_id) if inv_acc_id and inv_acc_id !=0 and selected_product_type_enum == ProductTypeEnum.INVENTORY else None,
            "tax_code": str(tax_code_val) if tax_code_val else None,
            "is_active": self.is_active_check.isChecked(),
            "min_stock_level": Decimal(str(self.min_stock_level_spin.value())) if selected_product_type_enum == ProductTypeEnum.INVENTORY else None,
            "reorder_point": Decimal(str(self.reorder_point_spin.value())) if selected_product_type_enum == ProductTypeEnum.INVENTORY else None,
            "user_id": self.current_user_id
        }

        try:
            if self.product_id: dto = ProductUpdateData(id=self.product_id, **data_dict) # type: ignore
            else: dto = ProductCreateData(**data_dict) # type: ignore
        except ValueError as pydantic_error: 
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}"); return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button else None)

    async def _perform_save(self, dto: ProductCreateData | ProductUpdateData):
        if not self.app_core.product_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Product Manager not available."))
            return

        result: Result[Product]
        if isinstance(dto, ProductUpdateData): result = await self.app_core.product_manager.update_product(dto.id, dto)
        else: result = await self.app_core.product_manager.create_product(dto)

        if result.is_success and result.value:
            action = "updated" if isinstance(dto, ProductUpdateData) else "created"
            QMessageBox.information(self, "Success", f"Product/Service {action} successfully (ID: {result.value.id}).")
            self.product_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save product/service:\n{', '.join(result.errors)}"))


```

