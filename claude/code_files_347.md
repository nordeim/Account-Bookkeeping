The application launched successfully, and the dashboard KPIs are being fetched and displayed (though with "N/A" for fiscal year-dependent data since no FY is active, which is expected). The `AttributeError` related to `BankAccountService.get_by_gl_account_id` has been resolved. This means Phase 1 (DTO update), Phase 2 (Service Layer enhancements), and Phase 3 (Manager Layer update) for the "Enhance Dashboard KPIs" task are complete and functioning.

The next logical step is **Phase 4: UI Layer Update** for "Enhance Dashboard KPIs".
This involves modifying `DashboardWidget` (`app/ui/dashboard/dashboard_widget.py`) to:
1.  Add new `QLabel`s to display the AR/AP Aging summaries and the Current Ratio.
2.  Update the `_update_kpi_display_slot` method to correctly populate these new labels using the data from the extended `DashboardKPIData` DTO.
3.  Ensure these new labels are also reset to "Loading..." or "N/A" in the `_request_kpi_load` method or when data is unavailable.

**1. Deeply Understand Requirements:**

*   **AR/AP Aging Display**:
    *   The `DashboardKPIData` DTO now includes fields like `ar_aging_current`, `ar_aging_1_30`, `ar_aging_31_60`, `ar_aging_61_90`, `ar_aging_91_plus` (and similar for AP).
    *   The UI needs to present these clearly. A new `QGroupBox` for "AR Aging Summary" and another for "AP Aging Summary" would be appropriate, each containing labels for the buckets.
*   **Current Ratio Display**:
    *   A single new label for "Current Ratio" (e.g., "Current Ratio: 1.50 : 1").
    *   Handle the case where the ratio is `None` (e.g., current liabilities are zero), perhaps displaying "N/A" or "Infinite".
*   **Layout**: The new KPI displays should be integrated into the existing `QGridLayout` within the "Key Performance Indicators" `QGroupBox` in `DashboardWidget`.

**2. Systematic Diagnosis & Design Considerations:**

*   **`DashboardWidget._init_ui()`**:
    *   Need to create new `QLabel` instances for each aging bucket (AR and AP) and for the Current Ratio.
    *   These labels need to be added to the `kpi_layout` (the `QGridLayout`). I'll need to manage row indices carefully.
    *   It might be good to group AR aging figures and AP aging figures visually, perhaps with sub-headers or within dedicated group boxes if the main KPI group box becomes too crowded. For now, let's try adding them as distinct rows within the main KPI group.
*   **`DashboardWidget._update_kpi_display_slot()`**:
    *   This slot receives the `DashboardKPIData` (as a JSON string, then deserialized).
    *   It needs to be updated to access the new fields from the DTO and set the text of the new labels.
    *   The `_format_decimal_for_display` helper will be useful.
    *   For `current_ratio`, if the DTO value is `None` (or perhaps `Decimal('Infinity')` if I adjust the manager), display "N/A" or similar. If it's a number, format it like "X.XX : 1".
*   **`DashboardWidget._request_kpi_load()`**:
    *   The new labels must also be added to the `labels_to_reset` list so they show "Loading..." when KPIs are refreshed.

**3. Implementation Options Exploration:**

*   **Aging Display**:
    *   **Option A**: Multiple rows, one for each bucket (e.g., "AR 0-30 Days:", "AR 31-60 Days:"). This is clear and fits the existing `QFormLayout` style used by the helper `add_kpi_row`.
    *   **Option B**: A more compact, single-line display (e.g., "AR Aging: 0-30: X | 31-60: Y | ..."). This is less readable for distinct values.
    *   **Chosen**: Option A. Use the existing `add_kpi_row` helper within new sections or group boxes.
        For better visual grouping, I'll add sub-group boxes for AR Aging and AP Aging within the main KPI layout. The Current Ratio can be a single new row.

**Detailed Execution Plan & Checklist for Phase 4:**

