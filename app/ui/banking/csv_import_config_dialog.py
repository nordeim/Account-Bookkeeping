# File: app/ui/banking/csv_import_config_dialog.py
import os
import json
from typing import Optional, Dict, Any, TYPE_CHECKING, cast, Tuple, Union, List # Added List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QMessageBox, QCheckBox, QFileDialog, QLabel, QSpinBox, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon

from app.utils.result import Result
from app.utils.json_helpers import json_converter
from app.utils.pydantic_models import CSVImportErrorData
from app.ui.banking.csv_import_errors_dialog import CSVImportErrorsDialog

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from PySide6.QtGui import QPaintDevice


class CSVImportConfigDialog(QDialog):
    statement_imported = Signal(dict)

    FIELD_DATE = "date"; FIELD_DESCRIPTION = "description"; FIELD_DEBIT = "debit"; FIELD_CREDIT = "credit"; FIELD_AMOUNT = "amount"; FIELD_REFERENCE = "reference"; FIELD_VALUE_DATE = "value_date"
    
    FIELD_DISPLAY_NAMES = {
        FIELD_DATE: "Transaction Date*", FIELD_DESCRIPTION: "Description*", FIELD_DEBIT: "Debit Amount Column", FIELD_CREDIT: "Credit Amount Column",
        FIELD_AMOUNT: "Single Amount Column*", FIELD_REFERENCE: "Reference Column", FIELD_VALUE_DATE: "Value Date Column"
    }

    def __init__(self, app_core: "ApplicationCore", bank_account_id: int, current_user_id: int, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core; self.bank_account_id = bank_account_id; self.current_user_id = current_user_id
        self.setWindowTitle("Import Bank Statement from CSV"); self.setMinimumWidth(600); self.setModal(True)
        self.icon_path_prefix = "resources/icons/";
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        self._column_mapping_inputs: Dict[str, QLineEdit] = {}; self._init_ui(); self._connect_signals(); self._update_ui_for_column_type()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        file_group = QGroupBox("CSV File"); file_layout = QHBoxLayout(file_group)
        self.file_path_edit = QLineEdit(); self.file_path_edit.setReadOnly(True); self.file_path_edit.setPlaceholderText("Select CSV file to import...")
        browse_button = QPushButton(QIcon(self.icon_path_prefix + "open_company.svg"), "Browse..."); browse_button.setObjectName("BrowseButton")
        file_layout.addWidget(self.file_path_edit, 1); file_layout.addWidget(browse_button); main_layout.addWidget(file_group)
        format_group = QGroupBox("CSV Format Options"); format_layout = QFormLayout(format_group)
        self.has_header_check = QCheckBox("CSV file has a header row"); self.has_header_check.setChecked(True); format_layout.addRow(self.has_header_check)
        self.date_format_edit = QLineEdit("%d/%m/%Y"); date_format_hint = QLabel("Common: <code>%d/%m/%Y</code>, <code>%Y-%m-%d</code>, <code>%m/%d/%y</code>, <code>%b %d %Y</code>. <a href='https://strftime.org/'>More...</a>"); date_format_hint.setOpenExternalLinks(True); format_layout.addRow("Date Format*:", self.date_format_edit); format_layout.addRow("", date_format_hint); main_layout.addWidget(format_group)
        mapping_group = QGroupBox("Column Mapping (Enter column index or header name)"); self.mapping_form_layout = QFormLayout(mapping_group)
        for field_key in [self.FIELD_DATE, self.FIELD_DESCRIPTION, self.FIELD_REFERENCE, self.FIELD_VALUE_DATE]: edit = QLineEdit(); self._column_mapping_inputs[field_key] = edit; self.mapping_form_layout.addRow(self.FIELD_DISPLAY_NAMES[field_key] + ":", edit)
        self.use_single_amount_col_check = QCheckBox("Use a single column for Amount"); self.use_single_amount_col_check.setChecked(False); self.mapping_form_layout.addRow(self.use_single_amount_col_check)
        self._column_mapping_inputs[self.FIELD_DEBIT] = QLineEdit(); self.debit_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_DEBIT] + ":"); self.mapping_form_layout.addRow(self.debit_amount_label, self._column_mapping_inputs[self.FIELD_DEBIT])
        self._column_mapping_inputs[self.FIELD_CREDIT] = QLineEdit(); self.credit_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_CREDIT] + ":"); self.mapping_form_layout.addRow(self.credit_amount_label, self._column_mapping_inputs[self.FIELD_CREDIT])
        self._column_mapping_inputs[self.FIELD_AMOUNT] = QLineEdit(); self.single_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_AMOUNT] + ":"); self.mapping_form_layout.addRow(self.single_amount_label, self._column_mapping_inputs[self.FIELD_AMOUNT])
        self.debit_is_negative_check = QCheckBox("In single amount column, debits are negative values (credits are positive)"); self.debit_is_negative_check.setChecked(True); self.debit_negative_label = QLabel(); self.mapping_form_layout.addRow(self.debit_negative_label, self.debit_is_negative_check)
        main_layout.addWidget(mapping_group)
        self.button_box = QDialogButtonBox(); self.import_button = self.button_box.addButton("Import", QDialogButtonBox.ButtonRole.AcceptRole); self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel); main_layout.addWidget(self.button_box)
        self.setLayout(main_layout); self._on_has_header_changed(self.has_header_check.isChecked())

    def _connect_signals(self):
        browse_button = self.findChild(QPushButton, "BrowseButton");
        if browse_button: browse_button.clicked.connect(self._browse_file)
        self.has_header_check.stateChanged.connect(lambda state: self._on_has_header_changed(state == Qt.CheckState.Checked.value))
        self.use_single_amount_col_check.stateChanged.connect(self._update_ui_for_column_type)
        self.import_button.clicked.connect(self._collect_config_and_import)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button: cancel_button.clicked.connect(self.reject)

    @Slot()
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Bank Statement CSV", "", "CSV Files (*.csv);;All Files (*)");
        if file_path: self.file_path_edit.setText(file_path)

    @Slot(bool)
    def _on_has_header_changed(self, checked: bool):
        placeholder = "Header Name (e.g., Transaction Date)" if checked else "Column Index (e.g., 0)"
        for edit_widget in self._column_mapping_inputs.values(): edit_widget.setPlaceholderText(placeholder)
            
    @Slot()
    def _update_ui_for_column_type(self):
        use_single_col = self.use_single_amount_col_check.isChecked()
        self.debit_amount_label.setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_DEBIT].setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_DEBIT].setEnabled(not use_single_col)
        self.credit_amount_label.setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_CREDIT].setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_CREDIT].setEnabled(not use_single_col)
        self.single_amount_label.setVisible(use_single_col); self._column_mapping_inputs[self.FIELD_AMOUNT].setVisible(use_single_col); self._column_mapping_inputs[self.FIELD_AMOUNT].setEnabled(use_single_col)
        self.debit_is_negative_check.setVisible(use_single_col); self.debit_negative_label.setVisible(use_single_col); self.debit_is_negative_check.setEnabled(use_single_col)

    def _get_column_specifier(self, field_edit: QLineEdit) -> Optional[Union[str, int]]:
        text = field_edit.text().strip()
        if not text: return None
        if self.has_header_check.isChecked(): return text 
        else:
            try: return int(text) 
            except ValueError: return None 

    @Slot()
    def _collect_config_and_import(self):
        file_path = self.file_path_edit.text().strip()
        if not file_path: QMessageBox.warning(self, "Input Error", "Please select a CSV file."); return
        if not os.path.exists(file_path): QMessageBox.warning(self, "Input Error", f"File not found: {file_path}"); return
        date_format = self.date_format_edit.text().strip()
        if not date_format: QMessageBox.warning(self, "Input Error", "Date format is required."); return
        column_map: Dict[str, Any] = {}; errors: List[str] = []
        date_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_DATE])
        if date_spec is None: errors.append("Date column mapping is required.")
        else: column_map[self.FIELD_DATE] = date_spec
        desc_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_DESCRIPTION])
        if desc_spec is None: errors.append("Description column mapping is required.")
        else: column_map[self.FIELD_DESCRIPTION] = desc_spec
        if self.use_single_amount_col_check.isChecked():
            amount_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_AMOUNT])
            if amount_spec is None: errors.append("Single Amount column mapping is required when selected.")
            else: column_map[self.FIELD_AMOUNT] = amount_spec
        else:
            debit_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_DEBIT])
            credit_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_CREDIT])
            if debit_spec is None and credit_spec is None: errors.append("At least one of Debit or Credit Amount column mapping is required if not using single amount column.")
            if debit_spec is not None: column_map[self.FIELD_DEBIT] = debit_spec
            if credit_spec is not None: column_map[self.FIELD_CREDIT] = credit_spec
        ref_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_REFERENCE]);
        if ref_spec is not None: column_map[self.FIELD_REFERENCE] = ref_spec
        val_date_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_VALUE_DATE]);
        if val_date_spec is not None: column_map[self.FIELD_VALUE_DATE] = val_date_spec
        if not self.has_header_check.isChecked():
            for key, val in list(column_map.items()):
                if val is not None and not isinstance(val, int): errors.append(f"Invalid column index for '{self.FIELD_DISPLAY_NAMES.get(key, key)}': '{val}'. Must be a number when not using headers.")
        if errors: QMessageBox.warning(self, "Configuration Error", "\n".join(errors)); return
        import_options = {"date_format_str": date_format, "skip_header": self.has_header_check.isChecked(), "debit_is_negative_in_single_col": self.debit_is_negative_check.isChecked() if self.use_single_amount_col_check.isChecked() else False, "use_single_amount_column": self.use_single_amount_col_check.isChecked()}
        self.import_button.setEnabled(False); self.import_button.setText("Importing...")
        future = schedule_task_from_qt(self.app_core.bank_transaction_manager.import_bank_statement_csv(self.bank_account_id, file_path, self.current_user_id, column_map, import_options))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_handle_import_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule bank statement import task."); self._handle_import_result_slot(None)

    @Slot(object)
    def _handle_import_result_slot(self, future_arg):
        self.import_button.setEnabled(True); self.import_button.setText("Import")
        if future_arg is None: QMessageBox.critical(self, "Task Error", "Failed to schedule import operation."); return
        try:
            result: Result[Dict[str, Any]] = future_arg.result()
            if result.is_success and result.value:
                summary = result.value
                detailed_errors = summary.get("detailed_errors", [])
                
                summary_msg_parts = [
                    f"Import Process Complete for Bank Account ID: {self.bank_account_id}",
                    f"Total Rows Processed: {summary.get('total_rows_in_file', 0)}",
                    f"Successfully Imported: {summary.get('imported_count', 0)}",
                    f"Skipped (Duplicates): {summary.get('skipped_duplicates_count', 0)}",
                    f"Skipped (Zero Amount): {summary.get('zero_amount_skipped_count', 0)}",
                    f"Failed (Errors): {len(detailed_errors)}"
                ]
                
                if detailed_errors:
                    error_dialog = CSVImportErrorsDialog(detailed_errors, self)
                    error_dialog.exec()
                    # After reviewing errors, show the summary message box
                    QMessageBox.warning(self, "Import Complete with Errors", "\n".join(summary_msg_parts))
                else:
                    QMessageBox.information(self, "Import Successful", "\n".join(summary_msg_parts))
                
                self.statement_imported.emit(summary) 
                self.accept()
            else:
                QMessageBox.warning(self, "Import Failed", f"Failed to import statement:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Exception handling import result: {e}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred: {str(e)}")
