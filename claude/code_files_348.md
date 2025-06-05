<think>
The application failed to launch due to a `NameError: name 'QFormLayout' is not defined` in `app/ui/dashboard/dashboard_widget.py`.

**Error Analysis:**
The traceback clearly shows that on line 110 of `dashboard_widget.py`, I tried to use `QFormLayout` without importing it from `PySide6.QtWidgets`.
```python
# app/ui/dashboard/dashboard_widget.py, line 110
        ar_aging_layout = QFormLayout(ar_aging_group) # <--- QFormLayout not imported
```
And similarly for the AP aging group box a few lines later.

**1. Deeply Understand Requirements (Recap for Dashboard UI):**
The plan was to add new `QGroupBox` sections for AR/AP aging, and within these group boxes, use a `QFormLayout` to arrange the labels for aging buckets. This is a standard Qt layout approach.

**2. Systematic Diagnosis:**
The diagnosis is straightforward: `QFormLayout` was used without being imported in `app/ui/dashboard/dashboard_widget.py`.

**3. Implementation Options Exploration (Minor - just an import):**
The only option is to add the correct import.

**Chosen Implementation Strategy:**
Add `QFormLayout` to the imports from `PySide6.QtWidgets` in `app/ui/dashboard/dashboard_widget.py`.

**Detailed Execution Plan & Checklist:**

1.  **Modify `app/ui/dashboard/dashboard_widget.py`**:
    *   Checklist:
        *   [X] Locate the import statement from `PySide6.QtWidgets`.
        *   [X] Add `QFormLayout` to this import list.
            ```python
            from PySide6.QtWidgets import (
                QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
                QScrollArea, QFrame, QFormLayout # Add QFormLayout here
            )
            ```
    *   [X] No other changes to this file are needed for this specific error. The layout logic itself using `QFormLayout` is correct.

I will now generate the updated `app/ui/dashboard/dashboard_widget.py` file.
</think>

You are absolutely correct to demand a meticulous review. The traceback clearly indicates a `NameError: name 'QFormLayout' is not defined` in `app/ui/dashboard/dashboard_widget.py`. This happened because I used `QFormLayout` for the new AR/AP aging summary sections without importing it from `PySide6.QtWidgets`.

I will fix this by adding the necessary import. No other files are implicated by this specific error.

---
**Complete Updated File: `app/ui/dashboard/dashboard_widget.py`**
---
```python
# File: app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
    QScrollArea, QFrame, QFormLayout # Added QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QIcon
from typing import Optional, TYPE_CHECKING, List, Dict # Added List, Dict
from decimal import Decimal, InvalidOperation # Added InvalidOperation for robust parsing
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
        
        self.kpi_layout = QGridLayout(kpi_group) 
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setColumnStretch(1, 1) 
        self.kpi_layout.setColumnStretch(3, 1) 
        self.kpi_layout.setColumnMinimumWidth(0, 200) 
        self.kpi_layout.setColumnMinimumWidth(2, 200) 


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
        self.kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.base_currency_label, current_row, 2, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        current_row += 1
        
        self.revenue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Revenue (YTD):")
        self.cash_balance_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Cash Balance:")
        current_row += 1
        self.expenses_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Expenses (YTD):")
        self.current_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Ratio:") 
        current_row += 1
        self.net_profit_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Net Profit / (Loss) (YTD):")
        current_row += 1

        self.ar_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Outstanding AR:")
        self.ap_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total Outstanding AP:")
        current_row += 1
        self.ar_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total AR Overdue:")
        self.ap_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total AP Overdue:")
        current_row += 1
        
        ar_aging_group = QGroupBox("AR Aging Summary")
        ar_aging_layout = QFormLayout(ar_aging_group) # Using QFormLayout now
        ar_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ar_aging_current_label = QLabel("Loading..."); ar_aging_layout.addRow("Current (Not Overdue):", self.ar_aging_current_label)
        self.ar_aging_1_30_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (1-30 days):", self.ar_aging_1_30_label)
        self.ar_aging_31_60_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (31-60 days):", self.ar_aging_31_60_label)
        self.ar_aging_61_90_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (61-90 days):", self.ar_aging_61_90_label)
        self.ar_aging_91_plus_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (91+ days):", self.ar_aging_91_plus_label)
        self.kpi_layout.addWidget(ar_aging_group, current_row, 0, 1, 2) 

        ap_aging_group = QGroupBox("AP Aging Summary")
        ap_aging_layout = QFormLayout(ap_aging_group) # Using QFormLayout now
        ap_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ap_aging_current_label = QLabel("Loading..."); ap_aging_layout.addRow("Current (Not Overdue):", self.ap_aging_current_label)
        self.ap_aging_1_30_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (1-30 days):", self.ap_aging_1_30_label)
        self.ap_aging_31_60_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (31-60 days):", self.ap_aging_31_60_label)
        self.ap_aging_61_90_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (61-90 days):", self.ap_aging_61_90_label)
        self.ap_aging_91_plus_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (91+ days):", self.ap_aging_91_plus_label)
        self.kpi_layout.addWidget(ap_aging_group, current_row, 2, 1, 2) 
        
        container_layout.addStretch() 


    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        try:
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
            self.ar_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_1_30, bc_symbol)) # Using consistent DTO field name
            self.ar_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_31_60, bc_symbol))
            self.ar_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_61_90, bc_symbol))
            self.ar_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_91_plus, bc_symbol))

            # AP Aging
            self.ap_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_current, bc_symbol))
            self.ap_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_1_30, bc_symbol)) # Using consistent DTO field name
            self.ap_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_31_60, bc_symbol))
            self.ap_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_61_90, bc_symbol))
            self.ap_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_91_plus, bc_symbol))
            
            # Current Ratio
            if kpi_data_dto.current_ratio is None:
                self.current_ratio_label.setText("N/A")
            elif not kpi_data_dto.current_ratio.is_finite(): 
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
            if kpi_data_json_str: # Only show QMessageBox if we actually received data but failed to parse/validate
                 QMessageBox.warning(self, "Dashboard Data Error", "Could not process Key Performance Indicators data.")
```