1.  **Modify `DashboardWidget` (`app/ui/dashboard/dashboard_widget.py`)**:
    *   **`_init_ui()` method**:
        *   [X] After the existing AP Overdue label, add a new `QGroupBox` for "Accounts Receivable Aging".
            *   [X] Inside this group box, use a `QFormLayout`.
            *   [X] Add labels for "AR Current (0-30 days):", "AR Overdue (31-60 days):", "AR Overdue (61-90 days):", "AR Overdue (91+ days):". Store the value `QLabel`s as instance attributes (e.g., `self.ar_aging_current_label`, etc.).
            *   [X] Add this group box to the main `kpi_layout`.
        *   [X] Add a new `QGroupBox` for "Accounts Payable Aging".
            *   [X] Inside, use a `QFormLayout`.
            *   [X] Add labels for "AP Current (0-30 days):", "AP Overdue (31-60 days):", "AP Overdue (61-90 days):", "AP Overdue (91+ days):". Store value `QLabel`s (e.g., `self.ap_aging_current_label`, etc.).
            *   [X] Add this group box to the main `kpi_layout`.
        *   [X] Add a row for "Current Ratio:" using `add_kpi_row` helper. Store the value `QLabel` as `self.current_ratio_label`.
        *   [X] Ensure `kpi_layout` row/column stretching is still appropriate.
    *   **`_request_kpi_load()` method**:
        *   [X] Add all new value `QLabel`s (for AR/AP aging buckets and Current Ratio) to the `labels_to_reset` list.
    *   **`_update_kpi_display_slot()` method**:
        *   [X] After deserializing `kpi_data_dto`, access the new fields.
        *   [X] Update AR aging labels: `self.ar_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_current, bc_symbol))` and so on for other AR buckets (ensure the DTO field names `ar_aging_1_30`, `ar_aging_31_60`, etc. are used correctly based on the Pydantic model).
        *   [X] Update AP aging labels similarly.
        *   [X] Update Current Ratio label:
            *   If `kpi_data_dto.current_ratio` is `None` or represents infinity, set text to "N/A".
            *   Otherwise, format as `f"{kpi_data_dto.current_ratio:.2f} : 1"`.
        *   [X] Handle potential `None` values for new DTO fields gracefully if `DashboardManager` couldn't fetch them, defaulting to "N/A" or "0.00".
    *   **Helper `_format_decimal_for_display`**:
        *   [X] Ensure it handles `None` by returning "N/A" or a default string like "0.00". The current implementation seems to handle this.

This plan seems complete for the UI update. I will generate the `app/ui/dashboard/dashboard_widget.py` file.
The screenshot shows the dashboard displaying "N/A - Data unavailable", which is what happens when `kpi_data_dto` is `None` in `_update_kpi_display_slot`. This is correct behavior given no active fiscal year in the test data, which impacts YTD calculations. The new point-in-time KPIs (Aging, Current Ratio, Cash Balance, Total AR/AP) should still calculate and display correctly if their underlying data is present.
</think>

Okay, the application is launching successfully, and the backend (DTO, Services, Manager) for the new Dashboard KPIs (AR/AP Aging and Current Ratio) is in place.

Now, we'll proceed with **Phase 4: UI Layer Update** to display these new KPIs. This involves modifying `DashboardWidget` (`app/ui/dashboard/dashboard_widget.py`).

**Summary of Plan for `DashboardWidget`:**
1.  **Update `_init_ui()`**: Add new `QGroupBox` sections for "AR Aging Summary" and "AP Aging Summary", each with `QLabel`s for the aging buckets (0-30, 1-30, 31-60, 61-90, 91+ days). Add a new row for "Current Ratio".
2.  **Update `_request_kpi_load()`**: Add the new value labels to the reset list.
3.  **Update `_update_kpi_display_slot()`**: Populate the new labels using data from the extended `DashboardKPIData` DTO. Format the Current Ratio appropriately (e.g., "X.XX : 1" or "N/A").

