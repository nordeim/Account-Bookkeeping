# File: app/ui/company/new_company_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Slot
from typing import Optional, Dict
import re

class NewCompanyDialog(QDialog):
    def __init__(self, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Company File")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._company_details: Optional[Dict[str, str]] = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.company_name_edit = QLineEdit()
        self.company_name_edit.setPlaceholderText("e.g., My Awesome Bakery Pte. Ltd.")
        form_layout.addRow("Company Display Name*:", self.company_name_edit)

        self.db_name_edit = QLineEdit()
        self.db_name_edit.setPlaceholderText("e.g., my_awesome_bakery")
        form_layout.addRow("Database Name*:", self.db_name_edit)

        hint_label = QLabel("Database name must be lowercase, with no spaces or special characters (underscores are allowed).")
        hint_label.setWordWrap(True)
        form_layout.addRow("", hint_label)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.company_name_edit.textChanged.connect(self._auto_populate_db_name)

    @Slot(str)
    def _auto_populate_db_name(self, text: str):
        # Sanitize company name to suggest a valid DB name
        db_name_suggestion = text.lower()
        db_name_suggestion = re.sub(r'[^a-z0-9_]+', '_', db_name_suggestion) # Replace invalid chars with underscore
        db_name_suggestion = re.sub(r'__+', '_', db_name_suggestion) # Collapse multiple underscores
        db_name_suggestion = db_name_suggestion.strip('_') # Remove leading/trailing underscores
        self.db_name_edit.setText("sgb_" + db_name_suggestion[:40]) # Add prefix and limit length

    def _validate_input(self) -> bool:
        company_name = self.company_name_edit.text().strip()
        db_name = self.db_name_edit.text().strip()
        
        if not company_name:
            QMessageBox.warning(self, "Input Error", "Company Display Name cannot be empty.")
            return False
            
        if not db_name:
            QMessageBox.warning(self, "Input Error", "Database Name cannot be empty.")
            return False
            
        # PostgreSQL identifier rules (simplified): starts with letter or underscore,
        # subsequent can be letters, digits, or underscores.
        if not re.match(r'^[a-z_][a-z0-9_]*$', db_name):
            QMessageBox.warning(self, "Invalid Database Name", 
                "Database name must start with a lowercase letter or underscore, "
                "and contain only lowercase letters, numbers, and underscores.")
            return False
        
        return True

    @Slot()
    def _on_accept(self):
        if self._validate_input():
            self._company_details = {
                "display_name": self.company_name_edit.text().strip(),
                "database_name": self.db_name_edit.text().strip()
            }
            self.accept()

    def get_company_details(self) -> Optional[Dict[str, str]]:
        return self._company_details
