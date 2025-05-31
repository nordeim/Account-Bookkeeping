# app/ui/sales_invoices/__init__.py
```py
# app/ui/sales_invoices/__init__.py
from .sales_invoice_table_model import SalesInvoiceTableModel
from .sales_invoice_dialog import SalesInvoiceDialog
from .sales_invoices_widget import SalesInvoicesWidget # New import

__all__ = [
    "SalesInvoiceTableModel",
    "SalesInvoiceDialog",
    "SalesInvoicesWidget", # Added to __all__
]


```

# app/ui/sales_invoices/sales_invoices_widget.py
```py
# app/ui/sales_invoices/sales_invoices_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.sales_invoices.sales_invoice_table_model import SalesInvoiceTableModel
from app.ui.sales_invoices.sales_invoice_dialog import SalesInvoiceDialog
from app.utils.pydantic_models import SalesInvoiceSummaryData, CustomerSummaryData
from app.common.enums import InvoiceStatusEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.sales_invoice import SalesInvoice # For Result type hint

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class SalesInvoicesWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._customers_cache_for_filter: List[CustomerSummaryData] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for SalesInvoicesWidget.")
        except ImportError:
            self.app_core.logger.info("SalesInvoicesWidget: Compiled resources not found. Using direct file paths.")
            
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_customers_for_filter_combo()))
        QTimer.singleShot(100, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addLayout(self.filter_layout) 

        self.invoices_table = QTableView()
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.horizontalHeader().setStretchLastSection(False)
        self.invoices_table.doubleClicked.connect(self._on_view_invoice_double_click) 
        self.invoices_table.setSortingEnabled(True)

        self.table_model = SalesInvoiceTableModel()
        self.invoices_table.setModel(self.table_model)
        
        header = self.invoices_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.invoices_table.setColumnHidden(id_col_idx, True)
        
        customer_col_idx = self.table_model._headers.index("Customer") if "Customer" in self.table_model._headers else -1
        if customer_col_idx != -1:
            visible_customer_idx = customer_col_idx
            if id_col_idx != -1 and id_col_idx < customer_col_idx and self.invoices_table.isColumnHidden(id_col_idx):
                 visible_customer_idx -=1
            if not self.invoices_table.isColumnHidden(customer_col_idx):
                 header.setSectionResizeMode(visible_customer_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 4 : 
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.invoices_table)
        self.setLayout(self.main_layout)

        if self.invoices_table.selectionModel():
            self.invoices_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Sales Invoice Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_new_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Invoice", self)
        self.toolbar_new_action.triggered.connect(self._on_new_invoice)
        self.toolbar.addAction(self.toolbar_new_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_draft_invoice)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Invoice", self)
        self.toolbar_view_action.triggered.connect(self._on_view_invoice_toolbar)
        self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar_post_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Invoice(s)", self)
        self.toolbar_post_action.triggered.connect(self._on_post_invoice) 
        self.toolbar_post_action.setEnabled(False) 
        self.toolbar.addAction(self.toolbar_post_action)

        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout() 
        
        self.filter_layout.addWidget(QLabel("Customer:"))
        self.customer_filter_combo = QComboBox()
        self.customer_filter_combo.setMinimumWidth(200)
        self.customer_filter_combo.addItem("All Customers", 0) 
        self.filter_layout.addWidget(self.customer_filter_combo)

        self.filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses", None) 
        for status_enum in InvoiceStatusEnum:
            self.status_filter_combo.addItem(status_enum.value, status_enum)
        self.filter_layout.addWidget(self.status_filter_combo)

        self.filter_layout.addWidget(QLabel("From:"))
        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-3))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout.addWidget(self.start_date_filter_edit)

        self.filter_layout.addWidget(QLabel("To:"))
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout.addWidget(self.end_date_filter_edit)

        self.apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply")
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.filter_layout.addWidget(self.apply_filter_button)
        
        self.clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        self.filter_layout.addWidget(self.clear_filter_button)
        self.filter_layout.addStretch()

    async def _load_customers_for_filter_combo(self):
        if not self.app_core.customer_manager: return
        try:
            result: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1) 
            if result.is_success and result.value:
                self._customers_cache_for_filter = result.value
                customers_json = json.dumps([c.model_dump() for c in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_customers_filter_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, customers_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading customers for filter: {e}", exc_info=True)

    @Slot(str)
    def _populate_customers_filter_slot(self, customers_json_str: str):
        self.customer_filter_combo.clear()
        self.customer_filter_combo.addItem("All Customers", 0) 
        try:
            customers_data = json.loads(customers_json_str)
            self._customers_cache_for_filter = [CustomerSummaryData.model_validate(c) for c in customers_data]
            for cust_summary in self._customers_cache_for_filter:
                self.customer_filter_combo.addItem(f"{cust_summary.customer_code} - {cust_summary.name}", cust_summary.id)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Failed to parse customers JSON for filter: {e}")

    @Slot()
    def _clear_filters_and_load(self):
        self.customer_filter_combo.setCurrentIndex(0) 
        self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-3))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        schedule_task_from_qt(self._load_invoices())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_edit_draft = False
        can_post_any_selected = False # Changed logic to allow posting multiple drafts
        
        if single_selection:
            row = selected_rows[0].row()
            status = self.table_model.get_invoice_status_at_row(row)
            if status == InvoiceStatusEnum.DRAFT:
                can_edit_draft = True
        
        if selected_rows: # Check if any selected are drafts for posting
            can_post_any_selected = any(
                self.table_model.get_invoice_status_at_row(idx.row()) == InvoiceStatusEnum.DRAFT
                for idx in selected_rows
            )
            
        self.toolbar_edit_action.setEnabled(can_edit_draft) # Edit only single draft
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(can_post_any_selected) 

    async def _load_invoices(self):
        if not self.app_core.sales_invoice_manager:
            self.app_core.logger.error("SalesInvoiceManager not available."); return
        try:
            cust_id_data = self.customer_filter_combo.currentData()
            customer_id_filter = int(cust_id_data) if cust_id_data and cust_id_data != 0 else None
            
            status_enum_data = self.status_filter_combo.currentData()
            status_filter_val: Optional[InvoiceStatusEnum] = status_enum_data if isinstance(status_enum_data, InvoiceStatusEnum) else None
            
            start_date_filter = self.start_date_filter_edit.date().toPython()
            end_date_filter = self.end_date_filter_edit.date().toPython()

            result: Result[List[SalesInvoiceSummaryData]] = await self.app_core.sales_invoice_manager.get_invoices_for_listing(
                customer_id=customer_id_filter, status=status_filter_val,
                start_date=start_date_filter, end_date=end_date_filter,
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load invoices: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading invoices: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            invoice_summaries: List[SalesInvoiceSummaryData] = [SalesInvoiceSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(invoice_summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate invoice data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_new_invoice(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = SalesInvoiceDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_invoice_id_and_status(self) -> tuple[Optional[int], Optional[InvoiceStatusEnum]]:
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None, None
        row = selected_rows[0].row()
        inv_id = self.table_model.get_invoice_id_at_row(row)
        inv_status = self.table_model.get_invoice_status_at_row(row)
        return inv_id, inv_status

    @Slot()
    def _on_edit_draft_invoice(self):
        invoice_id, status = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single invoice to edit."); return
        if status != InvoiceStatusEnum.DRAFT: QMessageBox.warning(self, "Edit Error", "Only Draft invoices can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        dialog = SalesInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_view_invoice_toolbar(self):
        invoice_id, _ = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single invoice to view."); return
        self._show_view_invoice_dialog(invoice_id)

    @Slot(QModelIndex)
    def _on_view_invoice_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        invoice_id = self.table_model.get_invoice_id_at_row(index.row())
        if invoice_id is None: return
        self._show_view_invoice_dialog(invoice_id)

    def _show_view_invoice_dialog(self, invoice_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = SalesInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, view_only=True, parent=self)
        dialog.exec()
        
    @Slot()
    def _on_post_invoice(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows: 
            QMessageBox.information(self, "Selection", "Please select one or more Draft invoices to post.")
            return
        
        if not self.app_core.current_user: 
            QMessageBox.warning(self, "Auth Error", "Please log in to post invoices.")
            return

        draft_invoice_ids_to_post: List[int] = []
        non_draft_selected_count = 0
        for index in selected_rows:
            inv_id = self.table_model.get_invoice_id_at_row(index.row())
            status = self.table_model.get_invoice_status_at_row(index.row())
            if inv_id and status == InvoiceStatusEnum.DRAFT:
                draft_invoice_ids_to_post.append(inv_id)
            elif inv_id: # It's a selected non-draft invoice
                non_draft_selected_count += 1
        
        if not draft_invoice_ids_to_post:
            QMessageBox.information(self, "Selection", "No Draft invoices selected for posting.")
            return
        
        warning_message = ""
        if non_draft_selected_count > 0:
            warning_message = f"\n\nNote: {non_draft_selected_count} selected invoice(s) are not in 'Draft' status and will be ignored."

        reply = QMessageBox.question(self, "Confirm Posting", 
                                     f"Are you sure you want to post {len(draft_invoice_ids_to_post)} selected draft invoice(s)?\nThis will create journal entries and change their status to 'Approved'.{warning_message}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        self.toolbar_post_action.setEnabled(False) # Disable while processing
        schedule_task_from_qt(self._perform_post_invoices(draft_invoice_ids_to_post, self.app_core.current_user.id))


    async def _perform_post_invoices(self, invoice_ids: List[int], user_id: int):
        if not self.app_core.sales_invoice_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Sales Invoice Manager not available."))
            self._update_action_states() # Re-enable button based on current state
            return

        success_count = 0
        failed_posts: List[str] = [] # Store "InvoiceNo: Error"

        for inv_id_to_post in invoice_ids:
            # Fetch invoice number for logging/messaging before attempting to post
            # This is a read, so should be relatively safe outside the main post transaction
            invoice_orm_for_no = await self.app_core.sales_invoice_manager.get_invoice_for_dialog(inv_id_to_post)
            inv_no_str = invoice_orm_for_no.invoice_no if invoice_orm_for_no else f"ID {inv_id_to_post}"

            result: Result[SalesInvoice] = await self.app_core.sales_invoice_manager.post_invoice(inv_id_to_post, user_id)
            if result.is_success:
                success_count += 1
            else:
                failed_posts.append(f"Invoice {inv_no_str}: {', '.join(result.errors)}")
        
        summary_message_parts = []
        if success_count > 0:
            summary_message_parts.append(f"{success_count} invoice(s) posted successfully.")
        if failed_posts:
            summary_message_parts.append(f"{len(failed_posts)} invoice(s) failed to post:")
            summary_message_parts.extend([f"  - {err}" for err in failed_posts])
        
        final_message = "\n".join(summary_message_parts)
        if not final_message: final_message = "No invoices were processed."

        msg_box_method = QMessageBox.information
        title = "Posting Complete"
        if failed_posts and success_count == 0:
            msg_box_method = QMessageBox.critical
            title = "Posting Failed"
        elif failed_posts:
            msg_box_method = QMessageBox.warning
            title = "Posting Partially Successful"
        
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, final_message))
        
        # Refresh list and update button states
        schedule_task_from_qt(self._load_invoices())


    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"SalesInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())


```

# app/ui/sales_invoices/sales_invoice_dialog.py
```py
# app/ui/sales_invoices/sales_invoice_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCompleter,
    QSizePolicy, QApplication, QStyledItemDelegate, QAbstractSpinBox, QLabel, QFrame,
    QGridLayout, QWidget 
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG, QModelIndex 
from PySide6.QtGui import QIcon, QFont, QPalette, QColor
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast, Union
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
    from PySide6.QtGui import QPaintDevice, QAbstractItemModel 

class LineItemNumericDelegate(QStyledItemDelegate):
    def __init__(self, decimals=2, allow_negative=False, max_val=999999999.9999, parent=None):
        super().__init__(parent)
        self.decimals = decimals
        self.allow_negative = allow_negative
        self.max_val = max_val

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget: # type: ignore
        editor = QDoubleSpinBox(parent)
        editor.setDecimals(self.decimals)
        editor.setMinimum(-self.max_val if self.allow_negative else 0.0)
        editor.setMaximum(self.max_val) 
        editor.setGroupSeparatorShown(True)
        editor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        return editor

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex):
        value_str = index.model().data(index, Qt.ItemDataRole.EditRole) 
        try:
            val = Decimal(str(value_str if value_str and str(value_str).strip() else '0'))
            editor.setValue(float(val))
        except (TypeError, ValueError, InvalidOperation):
            editor.setValue(0.0)

    def setModelData(self, editor: QDoubleSpinBox, model: "QAbstractItemModel", index: QModelIndex): # type: ignore
        precision_str = '0.01' if self.decimals == 2 else ('0.0001' if self.decimals == 4 else '0.000001')
        if isinstance(model, QTableWidget):
            item = model.item(index.row(), index.column())
            if not item: item = QTableWidgetItem()
            item.setText(str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)))
        else: 
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

        self._customers_cache: List[Dict[str, Any]] = []
        self._products_cache: List[Dict[str, Any]] = [] # Will store ProductSummaryData as dicts
        self._currencies_cache: List[Dict[str, Any]] = []
        self._tax_codes_cache: List[Dict[str, Any]] = []
        self._base_currency: str = "SGD" 

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
        inv_no_str = ""
        if self.loaded_invoice_orm and self.loaded_invoice_orm.invoice_no: inv_no_str = f" ({self.loaded_invoice_orm.invoice_no})"
        elif self.loaded_invoice_data_dict and self.loaded_invoice_data_dict.get("invoice_no"): inv_no_str = f" ({self.loaded_invoice_data_dict.get('invoice_no')})"
        if self.view_only_mode: return f"View Sales Invoice{inv_no_str}"
        if self.invoice_id: return f"Edit Sales Invoice{inv_no_str}"
        return "New Sales Invoice"

    def _init_ui(self):
        main_layout = QVBoxLayout(self); self.header_form = QFormLayout()
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows) 
        self.header_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.customer_combo = QComboBox(); self.customer_combo.setEditable(True); self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.customer_combo.setMinimumWidth(300)
        cust_completer = QCompleter(); cust_completer.setFilterMode(Qt.MatchFlag.MatchContains); cust_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.customer_combo.setCompleter(cust_completer)
        
        self.invoice_no_label = QLabel("To be generated"); self.invoice_no_label.setStyleSheet("font-style: italic; color: grey;")
        
        self.invoice_date_edit = QDateEdit(QDate.currentDate()); self.invoice_date_edit.setCalendarPopup(True); self.invoice_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30)); self.due_date_edit.setCalendarPopup(True); self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.currency_combo = QComboBox()
        self.exchange_rate_spin = QDoubleSpinBox(); self.exchange_rate_spin.setDecimals(6); self.exchange_rate_spin.setRange(0.000001, 999999.0); self.exchange_rate_spin.setValue(1.0)
        
        grid_header_layout = QGridLayout()
        grid_header_layout.addWidget(QLabel("Customer*:"), 0, 0); grid_header_layout.addWidget(self.customer_combo, 0, 1, 1, 2) 
        grid_header_layout.addWidget(QLabel("Invoice Date*:"), 1, 0); grid_header_layout.addWidget(self.invoice_date_edit, 1, 1)
        grid_header_layout.addWidget(QLabel("Invoice No.:"), 0, 3); grid_header_layout.addWidget(self.invoice_no_label, 0, 4)
        grid_header_layout.addWidget(QLabel("Due Date*:"), 1, 3); grid_header_layout.addWidget(self.due_date_edit, 1, 4)
        grid_header_layout.addWidget(QLabel("Currency*:"), 2, 0); grid_header_layout.addWidget(self.currency_combo, 2, 1)
        grid_header_layout.addWidget(QLabel("Exchange Rate:"), 2, 3); grid_header_layout.addWidget(self.exchange_rate_spin, 2, 4)
        grid_header_layout.setColumnStretch(2,1) 
        grid_header_layout.setColumnStretch(5,1) 
        main_layout.addLayout(grid_header_layout)

        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(40); self.header_form.addRow("Notes:", self.notes_edit)
        self.terms_edit = QTextEdit(); self.terms_edit.setFixedHeight(40); self.header_form.addRow("Terms & Conditions:", self.terms_edit)
        main_layout.addLayout(self.header_form) 

        self.lines_table = QTableWidget(); self.lines_table.setColumnCount(self.COL_TOTAL + 1) 
        self.lines_table.setHorizontalHeaderLabels(["", "Product/Service", "Description", "Qty*", "Price*", "Disc %", "Subtotal", "Tax", "Tax Amt", "Total"])
        self._configure_lines_table_columns(); main_layout.addWidget(self.lines_table)
        lines_button_layout = QHBoxLayout()
        self.add_line_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(self.icon_path_prefix + "remove.svg"), "Remove Line")
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
        self.save_approve_button = self.button_box.addButton("Save & Approve", QDialogButtonBox.ButtonRole.ActionRole) 
        self.save_approve_button.setToolTip("Save invoice and mark as Approved (posts Journal Entry).")
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box); self.setLayout(main_layout)

    def _configure_lines_table_columns(self):
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_DEL, QHeaderView.ResizeMode.Fixed); self.lines_table.setColumnWidth(self.COL_DEL, 30)
        header.setSectionResizeMode(self.COL_PROD, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_PROD, 250) # Increased width for richer text
        header.setSectionResizeMode(self.COL_DESC, QHeaderView.ResizeMode.Stretch) 
        for col in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT]: 
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(col,100)
        for col in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]: 
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(col,120)
        header.setSectionResizeMode(self.COL_TAX_CODE, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_TAX_CODE, 150)
        
        self.lines_table.setItemDelegateForColumn(self.COL_QTY, LineItemNumericDelegate(2, self))
        self.lines_table.setItemDelegateForColumn(self.COL_PRICE, LineItemNumericDelegate(4, self)) 
        self.lines_table.setItemDelegateForColumn(self.COL_DISC_PCT, LineItemNumericDelegate(2, False, 100.00, self))

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_invoice_line)
        self.remove_line_button.clicked.connect(self._remove_selected_invoice_line)
        self.lines_table.itemChanged.connect(self._on_line_item_changed_desc_only) 
        
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_approve_button.clicked.connect(self.on_save_and_approve) 
        
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if close_button: close_button.clicked.connect(self.reject)
        if cancel_button: cancel_button.clicked.connect(self.reject)

        self.customer_combo.currentIndexChanged.connect(self._on_customer_changed)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.invoice_date_edit.dateChanged.connect(self._on_invoice_date_changed)

    async def _load_initial_combo_data(self):
        try:
            cs_svc = self.app_core.company_settings_service
            if cs_svc: settings = await cs_svc.get_company_settings(); self._base_currency = settings.base_currency if settings else "SGD"

            cust_res: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1)
            self._customers_cache = [cs.model_dump() for cs in cust_res.value] if cust_res.is_success and cust_res.value else []
            
            prod_res: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(active_only=True, page_size=-1)
            self._products_cache = [ps.model_dump() for ps in prod_res.value] if prod_res.is_success and prod_res.value else []

            if self.app_core.currency_manager:
                curr_orms = await self.app_core.currency_manager.get_all_currencies()
                self._currencies_cache = [{"code":c.code, "name":c.name} for c in curr_orms if c.is_active]
            
            if self.app_core.tax_code_service:
                tc_orms = await self.app_core.tax_code_service.get_all()
                self._tax_codes_cache = [{"code":tc.code, "rate":tc.rate, "description":f"{tc.code} ({tc.rate:.0f}%)"} for tc in tc_orms if tc.is_active] # Rate formatting

            QMetaObject.invokeMethod(self, "_populate_initial_combos_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for SalesInvoiceDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load initial data for dropdowns: {str(e)}")

    @Slot()
    def _populate_initial_combos_slot(self):
        self.customer_combo.clear(); self.customer_combo.addItem("-- Select Customer --", 0)
        for cust in self._customers_cache: self.customer_combo.addItem(f"{cust['customer_code']} - {cust['name']}", cust['id'])
        if isinstance(self.customer_combo.completer(), QCompleter): self.customer_combo.completer().setModel(self.customer_combo.model()) # type: ignore

        self.currency_combo.clear()
        for curr in self._currencies_cache: self.currency_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        base_curr_idx = self.currency_combo.findData(self._base_currency)
        if base_curr_idx != -1: self.currency_combo.setCurrentIndex(base_curr_idx)
        elif self._currencies_cache : self.currency_combo.setCurrentIndex(0) 
        self._on_currency_changed(self.currency_combo.currentIndex())

        if self.loaded_invoice_orm: self._populate_fields_from_orm(self.loaded_invoice_orm)
        elif self.loaded_invoice_data_dict: self._populate_fields_from_dict(self.loaded_invoice_data_dict)
        
        for r in range(self.lines_table.rowCount()): self._populate_line_combos(r)

    async def _load_existing_invoice_data(self):
        if not self.invoice_id or not self.app_core.sales_invoice_manager: return
        self.loaded_invoice_orm = await self.app_core.sales_invoice_manager.get_invoice_for_dialog(self.invoice_id)
        self.setWindowTitle(self._get_window_title()) 
        if self.loaded_invoice_orm:
            inv_dict = {col.name: getattr(self.loaded_invoice_orm, col.name) for col in SalesInvoice.__table__.columns if hasattr(self.loaded_invoice_orm, col.name)}
            inv_dict["lines"] = []
            if self.loaded_invoice_orm.lines: 
                for line_orm in self.loaded_invoice_orm.lines:
                    line_dict = {col.name: getattr(line_orm, col.name) for col in SalesInvoiceLine.__table__.columns if hasattr(line_orm, col.name)}
                    inv_dict["lines"].append(line_dict)
            
            invoice_json_str = json.dumps(inv_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, invoice_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Sales Invoice ID {self.invoice_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_dialog_from_data_slot(self, invoice_json_str: str):
        try:
            data = json.loads(invoice_json_str, object_hook=json_date_hook)
            self.loaded_invoice_data_dict = data 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing invoice data."); return

        self.invoice_no_label.setText(data.get("invoice_no", "N/A"))
        self.invoice_no_label.setStyleSheet("font-style: normal; color: black;" if data.get("invoice_no") else "font-style: italic; color: grey;")
        
        if data.get("invoice_date"): self.invoice_date_edit.setDate(QDate(data["invoice_date"]))
        if data.get("due_date"): self.due_date_edit.setDate(QDate(data["due_date"]))
        
        cust_idx = self.customer_combo.findData(data.get("customer_id"))
        if cust_idx != -1: self.customer_combo.setCurrentIndex(cust_idx)
        else: self.app_core.logger.warning(f"Loaded invoice customer ID '{data.get('customer_id')}' not found in combo.")

        curr_idx = self.currency_combo.findData(data.get("currency_code"))
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
        else: self.app_core.logger.warning(f"Loaded invoice currency '{data.get('currency_code')}' not found in combo.")
        self.exchange_rate_spin.setValue(float(data.get("exchange_rate", 1.0) or 1.0))
        self._on_currency_changed(self.currency_combo.currentIndex()) 

        self.notes_edit.setText(data.get("notes", "") or "")
        self.terms_edit.setText(data.get("terms_and_conditions", "") or "")

        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_invoice_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_invoice_line()
        
        self._update_invoice_totals() 
        self._set_read_only_state(self.view_only_mode or (data.get("status") != InvoiceStatusEnum.DRAFT.value))

    def _populate_fields_from_orm(self, invoice_orm: SalesInvoice): 
        cust_idx = self.customer_combo.findData(invoice_orm.customer_id)
        if cust_idx != -1: self.customer_combo.setCurrentIndex(cust_idx)
        curr_idx = self.currency_combo.findData(invoice_orm.currency_code)
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
    
    def _set_read_only_state(self, read_only: bool):
        self.customer_combo.setEnabled(not read_only)
        for w in [self.invoice_date_edit, self.due_date_edit, self.notes_edit, self.terms_edit]:
            if hasattr(w, 'setReadOnly'): w.setReadOnly(read_only) # type: ignore
        self.currency_combo.setEnabled(not read_only)
        self._on_currency_changed(self.currency_combo.currentIndex()) 
        if read_only: self.exchange_rate_spin.setReadOnly(True)

        self.add_line_button.setEnabled(not read_only)
        self.remove_line_button.setEnabled(not read_only)
        
        is_draft = True 
        if self.loaded_invoice_data_dict:
            is_draft = (self.loaded_invoice_data_dict.get("status") == InvoiceStatusEnum.DRAFT.value)
        elif self.loaded_invoice_orm:
            is_draft = (self.loaded_invoice_orm.status == InvoiceStatusEnum.DRAFT.value)

        can_edit_or_create = not self.view_only_mode and (self.invoice_id is None or is_draft)

        self.save_draft_button.setVisible(can_edit_or_create)
        self.save_approve_button.setVisible(can_edit_or_create)
        self.save_approve_button.setEnabled(can_edit_or_create) 

        edit_trigger = QAbstractItemView.EditTrigger.NoEditTriggers if read_only else QAbstractItemView.EditTrigger.AllInputs
        self.lines_table.setEditTriggers(edit_trigger)
        for r in range(self.lines_table.rowCount()):
            del_btn_widget = self.lines_table.cellWidget(r, self.COL_DEL)
            if del_btn_widget: del_btn_widget.setEnabled(not read_only)

    def _add_new_invoice_line(self, line_data: Optional[Dict[str, Any]] = None):
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)

        del_btn = QPushButton(QIcon(self.icon_path_prefix + "remove.svg")); del_btn.setFixedSize(24,24); del_btn.setToolTip("Remove this line")
        del_btn.clicked.connect(lambda _, r=row: self._remove_specific_invoice_line(r))
        self.lines_table.setCellWidget(row, self.COL_DEL, del_btn)

        prod_combo = QComboBox(); prod_combo.setEditable(True); prod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        prod_completer = QCompleter(); prod_completer.setFilterMode(Qt.MatchFlag.MatchContains); prod_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        prod_combo.setCompleter(prod_completer)
        prod_combo.setMaxVisibleItems(15) # Set max visible items
        self.lines_table.setCellWidget(row, self.COL_PROD, prod_combo)
        
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row, self.COL_DESC, desc_item) 

        qty_spin = QDoubleSpinBox(); qty_spin.setDecimals(2); qty_spin.setRange(0.01, 999999.99); qty_spin.setValue(float(line_data.get("quantity", 1.0) or 1.0) if line_data else 1.0)
        self.lines_table.setCellWidget(row, self.COL_QTY, qty_spin)
        price_spin = QDoubleSpinBox(); price_spin.setDecimals(4); price_spin.setRange(0, 999999.9999); price_spin.setValue(float(line_data.get("unit_price", 0.0) or 0.0) if line_data else 0.0)
        self.lines_table.setCellWidget(row, self.COL_PRICE, price_spin)
        disc_spin = QDoubleSpinBox(); disc_spin.setDecimals(2); disc_spin.setRange(0, 100.00); disc_spin.setValue(float(line_data.get("discount_percent", 0.0) or 0.0) if line_data else 0.0)
        self.lines_table.setCellWidget(row, self.COL_DISC_PCT, disc_spin)

        tax_combo = QComboBox(); self.lines_table.setCellWidget(row, self.COL_TAX_CODE, tax_combo)

        for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
            item = QTableWidgetItem("0.00"); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable); self.lines_table.setItem(row, col_idx, item)

        self._populate_line_combos(row, line_data) 
        
        prod_combo.currentIndexChanged.connect(lambda idx, r=row, pc=prod_combo: self._on_line_product_changed(r, pc.itemData(idx)))
        qty_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        price_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        disc_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        tax_combo.currentIndexChanged.connect(lambda idx, r=row: self._trigger_line_recalculation_slot(r))

        if line_data: self._calculate_line_item_totals(row)
        self._update_invoice_totals()

    def _populate_line_combos(self, row: int, line_data: Optional[Dict[str, Any]] = None):
        prod_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_PROD))
        prod_combo.clear(); prod_combo.addItem("-- Select Product/Service --", 0)
        current_prod_id = line_data.get("product_id") if line_data else None
        selected_prod_idx = 0 
        for i, prod_dict in enumerate(self._products_cache):
            price_val = prod_dict.get('sales_price')
            price_str = f"{Decimal(str(price_val)):.2f}" if price_val is not None else "N/A"
            # ProductTypeEnum is how it's stored in DTO/cache if model_dump was used on ProductSummaryData
            prod_type_val = prod_dict.get('product_type')
            type_str = prod_type_val if isinstance(prod_type_val, str) else (prod_type_val.value if isinstance(prod_type_val, ProductTypeEnum) else "Unknown")

            display_text = f"{prod_dict['product_code']} - {prod_dict['name']} (Type: {type_str}, Price: {price_str})"
            prod_combo.addItem(display_text, prod_dict['id'])
            if prod_dict['id'] == current_prod_id: selected_prod_idx = i + 1
        prod_combo.setCurrentIndex(selected_prod_idx)
        if isinstance(prod_combo.completer(), QCompleter): prod_combo.completer().setModel(prod_combo.model()) # type: ignore
        
        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
        tax_combo.clear(); tax_combo.addItem("None", "") 
        current_tax_code_str = line_data.get("tax_code") if line_data else None
        selected_tax_idx = 0 
        for i, tc_dict in enumerate(self._tax_codes_cache):
            tax_combo.addItem(tc_dict['description'], tc_dict['code']) 
            if tc_dict['code'] == current_tax_code_str: selected_tax_idx = i + 1
        tax_combo.setCurrentIndex(selected_tax_idx)

    @Slot(int)
    def _on_line_product_changed(self, row:int, product_id_data: Any): 
        if not isinstance(product_id_data, int) or product_id_data == 0: 
             self._calculate_line_item_totals(row); return

        product_id = product_id_data
        product_detail = next((p for p in self._products_cache if p['id'] == product_id), None)
        
        if product_detail:
            desc_item = self.lines_table.item(row, self.COL_DESC)
            if desc_item and (not desc_item.text().strip() or "-- Select Product/Service --" in self.lines_table.cellWidget(row, self.COL_PROD).itemText(0)): # Auto-fill if default/empty
                desc_item.setText(product_detail.get('name', ''))
            
            price_widget = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            if price_widget and price_widget.value() == 0.0 and product_detail.get('sales_price') is not None:
                try: price_widget.setValue(float(Decimal(str(product_detail['sales_price']))))
                except: pass 
        self._calculate_line_item_totals(row)

    def _remove_selected_invoice_line(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): return
        current_row = self.lines_table.currentRow()
        if current_row >= 0: self._remove_specific_invoice_line(current_row)

    def _remove_specific_invoice_line(self, row:int):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): return
        self.lines_table.removeRow(row); self._update_invoice_totals()

    @Slot(QTableWidgetItem)
    def _on_line_item_changed_desc_only(self, item: QTableWidgetItem): 
        if item.column() == self.COL_DESC:
             pass 

    @Slot() 
    def _trigger_line_recalculation_slot(self, row_for_recalc: Optional[int] = None):
        current_row = row_for_recalc
        if current_row is None: 
            sender_widget = self.sender()
            if sender_widget and isinstance(sender_widget, QWidget):
                for r in range(self.lines_table.rowCount()):
                    for c in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT, self.COL_TAX_CODE, self.COL_PROD]:
                        if self.lines_table.cellWidget(r,c) == sender_widget: current_row = r; break
                    if current_row is not None: break
        if current_row is not None: self._calculate_line_item_totals(current_row)

    def _format_decimal_for_cell(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: return "0.00" if not show_zero_as_blank else ""
        if show_zero_as_blank and value.is_zero(): return ""
        return f"{value:,.2f}"

    def _calculate_line_item_totals(self, row: int):
        try:
            qty_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_QTY))
            price_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            disc_pct_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_DISC_PCT))
            tax_combo_w = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))

            qty = Decimal(str(qty_w.value()))
            price = Decimal(str(price_w.value()))
            disc_pct = Decimal(str(disc_pct_w.value()))
            
            discount_amount = (qty * price * (disc_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            
            tax_code_str = tax_combo_w.currentData() if tax_combo_w and tax_combo_w.currentIndex() > 0 else None
            line_tax_amount = Decimal(0)
            
            if tax_code_str and line_subtotal_before_tax != Decimal(0):
                tax_code_detail = next((tc for tc in self._tax_codes_cache if tc.get("code") == tax_code_str), None)
                if tax_code_detail and tax_code_detail.get("rate") is not None:
                    rate = Decimal(str(tax_code_detail["rate"]))
                    line_tax_amount = (line_subtotal_before_tax * (rate / Decimal(100))).quantize(Decimal("0.01"), ROUND_HALF_UP)
            
            line_total = line_subtotal_before_tax + line_tax_amount

            self.lines_table.item(row, self.COL_SUBTOTAL).setText(self._format_decimal_for_cell(line_subtotal_before_tax.quantize(Decimal("0.01")), False))
            self.lines_table.item(row, self.COL_TAX_AMT).setText(self._format_decimal_for_cell(line_tax_amount, True))
            self.lines_table.item(row, self.COL_TOTAL).setText(self._format_decimal_for_cell(line_total.quantize(Decimal("0.01")), False))
        except Exception as e:
            self.app_core.logger.error(f"Error calculating line totals for row {row}: {e}", exc_info=True)
            for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
                item = self.lines_table.item(row, col_idx)
                if item: item.setText("Error")
        finally:
            self._update_invoice_totals()

    def _update_invoice_totals(self):
        invoice_subtotal_agg = Decimal(0)
        total_tax_agg = Decimal(0)
        for r in range(self.lines_table.rowCount()):
            try:
                sub_item = self.lines_table.item(r, self.COL_SUBTOTAL)
                tax_item = self.lines_table.item(r, self.COL_TAX_AMT)
                if sub_item and sub_item.text() and sub_item.text() != "Error": 
                    invoice_subtotal_agg += Decimal(sub_item.text().replace(',',''))
                if tax_item and tax_item.text() and tax_item.text() != "Error": 
                    total_tax_agg += Decimal(tax_item.text().replace(',',''))
            except (InvalidOperation, AttributeError) as e:
                 self.app_core.logger.warning(f"Could not parse amount from line {r} during total update: {e}")
        
        grand_total_agg = invoice_subtotal_agg + total_tax_agg
        self.subtotal_display.setText(self._format_decimal_for_cell(invoice_subtotal_agg, False))
        self.total_tax_display.setText(self._format_decimal_for_cell(total_tax_agg, False))
        self.grand_total_display.setText(self._format_decimal_for_cell(grand_total_agg, False))
        
    def _collect_data(self) -> Optional[Union[SalesInvoiceCreateData, SalesInvoiceUpdateData]]:
        customer_id_data = self.customer_combo.currentData()
        if not customer_id_data or customer_id_data == 0:
            QMessageBox.warning(self, "Validation Error", "Customer must be selected.")
            return None
        customer_id = int(customer_id_data)

        invoice_date_py = self.invoice_date_edit.date().toPython()
        due_date_py = self.due_date_edit.date().toPython()
        if due_date_py < invoice_date_py:
            QMessageBox.warning(self, "Validation Error", "Due date cannot be before invoice date.")
            return None
        
        line_dtos: List[SalesInvoiceLineBaseData] = []
        for r in range(self.lines_table.rowCount()):
            try:
                prod_combo = cast(QComboBox, self.lines_table.cellWidget(r, self.COL_PROD))
                desc_item = self.lines_table.item(r, self.COL_DESC)
                qty_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_QTY))
                price_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_PRICE))
                disc_pct_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_DISC_PCT))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(r, self.COL_TAX_CODE))

                product_id_data = prod_combo.currentData() if prod_combo else None
                product_id = int(product_id_data) if product_id_data and product_id_data != 0 else None
                
                description = desc_item.text().strip() if desc_item else ""
                quantity = Decimal(str(qty_spin.value()))
                unit_price = Decimal(str(price_spin.value()))
                discount_percent = Decimal(str(disc_pct_spin.value()))
                tax_code_str = tax_combo.currentData() if tax_combo and tax_combo.currentData() else None

                if not description and not product_id: continue 
                if quantity <= 0:
                    QMessageBox.warning(self, "Validation Error", f"Quantity must be positive on line {r+1}.")
                    return None
                if unit_price < 0:
                     QMessageBox.warning(self, "Validation Error", f"Unit price cannot be negative on line {r+1}.")
                     return None

                line_dtos.append(SalesInvoiceLineBaseData(
                    product_id=product_id, description=description, quantity=quantity,
                    unit_price=unit_price, discount_percent=discount_percent, tax_code=tax_code_str
                ))
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Error processing line {r + 1}: {str(e)}"); return None
        
        if not line_dtos:
            QMessageBox.warning(self, "Input Error", "Sales invoice must have at least one valid line item."); return None

        common_data = {
            "customer_id": customer_id, "invoice_date": invoice_date_py, "due_date": due_date_py,
            "currency_code": self.currency_combo.currentData() or self._base_currency,
            "exchange_rate": Decimal(str(self.exchange_rate_spin.value())),
            "notes": self.notes_edit.toPlainText().strip() or None,
            "terms_and_conditions": self.terms_edit.toPlainText().strip() or None,
            "user_id": self.current_user_id, "lines": line_dtos
        }
        try:
            if self.invoice_id: return SalesInvoiceUpdateData(id=self.invoice_id, **common_data) # type: ignore
            else: return SalesInvoiceCreateData(**common_data) # type: ignore
        except ValueError as ve: 
            QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{str(ve)}"); return None

    @Slot()
    def on_save_draft(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value):
             QMessageBox.information(self, "Info", "Cannot save. Invoice is not a draft or in view-only mode.")
             return
        
        dto = self._collect_data()
        if dto:
            self._set_buttons_for_async_operation(True)
            future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=False))
            if future: future.add_done_callback(lambda _: self._set_buttons_for_async_operation(False))
            else: self._set_buttons_for_async_operation(False) 

    @Slot()
    def on_save_and_approve(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value):
            QMessageBox.information(self, "Info", "Cannot Save & Approve. Invoice is not a draft or in view-only mode.")
            return
        
        dto = self._collect_data()
        if dto:
            self._set_buttons_for_async_operation(True)
            future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=True))
            if future: future.add_done_callback(lambda _: self._set_buttons_for_async_operation(False))
            else: self._set_buttons_for_async_operation(False)

    def _set_buttons_for_async_operation(self, busy: bool):
        self.save_draft_button.setEnabled(not busy)
        can_approve = (self.invoice_id is None or (self.loaded_invoice_orm and self.loaded_invoice_orm.status == InvoiceStatusEnum.DRAFT.value)) and not self.view_only_mode
        self.save_approve_button.setEnabled(not busy and can_approve)


    async def _perform_save(self, dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData], post_invoice_after: bool):
        if not self.app_core.sales_invoice_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Sales Invoice Manager not available."))
            return

        save_result: Result[SalesInvoice]
        is_update = isinstance(dto, SalesInvoiceUpdateData)
        action_verb_past = "updated" if is_update else "created"

        if is_update:
            save_result = await self.app_core.sales_invoice_manager.update_draft_invoice(dto.id, dto) 
        else:
            save_result = await self.app_core.sales_invoice_manager.create_draft_invoice(dto) 

        if not save_result.is_success or not save_result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to {('update' if is_update else 'create')} sales invoice draft:\n{', '.join(save_result.errors)}"))
            return 

        saved_invoice = save_result.value
        self.invoice_saved.emit(saved_invoice.id) 
        self.invoice_id = saved_invoice.id 
        self.loaded_invoice_orm = saved_invoice 
        self.setWindowTitle(self._get_window_title()) 
        self.invoice_no_label.setText(saved_invoice.invoice_no)
        self.invoice_no_label.setStyleSheet("font-style: normal; color: black;")


        if not post_invoice_after:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str, f"Sales Invoice draft {action_verb_past} successfully (ID: {saved_invoice.id}, No: {saved_invoice.invoice_no})."))
            self._set_read_only_state(self.view_only_mode or (saved_invoice.status != InvoiceStatusEnum.DRAFT.value)) 
            return

        post_result: Result[SalesInvoice] = await self.app_core.sales_invoice_manager.post_invoice(saved_invoice.id, self.current_user_id)
        
        if post_result.is_success:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str, f"Sales Invoice {saved_invoice.invoice_no} saved and posted successfully. JE created."))
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection) 
        else:
            msg = (f"Sales Invoice {saved_invoice.invoice_no} was saved as a Draft successfully, "
                   f"BUT FAILED to post/approve:\n{', '.join(post_result.errors)}\n\n"
                   "Please review and post manually from the invoice list.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Posting Error After Save"), Q_ARG(str, msg))
            self._set_read_only_state(self.view_only_mode or (saved_invoice.status != InvoiceStatusEnum.DRAFT.value))

    @Slot(int)
    def _on_customer_changed(self, index: int):
        customer_id = self.customer_combo.itemData(index)
        if customer_id and customer_id != 0 and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("currency_code"):
                curr_idx = self.currency_combo.findData(customer_data["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
            if customer_data and customer_data.get("credit_terms") is not None:
                self.due_date_edit.setDate(self.invoice_date_edit.date().addDays(int(customer_data["credit_terms"])))

    @Slot(int)
    def _on_currency_changed(self, index: int):
        currency_code = self.currency_combo.currentData()
        is_base = (currency_code == self._base_currency)
        self.exchange_rate_spin.setEnabled(not is_base and not self.view_only_mode) 
        self.exchange_rate_spin.setReadOnly(is_base or self.view_only_mode) 
        if is_base: self.exchange_rate_spin.setValue(1.0)

    @Slot(QDate)
    def _on_invoice_date_changed(self, new_date: QDate):
        customer_id = self.customer_combo.currentData()
        terms = 30 
        if customer_id and customer_id != 0 and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("credit_terms") is not None:
                try: terms = int(customer_data["credit_terms"])
                except: pass
        self.due_date_edit.setDate(new_date.addDays(terms))


```