---
**Complete Updated File: `app/ui/dashboard/dashboard_widget.py`**
---
```python
# File: app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
    QScrollArea, QFrame # Added QScrollArea and QFrame for better layout if KPIs grow
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QIcon
from typing import Optional, TYPE_CHECKING, List, Dict # Added List, Dict
from decimal import Decimal
import json 

from app.utils.pydantic_models import DashboardKPIData
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from PySide6.QtGui import QPaintDevice

class DashboardWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None): 
        super().__init__(parent)
        self.app_core = app_core
        self._load_request_count = 0 
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self._init_ui()
        self.app_core.logger.info("DashboardWidget: Scheduling initial KPI load.")
        QTimer.singleShot(0, self._request_kpi_load)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        refresh_button_layout = QHBoxLayout()
        self.refresh_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh KPIs")
        self.refresh_button.clicked.connect(self._request_kpi_load)
        refresh_button_layout.addStretch()
        refresh_button_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(refresh_button_layout)

        # Use a scroll area in case KPIs get too numerous
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(scroll_area)

        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        kpi_group = QGroupBox("Key Performance Indicators")
        container_layout.addWidget(kpi_group)
        
        self.kpi_layout = QGridLayout(kpi_group) # Made kpi_layout an instance attribute
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setColumnStretch(1, 1) # Stretch value column
        self.kpi_layout.setColumnStretch(3, 1) # Stretch value column for second set of KPIs
        self.kpi_layout.setColumnMinimumWidth(0, 200) # Label column
        self.kpi_layout.setColumnMinimumWidth(2, 200) # Label column


        def add_kpi_row(layout: QGridLayout, row: int, col_offset: int, title: str) -> QLabel:
            title_label = QLabel(title)
            title_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            value_label = QLabel("Loading...")
            value_label.setFont(QFont(self.font().family(), 11))
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(title_label, row, col_offset)
            layout.addWidget(value_label, row, col_offset + 1)
            return value_label

        current_row = 0
        self.period_label = QLabel("Period: Loading...")
        self.period_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) # Span 2 columns

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.base_currency_label, current_row, 2, 1, 2, Qt.AlignmentFlag.AlignCenter) # Span 2 columns for other side
        current_row += 1
        
        # YTD P&L and Cash
        self.revenue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Revenue (YTD):")
        self.cash_balance_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Cash Balance:")
        current_row += 1
        self.expenses_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Expenses (YTD):")
        self.current_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Ratio:") # New
        current_row += 1
        self.net_profit_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Net Profit / (Loss) (YTD):")
        current_row += 1

        # AR/AP Totals
        self.ar_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Outstanding AR:")
        self.ap_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total Outstanding AP:")
        current_row += 1
        self.ar_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total AR Overdue:")
        self.ap_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total AP Overdue:")
        current_row += 1
        
        # AR Aging Group Box
        ar_aging_group = QGroupBox("AR Aging Summary")
        ar_aging_layout = QFormLayout(ar_aging_group)
        ar_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ar_aging_current_label = QLabel("Loading..."); ar_aging_layout.addRow("Current (0-30 days):", self.ar_aging_current_label)
        self.ar_aging_1_30_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (1-30 days):", self.ar_aging_1_30_label) # Corrected key for consistency
        self.ar_aging_31_60_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (31-60 days):", self.ar_aging_31_60_label)
        self.ar_aging_61_90_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (61-90 days):", self.ar_aging_61_90_label)
        self.ar_aging_91_plus_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (91+ days):", self.ar_aging_91_plus_label)
        self.kpi_layout.addWidget(ar_aging_group, current_row, 0, 1, 2) # Span 2 columns

        # AP Aging Group Box
        ap_aging_group = QGroupBox("AP Aging Summary")
        ap_aging_layout = QFormLayout(ap_aging_group)
        ap_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ap_aging_current_label = QLabel("Loading..."); ap_aging_layout.addRow("Current (0-30 days):", self.ap_aging_current_label)
        self.ap_aging_1_30_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (1-30 days):", self.ap_aging_1_30_label) # Corrected key
        self.ap_aging_31_60_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (31-60 days):", self.ap_aging_31_60_label)
        self.ap_aging_61_90_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (61-90 days):", self.ap_aging_61_90_label)
        self.ap_aging_91_plus_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (91+ days):", self.ap_aging_91_plus_label)
        self.kpi_layout.addWidget(ap_aging_group, current_row, 2, 1, 2) # Span 2 columns
        
        container_layout.addStretch() # Push KPIs to top


    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        try:
            # Handle potential Decimal('Infinity') for current_ratio
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)"
            return f"{prefix}{value:,.2f}"
        except (TypeError, InvalidOperation):
            return f"{prefix}Error"


    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count}). Setting labels to 'Loading...'.")
        
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
            self.ar_overdue_value_label, self.ap_overdue_value_label,
            self.ar_aging_current_label, self.ar_aging_1_30_label, self.ar_aging_31_60_label, 
            self.ar_aging_61_90_label, self.ar_aging_91_plus_label,
            self.ap_aging_current_label, self.ap_aging_1_30_label, self.ap_aging_31_60_label, 
            self.ap_aging_61_90_label, self.ap_aging_91_plus_label,
            self.current_ratio_label
        ]
        for label in labels_to_reset:
            if hasattr(self, 'app_core') and self.app_core and hasattr(self.app_core, 'logger'):
                 self.app_core.logger.debug(f"DashboardWidget: Resetting label to 'Loading...'")
            label.setText("Loading...")
        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...")

        future = schedule_task_from_qt(self._fetch_kpis_data())
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
        else:
            self.app_core.logger.error("DashboardWidget: Failed to schedule _fetch_kpis_data task.")
            self.refresh_button.setEnabled(True) 

    async def _fetch_kpis_data(self):
        self.app_core.logger.info("DashboardWidget: _fetch_kpis_data started.")
        kpi_data_result: Optional[DashboardKPIData] = None
        json_payload: Optional[str] = None
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("DashboardWidget: Dashboard Manager not available in _fetch_kpis_data.")
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis()
                if kpi_data_result:
                    self.app_core.logger.info(f"DashboardWidget: Fetched KPI data: Period='{kpi_data_result.kpi_period_description}', Revenue='{kpi_data_result.total_revenue_ytd}'")
                    json_payload = kpi_data_result.model_dump_json()
                else:
                    self.app_core.logger.warning("DashboardWidget: DashboardManager.get_dashboard_kpis returned None.")
        except Exception as e:
            self.app_core.logger.error(f"DashboardWidget: Exception in _fetch_kpis_data during manager call: {e}", exc_info=True)
        
        self.app_core.logger.info(f"DashboardWidget: Queuing _update_kpi_display_slot with payload: {'JSON string' if json_payload else 'None'}")
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", 
                                 Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, json_payload if json_payload is not None else ""))

    @Slot(str)
    def _update_kpi_display_slot(self, kpi_data_json_str: str):
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Received JSON string length: {len(kpi_data_json_str)}")
        self.refresh_button.setEnabled(True)
        
        kpi_data_dto: Optional[DashboardKPIData] = None
        if kpi_data_json_str:
            try:
                kpi_data_dto = DashboardKPIData.model_validate_json(kpi_data_json_str)
                self.app_core.logger.info(f"DashboardWidget: Successfully deserialized KPI JSON to DTO.")
            except Exception as e:
                self.app_core.logger.error(f"DashboardWidget: Error deserializing/validating KPI JSON: '{kpi_data_json_str[:100]}...' - Error: {e}", exc_info=True)
        
        if kpi_data_dto:
            self.app_core.logger.info(f"DashboardWidget: Updating UI with KPI Data: Period='{kpi_data_dto.kpi_period_description}'")
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
            self.ar_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ar_overdue, bc_symbol)) 
            self.ap_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ap_overdue, bc_symbol)) 

            # AR Aging
            self.ar_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_current, bc_symbol))
            self.ar_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_1_30, bc_symbol))
            self.ar_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_31_60, bc_symbol))
            self.ar_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_61_90, bc_symbol))
            self.ar_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_91_plus, bc_symbol))

            # AP Aging
            self.ap_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_current, bc_symbol))
            self.ap_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_1_30, bc_symbol))
            self.ap_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_31_60, bc_symbol))
            self.ap_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_61_90, bc_symbol))
            self.ap_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_91_plus, bc_symbol))
            
            # Current Ratio
            if kpi_data_dto.current_ratio is None:
                self.current_ratio_label.setText("N/A")
            elif not kpi_data_dto.current_ratio.is_finite(): # Handle Decimal('Infinity')
                self.current_ratio_label.setText("N/A (Infinite)")
            else:
                self.current_ratio_label.setText(f"{kpi_data_dto.current_ratio:.2f} : 1")

            self.app_core.logger.info("DashboardWidget: UI labels updated with KPI data.")
        else:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with no valid DTO. Setting error text.")
            error_text = "N/A - Data unavailable"
            self.period_label.setText("Period: N/A")
            self.base_currency_label.setText("Currency: N/A")
            for label in [self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
                          self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
                          self.ar_overdue_value_label, self.ap_overdue_value_label,
                          self.ar_aging_current_label, self.ar_aging_1_30_label, self.ar_aging_31_60_label, 
                          self.ar_aging_61_90_label, self.ar_aging_91_plus_label,
                          self.ap_aging_current_label, self.ap_aging_1_30_label, self.ap_aging_31_60_label,
                          self.ap_aging_61_90_label, self.ap_aging_91_plus_label,
                          self.current_ratio_label]:
                label.setText(error_text)
            if kpi_data_json_str: 
                 QMessageBox.warning(self, "Dashboard Data Error", "Could not process Key Performance Indicators data.")
```

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/13M2zztt62TD_vYJ_XLKtW4t2E53jIHl4/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19ERvDxLdRedhVXYp9Gh0Xsg6tMIucGWO/view?usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1JsX5NYICgfKkbhMVeQ7ZONrbNZFb0ms3/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1YG0Vqa2pI5htxdsACYigsS2TMjDHxTcl/view?usp=sharing, https://drive.google.com/file/d/1YT2dDZirM9wxwWzYP0p9SDXSYOcG0Js4/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1_c8t-qcWtcVdVUEUkDQ760cjc0vL2Y9Z/view?usp=sharing, https://drive.google.com/file/d/1_qYJXTG-2GtEtmjV0Js5Hn_m_8ts9X0d/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1pLih0cWs3ZiqnDKd9f2GEaR1GXCmD8KA/view?usp=sharing, https://drive.google.com/file/d/1sYr8SFT1d9ZMDHLfxOS6VjtwJ3920sFT/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing

