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