# app/ui/sales_invoices/sales_invoice_table_model.py
```py
# app/ui/sales_invoices/sales_invoice_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import SalesInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum

class SalesInvoiceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[SalesInvoiceSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Inv No.", "Inv Date", "Due Date", 
            "Customer", "Total", "Paid", "Balance", "Status"
        ]
        self._data: List[SalesInvoiceSummaryData] = data or []

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

    def _format_decimal_for_table(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: 
            return "0.00" if not show_zero_as_blank else ""
        try:
            d_value = Decimal(str(value))
            if show_zero_as_blank and d_value == Decimal(0):
                return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) # Fallback

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        invoice_summary: SalesInvoiceSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_')
            
            if col == 0: return str(invoice_summary.id)
            if col == 1: return invoice_summary.invoice_no
            if col == 2: # Inv Date
                inv_date = invoice_summary.invoice_date
                return inv_date.strftime('%d/%m/%Y') if isinstance(inv_date, python_date) else str(inv_date)
            if col == 3: # Due Date
                due_date = invoice_summary.due_date
                return due_date.strftime('%d/%m/%Y') if isinstance(due_date, python_date) else str(due_date)
            if col == 4: return invoice_summary.customer_name
            if col == 5: return self._format_decimal_for_table(invoice_summary.total_amount, False) # Total
            if col == 6: return self._format_decimal_for_table(invoice_summary.amount_paid, True)  # Paid
            if col == 7: # Balance
                balance = invoice_summary.total_amount - invoice_summary.amount_paid
                return self._format_decimal_for_table(balance, False)
            if col == 8: # Status
                status_val = invoice_summary.status
                return status_val.value if isinstance(status_val, InvoiceStatusEnum) else str(status_val)
            
            return str(getattr(invoice_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole: # Store ID for quick retrieval
            if col == 0: 
                return invoice_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Total", "Paid", "Balance"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Status":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_invoice_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_invoice_status_at_row(self, row: int) -> Optional[InvoiceStatusEnum]:
        if 0 <= row < len(self._data):
            status_val = self._data[row].status
            return status_val if isinstance(status_val, InvoiceStatusEnum) else None
        return None

    def update_data(self, new_data: List[SalesInvoiceSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


```

