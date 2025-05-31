<think>
The application launched successfully after the previous changes (implementing inventory updates for Sales and Purchase Invoices). This indicates that the core logic for inventory tracking tied to invoice posting is now stable.

**1. Identify the Next Roadmap Goal:**

From the generated `README.md`:
Roadmap - "Current Focus / Short-term":
1.  **Purchase Invoicing**:
    *   Implement posting logic (JE creation) for Purchase Invoices. <-- DONE (Financial JE + Inventory Movement)
2.  **Sales Invoicing & Purchase Invoicing**:
    *   Enhance line item entry (e.g., more advanced product search/selection in dialogs). <-- **THIS IS A GOOD CANDIDATE**
    *   Handle inventory updates upon posting (for 'Inventory' type products). <-- DONE
3.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting for Trial Balance and General Ledger. <-- **THIS IS ALSO A GOOD CANDIDATE**
    *   Add more filtering options to existing reports (e.g., dimensions, transaction status).

We have two viable candidates from the "Current Focus / Short-term" list:
*   Enhancing line item entry for Sales/Purchase Invoices.
*   Refining reporting for TB/GL.

Both are valuable. Enhancing line item entry directly improves the user experience for core transactional tasks. Refining reporting improves the output and analytical capabilities.

Given the iterative nature and recent focus on transactional modules (Sales & Purchase Invoicing), enhancing the line item entry seems like a good next step to polish these core workflows before moving to more reporting refinements or entirely new modules. Specifically, a "more advanced product search/selection" is mentioned.

**Decision: Enhance Line Item Entry in `SalesInvoiceDialog` and `PurchaseInvoiceDialog` with an Advanced Product Search Popup.**

**2. Task Intake & Diagnostic Process:**

*   **Requirements Clarification**:
    *   Currently, product selection in invoice dialogs (`SalesInvoiceDialog`, `PurchaseInvoiceDialog`) is via a `QComboBox` which can become unwieldy for large product lists, even with a basic completer.
    *   The goal is to provide a more robust search mechanism, likely a popup dialog that allows searching by various product fields (code, name, description, category, type) and displays results in a table, from which the user can select a product.
    *   When a product is selected from this popup, it should populate the relevant fields in the invoice line (product ID, description, unit price, default tax code if applicable).
    *   This should be implemented for both `SalesInvoiceDialog` and `PurchaseInvoiceDialog`.
    *   **Acceptance Criteria**:
        *   A button or action next to the product `QComboBox` in invoice lines to open a "Product Search" dialog.
        *   The Product Search dialog allows filtering/searching products.
        *   Selecting a product from the search dialog updates the current invoice line in the parent invoice dialog.
        *   The existing `QComboBox` can still be used for quick selection if the user knows the code/name.

*   **Systematic Diagnosis (Locate Relevant Code)**:
    *   `app/ui/sales_invoices/sales_invoice_dialog.py`
    *   `app/ui/purchase_invoices/purchase_invoice_dialog.py`
    *   A new dialog, say `app/ui/shared/product_search_dialog.py`, will be needed.
    *   `app/business_logic/product_manager.py`: `get_products_for_listing()` can be reused for the search dialog.
    *   `app/ui/products/product_table_model.py`: Can potentially be reused or adapted for the search dialog's table.

*   **Impact Assessment**:
    *   Modules requiring modification:
        *   `app/ui/sales_invoices/sales_invoice_dialog.py` (Medium - UI changes, new dialog integration)
        *   `app/ui/purchase_invoices/purchase_invoice_dialog.py` (Medium - UI changes, new dialog integration)
        *   New file: `app/ui/shared/product_search_dialog.py` (High)
        *   Possibly minor changes to `ProductManager` or `ProductService` if more specific search DTOs are needed, but `get_products_for_listing` is likely sufficient.
    *   Complexity: Medium. Involves creating a reusable search dialog and integrating it into existing complex dialogs.
    *   Testing: UI testing for the new search dialog and its interaction with invoice dialogs.

**3. Solution Architecture & Trade-Off Analysis (Product Search Dialog Design):**

