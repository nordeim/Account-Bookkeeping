# File: app/ui/purchase_invoices/purchase_invoices_widget.py
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
from app.ui.purchase_invoices.purchase_invoice_table_model import PurchaseInvoiceTableModel
from app.ui.purchase_invoices.purchase_invoice_dialog import PurchaseInvoiceDialog
from app.utils.pydantic_models import PurchaseInvoiceSummaryData, VendorSummaryData
from app.common.enums import InvoiceStatusEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.purchase_invoice import PurchaseInvoice

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class PurchaseInvoicesWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._vendors_cache_for_filter: List[VendorSummaryData] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for PurchaseInvoicesWidget.")
        except ImportError:
            self.app_core.logger.info("PurchaseInvoicesWidget: Compiled resources not found. Using direct file paths.")
            
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_vendors_for_filter_combo()))
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

        self.table_model = PurchaseInvoiceTableModel()
        self.invoices_table.setModel(self.table_model)
        
        header = self.invoices_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.invoices_table.setColumnHidden(id_col_idx, True)
        
        vendor_col_idx = self.table_model._headers.index("Vendor") if "Vendor" in self.table_model._headers else -1
        if vendor_col_idx != -1:
            visible_vendor_idx = vendor_col_idx
            if id_col_idx != -1 and id_col_idx < vendor_col_idx and self.invoices_table.isColumnHidden(id_col_idx):
                 visible_vendor_idx -=1
            if not self.invoices_table.isColumnHidden(vendor_col_idx):
                 header.setSectionResizeMode(visible_vendor_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 4 : 
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.invoices_table)
        self.setLayout(self.main_layout)

        if self.invoices_table.selectionModel():
            self.invoices_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Purchase Invoice Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_new_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New P.Invoice", self)
        self.toolbar_new_action.triggered.connect(self._on_new_invoice)
        self.toolbar.addAction(self.toolbar_new_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_draft_invoice)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View P.Invoice", self)
        self.toolbar_view_action.triggered.connect(self._on_view_invoice_toolbar)
        self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar_post_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post P.Invoice(s)", self)
        self.toolbar_post_action.triggered.connect(self._on_post_invoice) 
        # self.toolbar_post_action.setEnabled(False) # Now managed by _update_action_states
        self.toolbar.addAction(self.toolbar_post_action)

        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    # ... (_create_filter_area, _load_vendors_for_filter_combo, _populate_vendors_filter_slot, _clear_filters_and_load - unchanged from file set 3)
    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout() 
        self.filter_layout.addWidget(QLabel("Vendor:"))
        self.vendor_filter_combo = QComboBox(); self.vendor_filter_combo.setMinimumWidth(200)
        self.vendor_filter_combo.addItem("All Vendors", 0); self.vendor_filter_combo.setEditable(True) 
        self.vendor_filter_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        vend_completer = QCompleter(self); vend_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        vend_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.vendor_filter_combo.setCompleter(vend_completer); self.filter_layout.addWidget(self.vendor_filter_combo)
        self.filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox(); self.status_filter_combo.addItem("All Statuses", None) 
        for status_enum in InvoiceStatusEnum: self.status_filter_combo.addItem(status_enum.value, status_enum)
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
        self.filter_layout.addWidget(self.clear_filter_button); self.filter_layout.addStretch()

    async def _load_vendors_for_filter_combo(self):
        if not self.app_core.vendor_manager: return
        try:
            result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1) 
            if result.is_success and result.value:
                self._vendors_cache_for_filter = result.value
                vendors_json = json.dumps([v.model_dump() for v in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_vendors_filter_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, vendors_json))
        except Exception as e: self.app_core.logger.error(f"Error loading vendors for filter: {e}", exc_info=True)

    @Slot(str)
    def _populate_vendors_filter_slot(self, vendors_json_str: str):
        current_selection_data = self.vendor_filter_combo.currentData(); self.vendor_filter_combo.clear()
        self.vendor_filter_combo.addItem("All Vendors", 0) 
        try:
            vendors_data = json.loads(vendors_json_str)
            self._vendors_cache_for_filter = [VendorSummaryData.model_validate(v) for v in vendors_data]
            for vend_summary in self._vendors_cache_for_filter: self.vendor_filter_combo.addItem(f"{vend_summary.vendor_code} - {vend_summary.name}", vend_summary.id)
            idx = self.vendor_filter_combo.findData(current_selection_data)
            if idx != -1: self.vendor_filter_combo.setCurrentIndex(idx)
            if isinstance(self.vendor_filter_combo.completer(), QCompleter): self.vendor_filter_combo.completer().setModel(self.vendor_filter_combo.model())
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Failed to parse vendors JSON for filter: {e}")

    @Slot()
    def _clear_filters_and_load(self):
        self.vendor_filter_combo.setCurrentIndex(0); self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-3)); self.end_date_filter_edit.setDate(QDate.currentDate())
        schedule_task_from_qt(self._load_invoices())
        
    @Slot()
    def _update_action_states(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_edit_draft = False
        can_post_any_selected = False

        if single_selection:
            row = selected_rows[0].row()
            status = self.table_model.get_invoice_status_at_row(row)
            if status == InvoiceStatusEnum.DRAFT:
                can_edit_draft = True
        
        if selected_rows:
            can_post_any_selected = any(
                self.table_model.get_invoice_status_at_row(idx.row()) == InvoiceStatusEnum.DRAFT
                for idx in selected_rows
            )
            
        self.toolbar_edit_action.setEnabled(can_edit_draft)
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(can_post_any_selected) 

    async def _load_invoices(self):
        if not self.app_core.purchase_invoice_manager: self.app_core.logger.error("PurchaseInvoiceManager not available."); return
        try:
            vend_id_data = self.vendor_filter_combo.currentData()
            vendor_id_filter = int(vend_id_data) if vend_id_data and vend_id_data != 0 else None
            status_enum_data = self.status_filter_combo.currentData()
            status_filter_val: Optional[InvoiceStatusEnum] = status_enum_data if isinstance(status_enum_data, InvoiceStatusEnum) else None
            start_date_filter = self.start_date_filter_edit.date().toPython(); end_date_filter = self.end_date_filter_edit.date().toPython()
            result: Result[List[PurchaseInvoiceSummaryData]] = await self.app_core.purchase_invoice_manager.get_invoices_for_listing(
                vendor_id=vendor_id_filter, status=status_filter_val, start_date=start_date_filter, end_date=end_date_filter, page=1, page_size=200)
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load PIs: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading PIs: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            invoice_summaries: List[PurchaseInvoiceSummaryData] = [PurchaseInvoiceSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(invoice_summaries)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse/validate PI data: {e}")
        finally: self._update_action_states()

    @Slot()
    def _on_new_invoice(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_invoice_id_and_status(self) -> tuple[Optional[int], Optional[InvoiceStatusEnum]]:
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1: return None, None
        row = selected_rows[0].row()
        inv_id = self.table_model.get_invoice_id_at_row(row)
        inv_status = self.table_model.get_invoice_status_at_row(row)
        return inv_id, inv_status

    @Slot()
    def _on_edit_draft_invoice(self):
        invoice_id, status = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single PI to edit."); return
        if status != InvoiceStatusEnum.DRAFT: QMessageBox.warning(self, "Edit Error", "Only Draft PIs can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_view_invoice_toolbar(self):
        invoice_id, _ = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single PI to view."); return
        self._show_view_invoice_dialog(invoice_id)

    @Slot(QModelIndex)
    def _on_view_invoice_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        invoice_id = self.table_model.get_invoice_id_at_row(index.row())
        if invoice_id is None: return
        self._show_view_invoice_dialog(invoice_id)

    def _show_view_invoice_dialog(self, invoice_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, view_only=True, parent=self)
        dialog.exec()
        
    @Slot()
    def _on_post_invoice(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "Selection", "Please select one or more Draft PIs to post."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to post PIs."); return
        
        draft_invoice_ids_to_post: List[int] = []
        non_draft_selected_count = 0
        for index in selected_rows:
            inv_id = self.table_model.get_invoice_id_at_row(index.row())
            status = self.table_model.get_invoice_status_at_row(index.row())
            if inv_id and status == InvoiceStatusEnum.DRAFT: draft_invoice_ids_to_post.append(inv_id)
            elif inv_id: non_draft_selected_count += 1
        
        if not draft_invoice_ids_to_post: QMessageBox.information(self, "Selection", "No Draft PIs selected for posting."); return
        
        warning_message = f"\n\nNote: {non_draft_selected_count} selected PIs are not 'Draft' and will be ignored." if non_draft_selected_count > 0 else ""
        reply = QMessageBox.question(self, "Confirm Posting", 
                                     f"Are you sure you want to post {len(draft_invoice_ids_to_post)} selected draft PIs?\nThis will create JEs and change status to 'Approved'.{warning_message}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
            
        self.toolbar_post_action.setEnabled(False)
        schedule_task_from_qt(self._perform_post_invoices(draft_invoice_ids_to_post, self.app_core.current_user.id))

    async def _perform_post_invoices(self, invoice_ids: List[int], user_id: int):
        if not self.app_core.purchase_invoice_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Purchase Invoice Manager not available."))
            self._update_action_states(); return

        success_count = 0; failed_posts: List[str] = []
        for inv_id_to_post in invoice_ids:
            invoice_orm_for_no = await self.app_core.purchase_invoice_manager.get_invoice_for_dialog(inv_id_to_post)
            inv_no_str = invoice_orm_for_no.invoice_no if invoice_orm_for_no else f"ID {inv_id_to_post}"
            result: Result[PurchaseInvoice] = await self.app_core.purchase_invoice_manager.post_purchase_invoice(inv_id_to_post, user_id)
            if result.is_success: success_count += 1
            else: failed_posts.append(f"PI {inv_no_str}: {', '.join(result.errors)}")
        
        summary_message_parts = []
        if success_count > 0: summary_message_parts.append(f"{success_count} PIs posted successfully.")
        if failed_posts:
            summary_message_parts.append(f"{len(failed_posts)} PIs failed to post:")
            summary_message_parts.extend([f"  - {err}" for err in failed_posts])
        final_message = "\n".join(summary_message_parts) if summary_message_parts else "No PIs were processed."
        
        msg_box_method = QMessageBox.information
        title = "Posting Complete"
        if failed_posts and success_count == 0: msg_box_method = QMessageBox.critical; title = "Posting Failed"
        elif failed_posts: msg_box_method = QMessageBox.warning; title = "Posting Partially Successful"
        
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, final_message))
        
        schedule_task_from_qt(self._load_invoices())


    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"PurchaseInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())
