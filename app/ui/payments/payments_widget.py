# File: app/ui/payments/payments_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.payments.payment_table_model import PaymentTableModel
from app.ui.payments.payment_dialog import PaymentDialog
from app.utils.pydantic_models import PaymentSummaryData, CustomerSummaryData, VendorSummaryData
from app.common.enums import PaymentStatusEnum, PaymentEntityTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class PaymentsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._customers_cache_for_filter: List[Dict[str, Any]] = []
        self._vendors_cache_for_filter: List[Dict[str, Any]] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_filter_combos()))
        QTimer.singleShot(100, lambda: self.apply_filter_button.click()) # Initial load

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addLayout(self.filter_layout_main) 

        self.payments_table = QTableView()
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.payments_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # self.payments_table.doubleClicked.connect(self._on_view_payment_double_click) # For future view
        self.payments_table.setSortingEnabled(True)

        self.table_model = PaymentTableModel()
        self.payments_table.setModel(self.table_model)
        
        header = self.payments_table.horizontalHeader()
        # Adjust column widths - example
        if "ID" in self.table_model._headers:
            self.payments_table.setColumnHidden(self.table_model._headers.index("ID"), True)
        if "Payment No" in self.table_model._headers:
            header.setSectionResizeMode(self.table_model._headers.index("Payment No"), QHeaderView.ResizeMode.ResizeToContents)
        if "Entity Name" in self.table_model._headers:
             header.setSectionResizeMode(self.table_model._headers.index("Entity Name"), QHeaderView.ResizeMode.Stretch)
        if "Amount" in self.table_model._headers:
             header.setSectionResizeMode(self.table_model._headers.index("Amount"), QHeaderView.ResizeMode.ResizeToContents)

        self.main_layout.addWidget(self.payments_table)
        self.setLayout(self.main_layout)

        if self.payments_table.selectionModel():
            self.payments_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Payments Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_payment_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Payment/Receipt", self)
        self.toolbar_add_payment_action.triggered.connect(self._on_add_payment)
        self.toolbar.addAction(self.toolbar_add_payment_action)

        # Add View, Void actions later
        # self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Payment", self)
        # self.toolbar_view_action.triggered.connect(self._on_view_payment)
        # self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_payments()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout_main = QHBoxLayout()
        
        self.filter_layout_main.addWidget(QLabel("Entity Type:"))
        self.entity_type_filter_combo = QComboBox()
        self.entity_type_filter_combo.addItem("All Entities", None)
        self.entity_type_filter_combo.addItem(PaymentEntityTypeEnum.CUSTOMER.value, PaymentEntityTypeEnum.CUSTOMER)
        self.entity_type_filter_combo.addItem(PaymentEntityTypeEnum.VENDOR.value, PaymentEntityTypeEnum.VENDOR)
        self.entity_type_filter_combo.currentIndexChanged.connect(self._on_entity_type_filter_changed)
        self.filter_layout_main.addWidget(self.entity_type_filter_combo)

        self.entity_filter_label = QLabel("Entity:")
        self.filter_layout_main.addWidget(self.entity_filter_label)
        self.entity_filter_combo = QComboBox(); self.entity_filter_combo.setMinimumWidth(180)
        self.entity_filter_combo.addItem("All", 0)
        self.entity_filter_combo.setEditable(True)
        entity_completer = QCompleter(self); entity_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        entity_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.entity_filter_combo.setCompleter(entity_completer)
        self.filter_layout_main.addWidget(self.entity_filter_combo)

        self.filter_layout_main.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses", None) 
        for status_enum in PaymentStatusEnum: self.status_filter_combo.addItem(status_enum.value, status_enum)
        self.filter_layout_main.addWidget(self.status_filter_combo)

        self.filter_layout_main.addWidget(QLabel("From:"))
        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout_main.addWidget(self.start_date_filter_edit)

        self.filter_layout_main.addWidget(QLabel("To:"))
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout_main.addWidget(self.end_date_filter_edit)

        self.apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply")
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_payments()))
        self.filter_layout_main.addWidget(self.apply_filter_button)
        
        self.clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        self.filter_layout_main.addWidget(self.clear_filter_button)
        self.filter_layout_main.addStretch()

    async def _load_filter_combos(self):
        # Load customers and vendors for the entity filter combo
        if self.app_core.customer_manager:
            cust_res = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1)
            if cust_res.is_success and cust_res.value:
                self._customers_cache_for_filter = [c.model_dump() for c in cust_result.value] if cust_result.is_success and cust_result.value else []
        if self.app_core.vendor_manager:
            vend_res = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1)
            if vend_res.is_success and vend_res.value:
                self._vendors_cache_for_filter = [v.model_dump() for v in vend_result.value] if vend_result.is_success and vend_result.value else []
        
        # Initial population based on "All Entities"
        self._on_entity_type_filter_changed()


    @Slot()
    def _on_entity_type_filter_changed(self):
        self.entity_filter_combo.clear()
        self.entity_filter_combo.addItem("All", 0)
        entity_type_enum = self.entity_type_filter_combo.currentData()
        
        cache_to_use: List[Dict[str, Any]] = []
        code_field = "customer_code"

        if entity_type_enum == PaymentEntityTypeEnum.CUSTOMER:
            cache_to_use = self._customers_cache_for_filter
            code_field = "customer_code"
            self.entity_filter_label.setText("Customer:")
        elif entity_type_enum == PaymentEntityTypeEnum.VENDOR:
            cache_to_use = self._vendors_cache_for_filter
            code_field = "vendor_code"
            self.entity_filter_label.setText("Vendor:")
        else: # All Entities
            self.entity_filter_label.setText("Entity:")
            # Optionally, could add all customers then all vendors to the list
            # For now, if "All Entities" is selected, the entity_filter_combo can remain "All"
            # and the manager will not filter by specific entity_id.
            pass
        
        for entity in cache_to_use:
            self.entity_filter_combo.addItem(f"{entity.get(code_field, '')} - {entity.get('name', '')}", entity.get('id'))
        
        if isinstance(self.entity_filter_combo.completer(), QCompleter):
            self.entity_filter_combo.completer().setModel(self.entity_filter_combo.model())
        
        # Trigger a refresh if entity type changes
        self.toolbar_refresh_action.trigger()


    @Slot()
    def _clear_filters_and_load(self):
        self.entity_type_filter_combo.setCurrentIndex(0) 
        # _on_entity_type_filter_changed will clear entity_filter_combo and trigger refresh
        self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        # schedule_task_from_qt(self._load_payments()) # Already triggered by combo changes

    @Slot()
    def _update_action_states(self):
        # For now, only Add action is primary. View/Void can be added later.
        self.toolbar_add_payment_action.setEnabled(True) 

    async def _load_payments(self):
        if not self.app_core.payment_manager:
            self.app_core.logger.error("PaymentManager not available."); return
        try:
            entity_type_filter = self.entity_type_filter_combo.currentData()
            entity_id_filter_data = self.entity_filter_combo.currentData()
            entity_id_filter = int(entity_id_filter_data) if entity_id_filter_data and entity_id_filter_data != 0 else None
            
            status_filter = self.status_filter_combo.currentData()
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()

            result: Result[List[PaymentSummaryData]] = await self.app_core.payment_manager.get_payments_for_listing(
                entity_type=entity_type_filter, entity_id=entity_id_filter,
                status=status_filter, start_date=start_date, end_date=end_date,
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump(mode='json') for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load payments: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading payments: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            summaries = [PaymentSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate payment data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_payment(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        # Determine if a specific entity type or entity is pre-selected from filters
        preselected_entity_type = self.entity_type_filter_combo.currentData()
        preselected_entity_id = self.entity_filter_combo.currentData()
        if preselected_entity_id == 0: preselected_entity_id = None # Treat "All" as no preselection

        dialog = PaymentDialog(self.app_core, self.app_core.current_user.id, 
                               # Pass preselected_entity_type and _id to dialog if needed for defaulting
                               # For now, PaymentDialog manages its own entity selection.
                               parent=self)
        dialog.payment_saved.connect(lambda _id: schedule_task_from_qt(self._load_payments()))
        dialog.exec()
