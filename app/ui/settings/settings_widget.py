# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG 
from PySide6.QtGui import QColor 
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency # For type hint
from decimal import Decimal, InvalidOperation
import asyncio
from typing import Optional, List, Any 
from app.main import schedule_task_from_qt 

class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._loaded_settings_obj: Optional[CompanySetting] = None 
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
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        
        currencies_loaded_successfully = False
        if self.app_core.currency_manager:
            try:
                active_currencies: List[Currency] = await self.app_core.currency_manager.get_active_currencies()
                QMetaObject.invokeMethod(self, "_populate_currency_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(list, active_currencies))
                currencies_loaded_successfully = True
            except Exception as e:
                error_msg = f"Error loading currencies for settings: {e}"
                print(error_msg)
                QMetaObject.invokeMethod(QMessageBox, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Currency Load Error"), Q_ARG(str, error_msg))
        
        if not currencies_loaded_successfully: 
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        self._loaded_settings_obj = settings_obj 
        
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(CompanySetting, settings_obj) if settings_obj else Q_ARG(type(None), None))

    @Slot(list) 
    def _populate_currency_combo_slot(self, currencies: List[Currency]): 
        self.base_currency_combo.clear()
        for curr in currencies: 
            self.base_currency_combo.addItem(f"{curr.code} - {curr.name}", curr.code) 
        
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj:
            idx = self.base_currency_combo.findData(self._loaded_settings_obj.base_currency) 
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD")
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)

    @Slot(CompanySetting) 
    def _update_ui_from_settings_slot(self, settings_obj: Optional[CompanySetting]):
        if settings_obj:
            self.company_name_edit.setText(settings_obj.company_name)
            self.legal_name_edit.setText(settings_obj.legal_name or "")
            self.uen_edit.setText(settings_obj.uen_no or "")
            self.gst_reg_edit.setText(settings_obj.gst_registration_no or "")
            self.gst_registered_check.setChecked(settings_obj.gst_registered)
            
            if self.base_currency_combo.count() > 0:
                idx = self.base_currency_combo.findData(settings_obj.base_currency) 
                if idx != -1: 
                    self.base_currency_combo.setCurrentIndex(idx)
                else: 
                    idx_sgd = self.base_currency_combo.findData("SGD")
                    if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        else:
            QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")

    @Slot()
    def on_save_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return

        selected_currency_code = self.base_currency_combo.currentData() or "SGD"

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
            base_currency=selected_currency_code, 
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
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            # Update only fields present in UI for now for simplicity
            orm_obj_to_save.company_name = settings_data.company_name
            orm_obj_to_save.legal_name = settings_data.legal_name
            orm_obj_to_save.uen_no = settings_data.uen_no
            orm_obj_to_save.gst_registration_no = settings_data.gst_registration_no
            orm_obj_to_save.gst_registered = settings_data.gst_registered
            orm_obj_to_save.base_currency = settings_data.base_currency
            # For a full implementation, all fields from CompanySettingData should be mapped
            # or the UI should expose all editable fields.
        else: 
            # Create new if somehow settings don't exist, assuming id=1
            dict_data = settings_data.model_dump(exclude={'user_id', 'id'}, by_alias=False)
            orm_obj_to_save = CompanySetting(**dict_data) 
            orm_obj_to_save.id = 1 # Force ID 1 for the single company settings row

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
