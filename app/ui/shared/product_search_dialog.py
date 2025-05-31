# app/ui/shared/product_search_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QTableView, QHeaderView, QAbstractItemView, QComboBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG, QModelIndex
from PySide6.QtGui import QIcon # QAction not directly used here, but good to have common imports
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.products.product_table_model import ProductTableModel # Reusing existing model
from app.utils.pydantic_models import ProductSummaryData
from app.common.enums import ProductTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice


class ProductSearchDialog(QDialog):
    product_selected = Signal(object)  # Emits a ProductSummaryData dictionary

    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.setWindowTitle("Product/Service Search")
        self.setMinimumSize(800, 500)
        self.setModal(True)

        self.icon_path_prefix = "resources/icons/"
        try:
            import app.resources_rc
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self._init_ui()
        self._connect_signals()
        
        # Initial load with default filters (all active products/services)
        QTimer.singleShot(0, self._on_search_clicked)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Filter Area
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search Term:"))
        self.search_term_edit = QLineEdit()
        self.search_term_edit.setPlaceholderText("Code, Name, Description...")
        filter_layout.addWidget(self.search_term_edit)

        filter_layout.addWidget(QLabel("Type:"))
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItem("All Types", None) # User data is None
        for pt_enum in ProductTypeEnum:
            self.product_type_combo.addItem(pt_enum.value, pt_enum) # User data is the Enum member
        filter_layout.addWidget(self.product_type_combo)
        
        self.search_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Search")
        filter_layout.addWidget(self.search_button)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Results Table
        self.results_table = QTableView()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSortingEnabled(True)

        self.table_model = ProductTableModel() # Reusing the existing model
        self.results_table.setModel(self.table_model)
        
        # Hide ID column if present in model, adjust other columns
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.results_table.setColumnHidden(id_col_idx, True)
        
        header = self.results_table.horizontalHeader()
        for i in range(self.table_model.columnCount()): # Default to contents
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Stretch "Name" column
        if "Name" in self.table_model._headers:
            name_col_model_idx = self.table_model._headers.index("Name")
            visible_name_idx = name_col_model_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_model_idx and self.results_table.isColumnHidden(self.table_model._headers.index("ID")):
                 visible_name_idx -=1
            if not self.results_table.isColumnHidden(name_col_model_idx):
                header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)


        main_layout.addWidget(self.results_table)

        # Dialog Buttons
        self.button_box = QDialogButtonBox()
        self.select_button = self.button_box.addButton("Select Product", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.select_button.setEnabled(False) # Initially disabled
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.search_button.clicked.connect(self._on_search_clicked)
        self.search_term_edit.returnPressed.connect(self._on_search_clicked)
        self.product_type_combo.currentIndexChanged.connect(self._on_search_clicked) # Auto-search on type change

        self.results_table.selectionModel().selectionChanged.connect(self._update_select_button_state)
        self.results_table.doubleClicked.connect(self._on_accept_selection)
        
        self.select_button.clicked.connect(self._on_accept_selection)
        self.button_box.rejected.connect(self.reject)

    @Slot()
    def _on_search_clicked(self):
        # Disable search button while searching to prevent multiple clicks
        self.search_button.setEnabled(False)
        schedule_task_from_qt(self._perform_search()).add_done_callback(
            lambda _: self.search_button.setEnabled(True) # Re-enable after search completes
        )

    async def _perform_search(self):
        if not self.app_core.product_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Product Manager not available."))
            return

        search_term = self.search_term_edit.text().strip() or None
        product_type_filter_enum: Optional[ProductTypeEnum] = self.product_type_combo.currentData()

        try:
            result: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(
                active_only=True,  # Search dialog should only show active products
                product_type_filter=product_type_filter_enum,
                search_term=search_term,
                page=1,
                page_size=100  # Limit results in search dialog
            )
            if result.is_success:
                products_list = result.value if result.value is not None else []
                products_json = json.dumps([p.model_dump() for p in products_list], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, products_json))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Search Error"), Q_ARG(str, f"Failed to search products:\n{', '.join(result.errors)}"))
        except Exception as e:
            self.app_core.logger.error(f"Error performing product search: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Search Error"), Q_ARG(str, f"An unexpected error occurred: {e}"))


    @Slot(str)
    def _update_table_slot(self, products_json_str: str):
        try:
            products_dict_list = json.loads(products_json_str, object_hook=json_date_hook)
            product_summaries = [ProductSummaryData.model_validate(p) for p in products_dict_list]
            self.table_model.update_data(product_summaries)
            if not product_summaries:
                QMessageBox.information(self, "Search Results", "No products found matching your criteria.")
        except Exception as e:
            self.app_core.logger.error(f"Error updating product search table: {e}", exc_info=True)
            QMessageBox.critical(self, "Display Error", f"Could not display search results: {e}")
        finally:
            self._update_select_button_state()


    @Slot()
    def _update_select_button_state(self):
        self.select_button.setEnabled(self.results_table.selectionModel().hasSelection())

    @Slot()
    def _on_accept_selection(self):
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection Needed", "Please select a product from the list.")
            return

        selected_row_index = selected_rows[0].row()
        product_id = self.table_model.get_product_id_at_row(selected_row_index)
        
        if product_id is None:
            QMessageBox.warning(self, "Selection Error", "Could not retrieve product details for selection.")
            return

        # Find the full ProductSummaryData from the model's internal data
        selected_product_summary: Optional[ProductSummaryData] = None
        if 0 <= selected_row_index < len(self.table_model._data): # Access internal data (common pattern for table models)
            selected_product_summary = self.table_model._data[selected_row_index]
        
        if selected_product_summary:
            self.product_selected.emit(selected_product_summary.model_dump(mode='json')) # Emit as dict
            self.accept()
        else:
            QMessageBox.warning(self, "Selection Error", "Selected product data could not be fully retrieved.")

    def open(self) -> int:
        # Clear previous search results when opening
        self.table_model.update_data([])
        self.search_term_edit.clear()
        self.product_type_combo.setCurrentIndex(0) # "All Types"
        # Optionally trigger a default search or wait for user interaction
        # QTimer.singleShot(0, self._on_search_clicked) # If you want to load all active initially
        return super().open()