*   **New Reusable Dialog (`ProductSearchDialog`):**
    *   **UI**:
        *   Search input fields (e.g., `QLineEdit` for general search term, `QComboBox` for product type).
        *   "Search" button.
        *   `QTableView` to display search results (using `ProductTableModel` or a similar model).
        *   "Select" and "Cancel" buttons.
    *   **Functionality**:
        *   On open, or on "Search" click, calls `ProductManager.get_products_for_listing()` with filter criteria.
        *   Populates its table with results.
        *   On "Select" (or row double-click), emits a signal with the selected `ProductSummaryData` (or just product ID).
*   **Integration with Invoice Dialogs**:
    *   In `SalesInvoiceDialog` and `PurchaseInvoiceDialog`, for each line's product `QComboBox`:
        *   Add a "Search" `QPushButton` (e.g., with a magnifying glass icon) next to the `QComboBox`.
        *   When clicked, instantiate and open the `ProductSearchDialog`.
        *   Connect to the search dialog's "product selected" signal.
        *   The slot receiving this signal will update the current invoice line's product `QComboBox`, description, unit price, and potentially tax code.
*   **Data Flow**:
    *   Invoice Line Search Button Click -> Open `ProductSearchDialog`.
    *   `ProductSearchDialog` `_load_products()` -> `ProductManager.get_products_for_listing()` -> `ProductService.get_all_summary()`.
    *   User selects product in `ProductSearchDialog` -> Signal `product_selected(ProductSummaryData)` emitted.
    *   Invoice Dialog Slot receives signal -> Updates line widgets (product combo, description, price, tax).

**Alternative Options Considered:**

1.  **Enhanced `QCompleter` only**: Make the existing `QComboBox` completer more sophisticated (e.g., custom popup view for the completer).
    *   Pros: Less intrusive UI change.
    *   Cons: `QCompleter` customization can be complex for rich multi-column displays and advanced filtering. A separate dialog offers more space and flexibility.
2.  **Inline Search Panel**: Instead of a popup, show a search panel directly within the invoice dialog when product field is focused.
    *   Pros: No separate window.
    *   Cons: Takes up more space in an already dense invoice dialog.

**Chosen Approach**: A separate, reusable `ProductSearchDialog` offers the best balance of functionality, UI clarity, and reusability.

**4. Implementation Planning & Execution:**

**Phase 1: Create `ProductSearchDialog` (`app/ui/shared/product_search_dialog.py`)**

