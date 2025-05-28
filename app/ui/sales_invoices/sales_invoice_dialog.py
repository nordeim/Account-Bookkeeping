# app/ui/sales_invoices/sales_invoice_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCompleter,
    QSizePolicy, QApplication, QStyledItemDelegate, QAbstractSpinBox, QLabel, QFrame # Added QFrame, QLabel
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QFont, QPalette, QColor
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
from datetime import date as python_date

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    CustomerSummaryData, ProductSummaryData 
)
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.models.business.product import Product 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class LineItemNumericDelegate(QStyledItemDelegate):
    def __init__(self, decimals=2, allow_negative=False, parent=None):
        super().__init__(parent)
        self.decimals = decimals
        self.allow_negative = allow_negative

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget: # type: ignore
        editor = QDoubleSpinBox(parent)
        editor.setDecimals(self.decimals)
        editor.setMinimum(-999999999999.9999 if self.allow_negative else 0.0)
        editor.setMaximum(999999999999.9999) 
        editor.setGroupSeparatorShown(True)
        editor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        return editor

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex):
        value_str = index.model().data(index, Qt.ItemDataRole.EditRole) # EditRole for QTableWidgetItem
        try:
            editor.setValue(float(Decimal(str(value_str if value_str else '0'))))
        except (TypeError, ValueError, InvalidOperation):
            editor.setValue(0.0)

    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractItemModel, index: QModelIndex): # type: ignore
        # Store as string to maintain precision, round appropriately for display/calculation
        precision_str = '0.01' if self.decimals == 2 else '0.0001' # Common precisions
        model.setData(index, str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)), Qt.ItemDataRole.EditRole)


class SalesInvoiceDialog(QDialog):
    invoice_saved = Signal(int) 

    COL_DEL = 0; COL_PROD = 1; COL_DESC = 2; COL_QTY = 3; COL_PRICE = 4
    COL_DISC_PCT = 5; COL_SUBTOTAL = 6; COL_TAX_CODE = 7; COL_TAX_AMT = 8; COL_TOTAL = 9
    
    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 invoice_id: Optional[int] = None, 
                 view_only: bool = False, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core; self.current_user_id = current_user_id
        self.invoice_id = invoice_id; self.view_only_mode = view_only
        self.loaded_invoice_orm: Optional[SalesInvoice] = None
        self.loaded_invoice_data_dict: Optional[Dict[str, Any]] = None

        self._customers_cache: List[Dict[str, Any]] = [] # Store as dicts for combo
        self._products_cache: List[Dict[str, Any]] = []
        self._currencies_cache: List[Dict[str, Any]] = []
        self._tax_codes_cache: List[Dict[str, Any]] = []

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(1000, 750); self.setModal(True)
        self._init_ui(); self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.invoice_id:
            QTimer.singleShot(100, lambda: schedule_task_from_qt(self._load_existing_invoice_data()))
        elif not self.view_only_mode: self._add_new_invoice_line()

    def _get_window_title(self) -> str:
        if self.view_only_mode: return f"View Sales Invoice {self.loaded_invoice_orm.invoice_no if self.loaded_invoice_orm else ''}"
        if self.invoice_id: return f"Edit Sales Invoice {self.loaded_invoice_orm.invoice_no if self.loaded_invoice_orm else ''}"
        return "New Sales Invoice"

    def _init_ui(self):
        main_layout = QVBoxLayout(self); self.header_form = QFormLayout()
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.customer_combo = QComboBox(); self.customer_combo.setEditable(True); self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        cust_completer = QCompleter(); cust_completer.setFilterMode(Qt.MatchFlag.MatchContains); cust_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.customer_combo.setCompleter(cust_completer); self.header_form.addRow("Customer*:", self.customer_combo)
        self.invoice_no_label = QLabel("To be generated"); self.invoice_no_label.setStyleSheet("font-style: italic; color: grey;")
        self.header_form.addRow("Invoice No.:", self.invoice_no_label)
        self.invoice_date_edit = QDateEdit(QDate.currentDate()); self.invoice_date_edit.setCalendarPopup(True); self.invoice_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.header_form.addRow("Invoice Date*:", self.invoice_date_edit)
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30)); self.due_date_edit.setCalendarPopup(True); self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.header_form.addRow("Due Date*:", self.due_date_edit)
        self.currency_combo = QComboBox(); self.header_form.addRow("Currency*:", self.currency_combo)
        self.exchange_rate_spin = QDoubleSpinBox(); self.exchange_rate_spin.setDecimals(6); self.exchange_rate_spin.setRange(0.000001, 999999.0); self.exchange_rate_spin.setValue(1.0)
        self.header_form.addRow("Exchange Rate:", self.exchange_rate_spin)
        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(40); self.header_form.addRow("Notes:", self.notes_edit)
        self.terms_edit = QTextEdit(); self.terms_edit.setFixedHeight(40); self.header_form.addRow("Terms & Conditions:", self.terms_edit)
        main_layout.addLayout(self.header_form)
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(self.COL_TOTAL + 1) 
        self.lines_table.setHorizontalHeaderLabels(["", "Product/Service", "Description", "Qty*", "Unit Price*", "Disc %", "Subtotal", "Tax Code", "Tax Amt", "Line Total"])
        self._configure_lines_table_columns()
        main_layout.addWidget(self.lines_table)
        lines_button_layout = QHBoxLayout()
        self.add_line_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(self.icon_path_prefix + "remove.svg"), "Remove Selected Line")
        lines_button_layout.addWidget(self.add_line_button); lines_button_layout.addWidget(self.remove_line_button); lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)
        totals_form = QFormLayout(); totals_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows); totals_form.setStyleSheet("QLabel { font-weight: bold; } QLineEdit { font-weight: bold; }")
        self.subtotal_display = QLineEdit("0.00"); self.subtotal_display.setReadOnly(True); self.subtotal_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_tax_display = QLineEdit("0.00"); self.total_tax_display.setReadOnly(True); self.total_tax_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.grand_total_display = QLineEdit("0.00"); self.grand_total_display.setReadOnly(True); self.grand_total_display.setAlignment(Qt.AlignmentFlag.AlignRight); self.grand_total_display.setStyleSheet("font-weight: bold; font-size: 14pt;")
        totals_form.addRow("Subtotal:", self.subtotal_display); totals_form.addRow("Total Tax:", self.total_tax_display); totals_form.addRow("Grand Total:", self.grand_total_display)
        align_totals_layout = QHBoxLayout(); align_totals_layout.addStretch(); align_totals_layout.addLayout(totals_form)
        main_layout.addLayout(align_totals_layout)
        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_approve_button = self.button_box.addButton("Save & Approve", QDialogButtonBox.ButtonRole.ActionRole) # Placeholder for future
        self.save_approve_button.setToolTip("Future: Save, mark as Approved, and generate Journal Entry.")
        self.save_approve_button.setEnabled(False) # Disabled for now
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box); self.setLayout(main_layout)

    def _configure_lines_table_columns(self):
        # ... (same as before)
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_DEL, QHeaderView.ResizeMode.Fixed); self.lines_table.setColumnWidth(self.COL_DEL, 30)
        header.setSectionResizeMode(self.COL_PROD, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_DESC, QHeaderView.ResizeMode.Stretch)
        for col in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT, self.COL_SUBTOTAL, self.COL_TAX_CODE, self.COL_TAX_AMT, self.COL_TOTAL]:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.lines_table.setItemDelegateForColumn(self.COL_QTY, LineItemNumericDelegate(2, self))
        self.lines_table.setItemDelegateForColumn(self.COL_PRICE, LineItemNumericDelegate(4, self))
        self.lines_table.setItemDelegateForColumn(self.COL_DISC_PCT, LineItemNumericDelegate(2, self))


    def _connect_signals(self): # ... (same as before)
        self.add_line_button.clicked.connect(self._add_new_invoice_line)
        self.remove_line_button.clicked.connect(self._remove_selected_invoice_line)
        self.lines_table.itemChanged.connect(self._on_line_item_changed)
        self.save_draft_button.clicked.connect(self.on_save_draft)
        # self.save_approve_button.clicked.connect(self.on_save_approve) # Future
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if close_button: close_button.clicked.connect(self.reject)
        if cancel_button: cancel_button.clicked.connect(self.reject)
        self.customer_combo.currentIndexChanged.connect(self._on_customer_changed)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)


    async def _load_initial_combo_data(self):
        # ... (Implementation as previously planned, fetching customers, products, currencies, tax codes)
        pass # Placeholder - full implementation is extensive

    @Slot(str, str, str, str) 
    def _populate_initial_combos_slot(self, customers_json: str, products_json: str, currencies_json: str, tax_codes_json: str):
        # ... (Implementation as previously planned)
        pass # Placeholder

    async def _load_existing_invoice_data(self):
        # ... (Implementation as previously planned, call manager.get_invoice_for_dialog)
        pass # Placeholder

    @Slot(str)
    def _populate_dialog_from_data_slot(self, invoice_json_str: str):
        # ... (Implementation as previously planned, parse JSON, populate header and lines)
        pass # Placeholder
    
    def _set_read_only_state(self, read_only: bool): # ... (similar to JE Dialog, disable all inputs)
        pass # Placeholder

    def _add_new_invoice_line(self, line_data: Optional[Dict[str, Any]] = None):
        # ... (Implementation as previously planned, create and set cell widgets, connect signals)
        pass # Placeholder

    def _remove_selected_invoice_line(self): # ... (similar to JE Dialog)
        pass # Placeholder

    @Slot(QTableWidgetItem)
    def _on_line_item_changed(self, item: QTableWidgetItem): 
        # ... (Trigger recalculations if Qty, Price, Disc%, or Tax Code text changes (if not using dedicated widgets))
        # For QDoubleSpinBox/QComboBox, connect their valueChanged/currentIndexChanged directly.
        # This slot mainly for Description if it's a QTableWidgetItem.
        if item.column() in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT]: # Unlikely if using widgets
            self._trigger_line_recalculation(item.row())

    @Slot() # Helper to connect signals from widgets in cells
    def _trigger_line_recalculation_slot(self):
        sender_widget = self.sender()
        if sender_widget:
            for row in range(self.lines_table.rowCount()):
                # Check if sender is a widget in this row for Qty, Price, Disc%, TaxCode
                if self.lines_table.cellWidget(row, self.COL_QTY) == sender_widget or \
                   self.lines_table.cellWidget(row, self.COL_PRICE) == sender_widget or \
                   self.lines_table.cellWidget(row, self.COL_DISC_PCT) == sender_widget or \
                   self.lines_table.cellWidget(row, self.COL_TAX_CODE) == sender_widget:
                    self._calculate_line_item_totals(row)
                    break # Found the row

    def _calculate_line_item_totals(self, row: int): # ... (as previously planned)
        pass # Placeholder

    def _update_invoice_totals(self): # ... (as previously planned)
        pass # Placeholder
        
    def _collect_data(self) -> Optional[Union[SalesInvoiceCreateData, SalesInvoiceUpdateData]]: # Updated return type
        return None # Placeholder

    @Slot()
    def on_save_draft(self): # ... (collect data, call manager.create_draft_invoice or update_draft_invoice)
        pass # Placeholder

    # @Slot()
    # def on_save_approve(self): # ... (Future: collect data, call manager.create_and_post_invoice)
    #     pass

    async def _perform_save(self, dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData], post_after_save: bool = False):
        pass # Placeholder

    # --- New slots for customer/currency changes ---
    @Slot(int)
    def _on_customer_changed(self, index: int):
        customer_id = self.customer_combo.itemData(index)
        if customer_id and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("currency_code"):
                curr_idx = self.currency_combo.findData(customer_data["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
                # Potentially auto-fill terms, etc.

    @Slot(int)
    def _on_currency_changed(self, index: int):
        # Enable/disable exchange rate based on whether it's base currency
        # Requires knowing base currency from company settings
        # currency_code = self.currency_combo.itemData(index)
        # base_currency = self.app_core.company_settings_service.get_base_currency_code() # Needs sync access or async
        # self.exchange_rate_spin.setEnabled(currency_code != base_currency)
        # if currency_code == base_currency: self.exchange_rate_spin.setValue(1.0)
        pass # Placeholder

