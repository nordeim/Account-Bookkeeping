# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG # Added QMetaObject, Q_ARG
from PySide6.QtGui import QColor # Added QColor
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData 
from app.models.core.company_setting import CompanySetting
from decimal import Decimal, InvalidOperation
import asyncio
from typing import Optional
from app.main import schedule_task_from_qt # Import the new scheduler

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
        self.base_currency_combo = QComboBox() 

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
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_settings()))


    async def load_settings(self):
        # This runs in the asyncio thread
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        
        currencies_loaded = False
        if self.app_core.currency_manager:
            try:
                currencies = await self.app_core.currency_manager.get_active_currencies()
                # Marshal ComboBox update to main thread
                QMetaObject.invokeMethod(self, "_populate_currency_combo", Qt.ConnectionType.QueuedConnection, Q_ARG(list, currencies))
                currencies_loaded = True
            except Exception as e:
                print(f"Error loading currencies for settings: {e}")
        
        if not currencies_loaded: # Fallback if currency loading failed
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))


        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        
        # Marshal UI updates back to the main thread
        QMetaObject.invokeMethod(self, "_update_ui_from_settings", Qt.ConnectionType.QueuedConnection, Q_ARG(CompanySetting, settings_obj) if settings_obj else Q_ARG(type(None), None))


    @Slot(list) # Slot for currencies
    def _populate_currency_combo(self, currencies: List[Any]): # Currency objects
        self.base_currency_combo.clear()
        for curr in currencies:
            self.base_currency_combo.addItem(curr.code, curr.code) # User data is code
        # After populating, try to set current if settings were loaded first
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj:
            idx = self.base_currency_combo.findText(self._loaded_settings_obj.base_currency) # type: ignore
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)


    @Slot(CompanySetting) # Make sure CompanySetting is registered for queued connections if not a QObject
    def _update_ui_from_settings(self, settings_obj: Optional[CompanySetting]):
        self._loaded_settings_obj = settings_obj # Store for re-applying currency selection
        if settings_obj:
            self.company_name_edit.setText(settings_obj.company_name)
            self.legal_name_edit.setText(settings_obj.legal_name or "")
            self.uen_edit.setText(settings_obj.uen_no or "")
            self.gst_reg_edit.setText(settings_obj.gst_registration_no or "")
            self.gst_registered_check.setChecked(settings_obj.gst_registered)
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
            fiscal_year_start_month=1, 
            fiscal_year_start_day=1,  
            base_currency=self.base_currency_combo.currentText() or "SGD", 
            tax_id_label="UEN",       
            date_format="yyyy-MM-dd", 
            address_line1=None, 
            address_line2=None,
            postal_code=None,
            city="Singapore",
            country="Singapore",
            contact_person=None,
            phone=None,
            email=None,
            website=None,
            logo=None
        )
        schedule_task_from_qt(self.perform_save(dto))

    async def perform_save(self, settings_data: CompanySettingData):
        # This runs in asyncio thread
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            for field_name, field_value in settings_data.model_dump(exclude={'user_id', 'id'}, by_alias=False).items():
                if hasattr(orm_obj_to_save, field_name):
                    setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id'}, by_alias=False)
            orm_obj_to_save = CompanySetting(**dict_data) 
            if settings_data.id:
                 orm_obj_to_save.id = settings_data.id

        if self.app_core.current_user:
             orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 

        result = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        
        if result:
            QMetaObject.invokeMethod(QMessageBox, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str,"Settings saved successfully."))
        else:
            QMetaObject.invokeMethod(QMessageBox, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Failed to save settings."))
