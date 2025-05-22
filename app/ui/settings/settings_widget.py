# File: app/ui/settings/settings_widget.py
# (Stub content as previously generated and lightly expanded)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFormLayout, QLineEdit, QMessageBox, QComboBox, QSpinBox, QDateEdit
from PySide6.QtCore import Slot, QDate, QTimer
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData 
from app.models.core.company_setting import CompanySetting
from decimal import Decimal, InvalidOperation
import asyncio
from typing import Optional


class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()
        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        # ... add more fields for address, contact, fiscal year, etc.
        self.base_currency_combo = QComboBox() # Populate with currencies
        # self.base_currency_combo.addItems(["SGD", "USD", "EUR"]) # Example

        self.form_layout.addRow("Company Name:", self.company_name_edit)
        self.form_layout.addRow("Legal Name:", self.legal_name_edit)
        self.form_layout.addRow("UEN No:", self.uen_edit)
        self.form_layout.addRow("GST Reg. No:", self.gst_reg_edit)
        self.form_layout.addRow(self.gst_registered_check)
        self.form_layout.addRow("Base Currency:", self.base_currency_combo)
        
        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.on_save_settings)
        self.layout.addWidget(self.save_button)
        self.layout.addStretch()

        self.setLayout(self.layout)
        QTimer.singleShot(0, lambda: asyncio.ensure_future(self.load_settings()))


    async def load_settings(self):
        if not self.app_core.company_settings_service:
            QMessageBox.critical(self, "Error", "Company Settings Service not available.")
            return
        
        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        if settings_obj:
            self.company_name_edit.setText(settings_obj.company_name)
            self.legal_name_edit.setText(settings_obj.legal_name or "")
            self.uen_edit.setText(settings_obj.uen_no or "")
            self.gst_reg_edit.setText(settings_obj.gst_registration_no or "")
            self.gst_registered_check.setChecked(settings_obj.gst_registered)
            # Find and set current currency in combo
            idx = self.base_currency_combo.findText(settings_obj.base_currency)
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
        else:
            QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")


    @Slot()
    def on_save_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return

        dto = CompanySettingData(
            id=1, 
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None,
            uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None,
            gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            # Defaulting some required fields for the DTO not present in this simple UI form
            fiscal_year_start_month=1, 
            fiscal_year_start_day=1,
            base_currency=self.base_currency_combo.currentText() or "SGD", 
            tax_id_label="UEN", 
            date_format="yyyy-MM-dd"
            # Add other fields from form...
        )
        asyncio.ensure_future(self.perform_save(dto))

    async def perform_save(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMessageBox.critical(self, "Error", "Company Settings Service not available.")
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings(settings_data.id or 1)
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            # Update existing_settings object with fields from settings_data
            existing_settings.company_name = settings_data.company_name
            existing_settings.legal_name = settings_data.legal_name
            existing_settings.uen_no = settings_data.uen_no
            existing_settings.gst_registration_no = settings_data.gst_registration_no
            existing_settings.gst_registered = settings_data.gst_registered
            existing_settings.base_currency = settings_data.base_currency
            # ... update other fields from DTO ...
            orm_obj_to_save = existing_settings
        else: 
            # This case implies creating settings for the first time for ID 1
            # This is unlikely if initial_data.sql seeds it.
            dict_data = settings_data.dict(exclude={'user_id', 'id'}) # Exclude fields not in CompanySetting model directly or handled by DB
            orm_obj_to_save = CompanySetting(**dict_data) # type: ignore
            orm_obj_to_save.id = settings_data.id or 1 

        if self.app_core.current_user:
             orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id # type: ignore

        result = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        if result:
            QMessageBox.information(self, "Success", "Settings saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")
