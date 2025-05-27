# app/ui/products/products_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.products.product_table_model import ProductTableModel 
from app.ui.products.product_dialog import ProductDialog 
from app.utils.pydantic_models import ProductSummaryData 
from app.common.enums import ProductTypeEnum 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.product import Product 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class ProductsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for ProductsWidget.")
        except ImportError:
            self.app_core.logger.info("ProductsWidget: Compiled Qt resources not found. Using direct file paths.")
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_products()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Code, Name, Description...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.search_edit)

        filter_layout.addWidget(QLabel("Type:"))
        self.product_type_filter_combo = QComboBox()
        self.product_type_filter_combo.addItem("All Types", None) 
        for pt_enum in ProductTypeEnum:
            self.product_type_filter_combo.addItem(pt_enum.value, pt_enum) 
        self.product_type_filter_combo.currentIndexChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.product_type_filter_combo)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"),"Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        self.products_table = QTableView()
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(False)
        self.products_table.doubleClicked.connect(self._on_edit_product_double_click) 
        self.products_table.setSortingEnabled(True)

        self.table_model = ProductTableModel()
        self.products_table.setModel(self.table_model)
        
        header = self.products_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.products_table.setColumnHidden(id_col_idx, True)
        
        name_col_idx = self.table_model._headers.index("Name") if "Name" in self.table_model._headers else -1
        if name_col_idx != -1:
            visible_name_idx = name_col_idx
            if id_col_idx != -1 and id_col_idx < name_col_idx and self.products_table.isColumnHidden(id_col_idx): # Check if ID column is actually hidden
                visible_name_idx -=1
            
            # Check if the model column corresponding to name_col_idx is not hidden before stretching
            if not self.products_table.isColumnHidden(name_col_idx): # Use model index for isColumnHidden
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 2 : 
            # Fallback: if ID (model index 0) is hidden, stretch second visible column (model index 2 -> visible 1)
            # This assumes "Code" is model index 1 (visible 0) and "Name" is model index 2 (visible 1)
            # If headers are ["ID", "Code", "Name", ...], and ID is hidden, visible Name is index 1.
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.products_table)
        self.setLayout(self.main_layout)

        if self.products_table.selectionModel():
            self.products_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Product/Service Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Product/Service", self)
        self.toolbar_add_action.triggered.connect(self._on_add_product)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Product/Service", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_product)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_products()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.product_type_filter_combo.setCurrentIndex(0) 
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_products())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_products(self):
        if not self.app_core.product_manager:
            self.app_core.logger.error("ProductManager not available in ProductsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Product Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            product_type_enum_filter: Optional[ProductTypeEnum] = self.product_type_filter_combo.currentData()
            
            result: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(
                active_only=active_only, 
                product_type_filter=product_type_enum_filter,
                search_term=search_term,
                page=1, 
                page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load products/services: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading products/services: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            product_summaries: List[ProductSummaryData] = [ProductSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(product_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse product/service data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid product/service data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_product(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a product/service.")
            return
        
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    def _get_selected_product_id(self) -> Optional[int]:
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None
        return self.table_model.get_product_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_product(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a product/service.")
            return
            
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_edit_product_double_click(self, index: QModelIndex): 
        if not index.isValid(): return
        product_id = self.table_model.get_product_id_at_row(index.row())
        if product_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit product/service.")
            return
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change product/service status.")
            return
            
        current_row = self.products_table.currentIndex().row()
        if current_row < 0: # Should not happen if product_id is not None
            return

        product_status_active = self.table_model.get_product_status_at_row(current_row)
        action_verb = "deactivate" if product_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this product/service?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.product_manager.toggle_product_active_status(product_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule product/service status toggle."); return
        try:
            result: Result[Product] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Product/Service {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_products()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle product/service status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for product/service: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

