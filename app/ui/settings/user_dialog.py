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