# app/ui/vendors/vendor_table_model.py
```py
# File: app/ui/vendors/vendor_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import VendorSummaryData # Using the DTO for type safety

class VendorTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[VendorSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers should match fields in VendorSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Email", "Phone", "Active"]
        self._data: List[VendorSummaryData] = data or []

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
            
        vendor_summary: VendorSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(vendor_summary.id)
            if col == 1: return vendor_summary.vendor_code
            if col == 2: return vendor_summary.name
            if col == 3: return str(vendor_summary.email) if vendor_summary.email else ""
            if col == 4: return vendor_summary.phone if vendor_summary.phone else ""
            if col == 5: return "Yes" if vendor_summary.is_active else "No"
            
            header_key = self._headers[col].lower().replace(' ', '_')
            return str(getattr(vendor_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: 
                return vendor_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 5: # Active status
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_vendor_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_vendor_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[VendorSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/vendors/vendor_dialog.py
```py
# File: app/ui/vendors/vendor_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox, # Added QDoubleSpinBox
    QCompleter
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import VendorCreateData, VendorUpdateData
from app.models.business.vendor import Vendor
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class VendorDialog(QDialog):
    vendor_saved = Signal(int) # Emits vendor ID on successful save

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 vendor_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.vendor_id = vendor_id
        self.loaded_vendor_data: Optional[Vendor] = None 

        self._currencies_cache: List[Currency] = []
        self._payables_accounts_cache: List[Account] = []
        
        self.setWindowTitle("Edit Vendor" if self.vendor_id else "Add New Vendor")
        self.setMinimumWidth(600) # Adjusted width for more fields
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        if self.vendor_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_vendor_details()))

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Basic Info
        self.vendor_code_edit = QLineEdit(); form_layout.addRow("Vendor Code*:", self.vendor_code_edit)
        self.name_edit = QLineEdit(); form_layout.addRow("Vendor Name*:", self.name_edit)
        self.legal_name_edit = QLineEdit(); form_layout.addRow("Legal Name:", self.legal_name_edit)
        self.uen_no_edit = QLineEdit(); form_layout.addRow("UEN No.:", self.uen_no_edit)
        
        gst_layout = QHBoxLayout()
        self.gst_registered_check = QCheckBox("GST Registered"); gst_layout.addWidget(self.gst_registered_check)
        self.gst_no_edit = QLineEdit(); self.gst_no_edit.setPlaceholderText("GST Registration No."); gst_layout.addWidget(self.gst_no_edit)
        form_layout.addRow(gst_layout)

        wht_layout = QHBoxLayout()
        self.wht_applicable_check = QCheckBox("WHT Applicable"); wht_layout.addWidget(self.wht_applicable_check)
        self.wht_rate_spin = QDoubleSpinBox(); 
        self.wht_rate_spin.setDecimals(2); self.wht_rate_spin.setRange(0, 100); self.wht_rate_spin.setSuffix(" %")
        wht_layout.addWidget(self.wht_rate_spin)
        form_layout.addRow(wht_layout)


        # Contact Info
        self.contact_person_edit = QLineEdit(); form_layout.addRow("Contact Person:", self.contact_person_edit)
        self.email_edit = QLineEdit(); self.email_edit.setPlaceholderText("example@domain.com"); form_layout.addRow("Email:", self.email_edit)
        self.phone_edit = QLineEdit(); form_layout.addRow("Phone:", self.phone_edit)

        # Address Info
        self.address_line1_edit = QLineEdit(); form_layout.addRow("Address Line 1:", self.address_line1_edit)
        self.address_line2_edit = QLineEdit(); form_layout.addRow("Address Line 2:", self.address_line2_edit)
        self.postal_code_edit = QLineEdit(); form_layout.addRow("Postal Code:", self.postal_code_edit)
        self.city_edit = QLineEdit(); self.city_edit.setText("Singapore"); form_layout.addRow("City:", self.city_edit)
        self.country_edit = QLineEdit(); self.country_edit.setText("Singapore"); form_layout.addRow("Country:", self.country_edit)
        
        # Financial Info
        self.payment_terms_spin = QSpinBox(); self.payment_terms_spin.setRange(0, 365); self.payment_terms_spin.setValue(30); form_layout.addRow("Payment Terms (Days):", self.payment_terms_spin)
        
        self.currency_code_combo = QComboBox(); self.currency_code_combo.setMinimumWidth(150)
        form_layout.addRow("Default Currency*:", self.currency_code_combo)
        
        self.payables_account_combo = QComboBox(); self.payables_account_combo.setMinimumWidth(250)
        form_layout.addRow("A/P Account:", self.payables_account_combo)

        # Bank Details
        bank_details_group = QGroupBox("Vendor Bank Details")
        bank_form_layout = QFormLayout(bank_details_group)
        self.bank_account_name_edit = QLineEdit(); bank_form_layout.addRow("Account Name:", self.bank_account_name_edit)
        self.bank_account_number_edit = QLineEdit(); bank_form_layout.addRow("Account Number:", self.bank_account_number_edit)
        self.bank_name_edit = QLineEdit(); bank_form_layout.addRow("Bank Name:", self.bank_name_edit)
        self.bank_branch_edit = QLineEdit(); bank_form_layout.addRow("Bank Branch:", self.bank_branch_edit)
        self.bank_swift_code_edit = QLineEdit(); bank_form_layout.addRow("SWIFT Code:", self.bank_swift_code_edit)
        form_layout.addRow(bank_details_group)


        # Other Info
        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True); form_layout.addRow(self.is_active_check)
        self.vendor_since_date_edit = QDateEdit(QDate.currentDate()); self.vendor_since_date_edit.setCalendarPopup(True); self.vendor_since_date_edit.setDisplayFormat("dd/MM/yyyy"); form_layout.addRow("Vendor Since:", self.vendor_since_date_edit)
        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(80); form_layout.addRow("Notes:", self.notes_edit)
        
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_vendor)
        self.button_box.rejected.connect(self.reject)
        self.gst_registered_check.stateChanged.connect(lambda state: self.gst_no_edit.setEnabled(state == Qt.CheckState.Checked.value))
        self.gst_no_edit.setEnabled(self.gst_registered_check.isChecked())
        self.wht_applicable_check.stateChanged.connect(lambda state: self.wht_rate_spin.setEnabled(state == Qt.CheckState.Checked.value))
        self.wht_rate_spin.setEnabled(self.wht_applicable_check.isChecked())


    async def _load_combo_data(self):
        try:
            if self.app_core.currency_manager:
                active_currencies = await self.app_core.currency_manager.get_all_currencies()
                self._currencies_cache = [c for c in active_currencies if c.is_active]
            
            if self.app_core.chart_of_accounts_manager:
                # Fetch Liability accounts, ideally filtered for AP control accounts
                ap_accounts = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(account_type="Liability", active_only=True)
                self._payables_accounts_cache = [acc for acc in ap_accounts if acc.is_active and (acc.is_control_account or "Payable" in acc.name)] # Basic filter
            
            currencies_json = json.dumps([{"code": c.code, "name": c.name} for c in self._currencies_cache], default=json_converter)
            accounts_json = json.dumps([{"id": acc.id, "code": acc.code, "name": acc.name} for acc in self._payables_accounts_cache], default=json_converter)

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, currencies_json), Q_ARG(str, accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for VendorDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str)
    def _populate_combos_slot(self, currencies_json: str, accounts_json: str):
        try:
            currencies_data = json.loads(currencies_json, object_hook=json_date_hook)
            accounts_data = json.loads(accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing combo JSON data for VendorDialog: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing dropdown data.")
            return

        self.currency_code_combo.clear()
        for curr in currencies_data: self.currency_code_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        
        self.payables_account_combo.clear()
        self.payables_account_combo.addItem("None", 0) 
        for acc in accounts_data: self.payables_account_combo.addItem(f"{acc['code']} - {acc['name']}", acc['id'])
        
        if self.loaded_vendor_data: # If editing, set current values after combos are populated
            self._populate_fields_from_orm(self.loaded_vendor_data)


    async def _load_existing_vendor_details(self):
        if not self.vendor_id or not self.app_core.vendor_manager: return # Changed from customer_manager
        self.loaded_vendor_data = await self.app_core.vendor_manager.get_vendor_for_dialog(self.vendor_id) # Changed
        if self.loaded_vendor_data:
            vendor_dict = {col.name: getattr(self.loaded_vendor_data, col.name) for col in Vendor.__table__.columns}
            vendor_json_str = json.dumps(vendor_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, vendor_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Vendor ID {self.vendor_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, vendor_json_str: str):
        try:
            vendor_data = json.loads(vendor_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse vendor data for editing."); return
        self._populate_fields_from_dict(vendor_data)

    def _populate_fields_from_orm(self, vendor_orm: Vendor): # Called after combos populated, if editing
        currency_idx = self.currency_code_combo.findData(vendor_orm.currency_code)
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        else: self.app_core.logger.warning(f"Loaded vendor currency '{vendor_orm.currency_code}' not found in active currencies combo.")

        ap_acc_idx = self.payables_account_combo.findData(vendor_orm.payables_account_id or 0)
        if ap_acc_idx != -1: self.payables_account_combo.setCurrentIndex(ap_acc_idx)
        elif vendor_orm.payables_account_id:
             self.app_core.logger.warning(f"Loaded vendor A/P account ID '{vendor_orm.payables_account_id}' not found in combo.")

    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.vendor_code_edit.setText(data.get("vendor_code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.legal_name_edit.setText(data.get("legal_name", "") or "")
        self.uen_no_edit.setText(data.get("uen_no", "") or "")
        self.gst_registered_check.setChecked(data.get("gst_registered", False))
        self.gst_no_edit.setText(data.get("gst_no", "") or ""); self.gst_no_edit.setEnabled(data.get("gst_registered", False))
        self.wht_applicable_check.setChecked(data.get("withholding_tax_applicable", False))
        self.wht_rate_spin.setValue(float(data.get("withholding_tax_rate", 0.0) or 0.0))
        self.wht_rate_spin.setEnabled(data.get("withholding_tax_applicable", False))
        self.contact_person_edit.setText(data.get("contact_person", "") or "")
        self.email_edit.setText(data.get("email", "") or "")
        self.phone_edit.setText(data.get("phone", "") or "")
        self.address_line1_edit.setText(data.get("address_line1", "") or "")
        self.address_line2_edit.setText(data.get("address_line2", "") or "")
        self.postal_code_edit.setText(data.get("postal_code", "") or "")
        self.city_edit.setText(data.get("city", "") or "Singapore")
        self.country_edit.setText(data.get("country", "") or "Singapore")
        self.payment_terms_spin.setValue(data.get("payment_terms", 30))
        
        currency_idx = self.currency_code_combo.findData(data.get("currency_code", "SGD"))
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        
        ap_acc_id = data.get("payables_account_id")
        ap_acc_idx = self.payables_account_combo.findData(ap_acc_id if ap_acc_id is not None else 0)
        if ap_acc_idx != -1: self.payables_account_combo.setCurrentIndex(ap_acc_idx)

        self.bank_account_name_edit.setText(data.get("bank_account_name","") or "")
        self.bank_account_number_edit.setText(data.get("bank_account_number","") or "")
        self.bank_name_edit.setText(data.get("bank_name","") or "")
        self.bank_branch_edit.setText(data.get("bank_branch","") or "")
        self.bank_swift_code_edit.setText(data.get("bank_swift_code","") or "")

        self.is_active_check.setChecked(data.get("is_active", True))
        vs_date = data.get("vendor_since")
        self.vendor_since_date_edit.setDate(QDate(vs_date) if vs_date else QDate.currentDate())
        self.notes_edit.setText(data.get("notes", "") or "")

    @Slot()
    def on_save_vendor(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        payables_acc_id_data = self.payables_account_combo.currentData()
        payables_acc_id = int(payables_acc_id_data) if payables_acc_id_data and int(payables_acc_id_data) != 0 else None
        
        vendor_since_py_date = self.vendor_since_date_edit.date().toPython()

        data_dict = {
            "vendor_code": self.vendor_code_edit.text().strip(), "name": self.name_edit.text().strip(),
            "legal_name": self.legal_name_edit.text().strip() or None, "uen_no": self.uen_no_edit.text().strip() or None,
            "gst_registered": self.gst_registered_check.isChecked(),
            "gst_no": self.gst_no_edit.text().strip() if self.gst_registered_check.isChecked() else None,
            "withholding_tax_applicable": self.wht_applicable_check.isChecked(),
            "withholding_tax_rate": Decimal(str(self.wht_rate_spin.value())) if self.wht_applicable_check.isChecked() else None,
            "contact_person": self.contact_person_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None, 
            "phone": self.phone_edit.text().strip() or None,
            "address_line1": self.address_line1_edit.text().strip() or None,
            "address_line2": self.address_line2_edit.text().strip() or None,
            "postal_code": self.postal_code_edit.text().strip() or None,
            "city": self.city_edit.text().strip() or None,
            "country": self.country_edit.text().strip() or "Singapore",
            "payment_terms": self.payment_terms_spin.value(),
            "currency_code": self.currency_code_combo.currentData() or "SGD",
            "is_active": self.is_active_check.isChecked(),
            "vendor_since": vendor_since_py_date,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "bank_account_name": self.bank_account_name_edit.text().strip() or None,
            "bank_account_number": self.bank_account_number_edit.text().strip() or None,
            "bank_name": self.bank_name_edit.text().strip() or None,
            "bank_branch": self.bank_branch_edit.text().strip() or None,
            "bank_swift_code": self.bank_swift_code_edit.text().strip() or None,
            "payables_account_id": payables_acc_id,
            "user_id": self.current_user_id
        }

        try:
            if self.vendor_id: dto = VendorUpdateData(id=self.vendor_id, **data_dict) # type: ignore
            else: dto = VendorCreateData(**data_dict) # type: ignore
        except ValueError as pydantic_error: 
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}"); return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button else None)

    async def _perform_save(self, dto: VendorCreateData | VendorUpdateData):
        if not self.app_core.vendor_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Vendor Manager not available."))
            return

        result: Result[Vendor]
        if isinstance(dto, VendorUpdateData): result = await self.app_core.vendor_manager.update_vendor(dto.id, dto)
        else: result = await self.app_core.vendor_manager.create_vendor(dto)

        if result.is_success and result.value:
            action = "updated" if isinstance(dto, VendorUpdateData) else "created"
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Vendor {action} successfully (ID: {result.value.id})."))
            self.vendor_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save vendor:\n{', '.join(result.errors)}"))

```

# app/ui/vendors/__init__.py
```py
# app/ui/vendors/__init__.py
from .vendors_widget import VendorsWidget # Was previously just a stub, now functional
from .vendor_dialog import VendorDialog
from .vendor_table_model import VendorTableModel

__all__ = [
    "VendorsWidget",
    "VendorDialog",
    "VendorTableModel",
]


```

# app/ui/vendors/vendors_widget.py
```py
# app/ui/vendors/vendors_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox # Added for filtering/search
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.vendors.vendor_table_model import VendorTableModel 
from app.ui.vendors.vendor_dialog import VendorDialog 
from app.utils.pydantic_models import VendorSummaryData 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.vendor import Vendor # For Result type hint from manager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class VendorsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for VendorsWidget.")
        except ImportError:
            self.app_core.logger.info("VendorsWidget: Compiled Qt resources not found. Using direct file paths.")
            # self.icon_path_prefix remains "resources/icons/"

        self._init_ui()
        # Initial load triggered by filter button click to respect default filter settings
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_vendors()))


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        # --- Toolbar ---
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        # --- Filter/Search Area ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter code, name, or email...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger) 
        filter_layout.addWidget(self.search_edit)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger) 
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"),"Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # --- Table View ---
        self.vendors_table = QTableView()
        self.vendors_table.setAlternatingRowColors(True)
        self.vendors_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vendors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vendors_table.horizontalHeader().setStretchLastSection(False) # Changed for better control
        self.vendors_table.doubleClicked.connect(self._on_edit_vendor) # Or view_vendor
        self.vendors_table.setSortingEnabled(True)

        self.table_model = VendorTableModel()
        self.vendors_table.setModel(self.table_model)
        
        # Configure columns after model is set
        header = self.vendors_table.horizontalHeader()
        for i in range(self.table_model.columnCount()): # Default to ResizeToContents
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.vendors_table.setColumnHidden(id_col_idx, True)
        
        if "Name" in self.table_model._headers:
            name_col_model_idx = self.table_model._headers.index("Name")
            # Calculate visible index for "Name" if "ID" is hidden before it
            visible_name_idx = name_col_model_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_model_idx and self.vendors_table.isColumnHidden(self.table_model._headers.index("ID")):
                visible_name_idx -=1
            
            if not self.vendors_table.isColumnHidden(name_col_model_idx):
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        else: 
             # Fallback: if ID is hidden (col 0), then Code (model col 1 -> vis col 0), Name (model col 2 -> vis col 1)
             # Stretch the second visible column which is typically Name.
             if self.table_model.columnCount() > 2 and self.vendors_table.isColumnHidden(0):
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
             elif self.table_model.columnCount() > 1: # If ID is not hidden or not present
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


        self.main_layout.addWidget(self.vendors_table)
        self.setLayout(self.main_layout)

        if self.vendors_table.selectionModel():
            self.vendors_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Vendor Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Vendor", self)
        self.toolbar_add_action.triggered.connect(self._on_add_vendor)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Vendor", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_vendor)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self) # Icon might need specific "activate" variant too
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_vendors()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_vendors()) # Trigger load with cleared filters

    @Slot()
    def _update_action_states(self):
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_vendors(self):
        if not self.app_core.vendor_manager:
            self.app_core.logger.error("VendorManager not available in VendorsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Vendor Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            
            result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(
                active_only=active_only, 
                search_term=search_term,
                page=1, 
                page_size=200 # Load a reasonable number for MVP table, pagination UI later
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load vendors: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading vendors: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            vendor_summaries: List[VendorSummaryData] = [VendorSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(vendor_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse vendor data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid vendor data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_vendor(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a vendor.")
            return
        
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()

    def _get_selected_vendor_id(self) -> Optional[int]:
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        if not selected_rows: # No message if simply no selection for state update
            return None
        if len(selected_rows) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single vendor for this action.")
            return None
        return self.table_model.get_vendor_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_vendor(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            # Message only if action was explicitly triggered and no single item was selected
            if self.sender() == self.toolbar_edit_action : # type: ignore
                 QMessageBox.information(self, "Selection", "Please select a single vendor to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a vendor.")
            return
            
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_view_vendor_double_click(self, index: QModelIndex): # Renamed for clarity
        if not index.isValid(): return
        vendor_id = self.table_model.get_vendor_id_at_row(index.row())
        if vendor_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to view/edit vendor.")
            return
        # For MVP, double-click opens for edit. Can be changed to view-only later.
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single vendor to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change vendor status.")
            return
            
        vendor_status_active = self.table_model.get_vendor_status_at_row(self.vendors_table.currentIndex().row())
        action_verb = "deactivate" if vendor_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this vendor?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.vendor_manager.toggle_vendor_active_status(vendor_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None) # Handle scheduling failure

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule vendor status toggle."); return
        try:
            result: Result[Vendor] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Vendor {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_vendors()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle vendor status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for vendor: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/dashboard/__init__.py
```py
# File: app/ui/dashboard/__init__.py
# (Content as previously generated)
from .dashboard_widget import DashboardWidget

__all__ = ["DashboardWidget"]

```

# app/ui/dashboard/dashboard_widget.py
```py
# File: app/ui/dashboard/dashboard_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore 

class DashboardWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None): 
        super().__init__(parent)
        self.app_core = app_core
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Dashboard Widget Content (Financial Snapshots, KPIs - To be implemented)")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

```