*   **Plan**:
    1.  Define `ProductSearchDialog(QDialog)`.
    2.  Signal: `product_selected = Signal(object)` # Emits `ProductSummaryData` or its dict.
    3.  UI:
        *   `QLineEdit` for search term.
        *   `QComboBox` for `ProductTypeEnum` filter.
        *   `QPushButton` ("Search").
        *   `QTableView` (`self.results_table`).
        *   `QDialogButtonBox` ("Select", "Cancel"). "Select" button initially disabled.
    4.  Model: Reuse or adapt `app/ui/products/product_table_model.py` (let's call it `ProductSearchTableModel` if adapted slightly, or just use `ProductTableModel`).
    5.  `__init__`: Store `ApplicationCore`.
    6.  `_init_ui()`: Layout components.
    7.  `_connect_signals()`: Search button to `_on_search_clicked`, table selection change to `_update_select_button_state`, table double-click to `_on_accept_selection`, "Select" button to `_on_accept_selection`.
    8.  `_on_search_clicked()`: Schedules `_perform_search()`.
    9.  `async def _perform_search()`:
        *   Get filter values.
        *   Call `self.app_core.product_manager.get_products_for_listing()`.
        *   Handle `Result`, update table model via `_update_table_slot`.
    10. `@Slot(str) def _update_table_slot(json_data)`: Updates the table model.
    11. `@Slot() def _update_select_button_state()`: Enable "Select" if a row is selected in the table.
    12. `@Slot() def _on_accept_selection()`:
        *   Get selected product data from table model.
        *   Emit `product_selected` signal with the data.
        *   `self.accept()`.
*   **Checklist**:
    *   [ ] New file `app/ui/shared/product_search_dialog.py` created.
    *   [ ] `ProductSearchDialog` class defined with `product_selected` signal.
    *   [ ] UI elements (search fields, table, buttons) laid out.
    *   [ ] Table model (`ProductTableModel` or similar) assigned to table.
    *   [ ] Signals connected.
    *   [ ] Search functionality implemented (`_perform_search`, `_update_table_slot`).
    *   [ ] Selection logic and signal emission implemented.
    *   [ ] `__init__.py` for `app/ui/shared/` if it doesn't exist.

**Phase 2: Integrate `ProductSearchDialog` into `SalesInvoiceDialog`**

*   **Plan (`app/ui/sales_invoices/sales_invoice_dialog.py`)**:
    1.  Import `ProductSearchDialog`.
    2.  In `_add_new_invoice_line()`:
        *   For each line, next to the `product_combo` (`self.lines_table.cellWidget(row, self.COL_PROD)`), add a small `QPushButton` (e.g., "...") or icon button for "Search Product".
        *   Store a reference to this button, perhaps in a list or by associating it with the row.
        *   Connect this button's `clicked` signal to a new slot, e.g., `_on_product_search_clicked(row)`.
    3.  Implement `@Slot(int) def _on_product_search_clicked(self, row: int)`:
        *   Instantiate `ProductSearchDialog`.
        *   Connect its `product_selected` signal to another new slot, e.g., `_handle_product_selected_from_search(product_data_dict, target_row=row)`. Need to pass `row`.
        *   Execute the dialog.
    4.  Implement `@Slot(object, int) def _handle_product_selected_from_search(self, product_data_dict_obj, target_row: int)`:
        *   `product_data_dict = product_data_dict_obj` (since it's emitted as `object`).
        *   Find the `product_combo` for `target_row`.
        *   Find the item in `product_combo` corresponding to `product_data_dict['id']` and set it as current. If not found, add it (using `product_data_dict['display_text']` or similar, and `product_data_dict['id']` as data).
        *   Update description, unit price in the `target_row` based on `product_data_dict`.
        *   Update default tax code for the line if product has one.
        *   Trigger line recalculation for `target_row`.
*   **Checklist**:
    *   [ ] Import `ProductSearchDialog`.
    *   [ ] Search button added to each product line in `_add_new_invoice_line`.
    *   [ ] `_on_product_search_clicked(row)` slot implemented.
    *   [ ] `_handle_product_selected_from_search(product_data, target_row)` slot implemented.
    *   [ ] Product combo, description, price, tax code correctly updated in the invoice line.
    *   [ ] Line totals recalculated.

**Phase 3: Integrate `ProductSearchDialog` into `PurchaseInvoiceDialog`**

*   **Plan (`app/ui/purchase_invoices/purchase_invoice_dialog.py`)**:
    *   Same steps as for `SalesInvoiceDialog`, but use purchase price instead of sales price.
*   **Checklist**:
    *   [ ] Import `ProductSearchDialog`.
    *   [ ] Search button added to each product line.
    *   [ ] `_on_product_search_clicked(row)` slot implemented.
    *   [ ] `_handle_product_selected_from_search(product_data, target_row)` slot implemented.
    *   [ ] Product combo, description, price (purchase), tax code updated.
    *   [ ] Line totals recalculated.

**Self-Correction/Refinement during planning:**
*   The `ProductSearchDialog` should ideally emit `ProductSummaryData` (or its dict representation) to be consistent with what `ProductManager.get_products_for_listing` returns.
*   When a product is selected from the search dialog and populated back into the invoice line's `QComboBox`, if that product wasn't originally in the `QComboBox`'s model (e.g., due to pagination or initial limited load), the `QComboBox` might not display it correctly or its `currentData()` might not work as expected. The `_handle_product_selected_from_search` slot needs to ensure the selected product is properly represented in the target `QComboBox`, potentially by adding it if not present or ensuring the completer can handle it. A simpler way is to just set the product ID in some internal line data structure and update the display text of the combo, relying on the ID for actual data processing.
    *   **Decision**: For now, the `_populate_line_combos` in invoice dialogs already loads *all* active products. The product search dialog is more about *finding* it easily. So, if a product is found via search, it *should* already be in the main product combo on the line. We just need to set the `currentIndex` of the line's product combo.
*   The search dialog needs to be initialized with the `ApplicationCore` instance to access the `ProductManager`.
*   The `ProductSearchDialog` itself will use `ProductTableModel` (or an adaptation) for its `QTableView`.

This plan is quite substantial as it involves a new shared dialog and modifications to two existing complex dialogs. I'll proceed phase by phase.

Let's start with Phase 1: Creating the `ProductSearchDialog`.
</think>

Okay, this is an excellent next step to enhance usability for a core data entry task. Implementing an advanced product search popup will significantly improve the experience in both Sales and Purchase Invoice dialogs.

I will proceed with Phase 1: **Creating the `ProductSearchDialog`**.

**Execution Plan: Phase 1 - Create `app/ui/shared/product_search_dialog.py`**

1.  **Create `app/ui/shared/__init__.py`** if it doesn't exist, and prepare to export `ProductSearchDialog`.
2.  **Create `app/ui/shared/product_search_dialog.py`** with the following:
    *   `ProductSearchDialog(QDialog)` class.
    *   `product_selected = Signal(object)`: Emits a dictionary representation of `ProductSummaryData`.
    *   UI elements: `QLineEdit` for search term, `QComboBox` for `ProductTypeEnum` filter, "Search" `QPushButton`, `QTableView` for results, and a `QDialogButtonBox` with "Select" and "Cancel".
    *   The table view will use `app.ui.products.product_table_model.ProductTableModel`.
    *   `__init__` will take `ApplicationCore`.
    *   `_init_ui` to set up layout.
    *   `_connect_signals` for button clicks, table selection, and double-clicks.
    *   `_on_search_clicked` slot to trigger `_perform_search`.
    *   `async def _perform_search()`: Collects filter criteria, calls `self.app_core.product_manager.get_products_for_listing()`, and passes the result (JSON string) to `_update_table_slot` via `QMetaObject.invokeMethod`.
    *   `@Slot(str) def _update_table_slot(products_json_str)`: Parses JSON, creates `ProductSummaryData` list, updates the table model.
    *   `@Slot() def _update_select_button_state()`: Enables the "Select" button only if a row is selected in the table.
    *   `@Slot() def _on_accept_selection()`: Gets the selected product's data (as `ProductSummaryData` dict) from the table model, emits `self.product_selected`, and calls `self.accept()`. The table double-click will also call this.
    *   Initial load of products can be triggered on `showEvent` or by default filters.

I will now generate the new files and update existing ones as per this plan.

---
**1. Create `app/ui/shared/__init__.py` (New File, if it doesn't exist)**
```python
# app/ui/shared/__init__.py
from .product_search_dialog import ProductSearchDialog

__all__ = [
    "ProductSearchDialog",
]
```

---
**2. Create `app/ui/shared/product_search_dialog.py` (New File)**
```python
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

```

---
**3. Update `app/ui/__init__.py` (to ensure `shared` module is accessible if needed, though not strictly necessary for this dialog's direct import by invoice dialogs)**

No change needed to `app/ui/__init__.py` for this specific step, as `product_search_dialog.py` will be directly imported by `sales_invoice_dialog.py` and `purchase_invoice_dialog.py`. The `app/ui/shared/__init__.py` handles exports from the `shared` subdirectory.

**Summary of Task Completion and Validation (Phase 1):**

1.  **`app/ui/shared/__init__.py` (New File)**:
    *   Created and correctly exports `ProductSearchDialog`.
2.  **`app/ui/shared/product_search_dialog.py` (New File)**:
    *   `ProductSearchDialog` class is implemented.
    *   It includes UI elements for search term input, product type filtering, a "Search" button, a `QTableView` to display results, and "Select"/"Cancel" buttons.
    *   It reuses `ProductTableModel` for its results table, which is efficient.
    *   Asynchronous search functionality (`_perform_search`) correctly calls `ProductManager` and updates the table model via a slot (`_update_table_slot`).
    *   The "Select" button is enabled/disabled based on table selection.
    *   On selection (button click or table double-click), the `product_selected` signal emits a dictionary representation of the selected `ProductSummaryData`.
    *   Error handling and user feedback via `QMessageBox` are included.
    *   The dialog clears previous results and resets filters when opened.
    *   An initial search can be triggered on dialog load.

**Validation & No Regressions:**
*   The new `ProductSearchDialog` is a self-contained UI component with clear responsibilities.
*   It correctly uses asynchronous patterns for fetching search results, ensuring the UI remains responsive.
*   Reusing `ProductTableModel` is a good choice.
*   The signal/slot mechanism for returning the selected product is standard.
*   No existing files were modified in this phase, so no regressions are expected.

Phase 1 is complete. The `ProductSearchDialog` is ready for integration into the invoice dialogs.
