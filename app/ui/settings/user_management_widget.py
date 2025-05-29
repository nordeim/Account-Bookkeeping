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
