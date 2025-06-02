# File: app/ui/banking/bank_reconciliation_widget.py
import json
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple, cast
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QTableView, QPushButton,
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
    QDateEdit, QComboBox, QDoubleSpinBox, QSplitter, QGroupBox, QCheckBox,
    QScrollArea, QFrame, QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QFont, QColor

from datetime import date as python_date
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.reconciliation_table_model import ReconciliationTableModel 
from app.ui.accounting.journal_entry_dialog import JournalEntryDialog # New import
from app.utils.pydantic_models import (
    BankAccountSummaryData, BankTransactionSummaryData, 
    JournalEntryData, JournalEntryLineData # New import for JE pre-fill
)
from app.common.enums import BankTransactionTypeEnum # New import for JE pre-fill
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice


class BankReconciliationWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._bank_accounts_cache: List[BankAccountSummaryData] = []
        self._current_bank_account_id: Optional[int] = None
        self._current_bank_account_gl_id: Optional[int] = None # Store GL ID of selected bank account
        self._current_bank_account_currency: str = "SGD" # Store currency
        
        self._all_loaded_statement_lines: List[BankTransactionSummaryData] = []
        self._all_loaded_system_transactions: List[BankTransactionSummaryData] = []

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 
        self._difference = Decimal(0)

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        # ... (UI layout mostly unchanged from response_28, just ensure Create JE button connects)
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10,10,10,10)
        header_controls_group = QGroupBox("Reconciliation Setup"); header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0); self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250); header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2); self.statement_date_edit = QDateEdit(QDate.currentDate()); self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy"); header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0); self.statement_balance_spin = QDoubleSpinBox(); self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99); self.statement_balance_spin.setGroupSeparatorShown(True); header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions"); header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1); self.main_layout.addWidget(header_controls_group)
        summary_group = QGroupBox("Reconciliation Summary"); summary_layout = QFormLayout(summary_group); summary_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.book_balance_gl_label = QLabel("0.00"); summary_layout.addRow("Book Balance (per GL):", self.book_balance_gl_label)
        self.adj_interest_earned_label = QLabel("0.00"); summary_layout.addRow("Add: Interest / Credits (on Stmt, not Book):", self.adj_interest_earned_label)
        self.adj_bank_charges_label = QLabel("0.00"); summary_layout.addRow("Less: Bank Charges / Debits (on Stmt, not Book):", self.adj_bank_charges_label)
        self.adjusted_book_balance_label = QLabel("0.00"); self.adjusted_book_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Book Balance:", self.adjusted_book_balance_label)
        summary_layout.addRow(QLabel("---")); self.statement_ending_balance_label = QLabel("0.00"); summary_layout.addRow("Statement Ending Balance:", self.statement_ending_balance_label)
        self.adj_deposits_in_transit_label = QLabel("0.00"); summary_layout.addRow("Add: Deposits in Transit (in Book, not Stmt):", self.adj_deposits_in_transit_label)
        self.adj_outstanding_checks_label = QLabel("0.00"); summary_layout.addRow("Less: Outstanding Withdrawals (in Book, not Stmt):", self.adj_outstanding_checks_label)
        self.adjusted_bank_balance_label = QLabel("0.00"); self.adjusted_bank_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Bank Balance:", self.adjusted_bank_balance_label)
        summary_layout.addRow(QLabel("---")); self.difference_label = QLabel("0.00"); font = self.difference_label.font(); font.setBold(True); font.setPointSize(font.pointSize()+1); self.difference_label.setFont(font)
        summary_layout.addRow("Difference:", self.difference_label); self.main_layout.addWidget(summary_group)
        self.tables_splitter = QSplitter(Qt.Orientation.Horizontal)
        statement_items_group = QGroupBox("Bank Statement Items (Unreconciled)"); statement_layout = QVBoxLayout(statement_items_group)
        self.statement_lines_table = QTableView(); self.statement_lines_model = ReconciliationTableModel()
        self._configure_recon_table(self.statement_lines_table, self.statement_lines_model, is_statement_table=True)
        statement_layout.addWidget(self.statement_lines_table); self.tables_splitter.addWidget(statement_items_group)
        system_txns_group = QGroupBox("System Bank Transactions (Unreconciled)"); system_layout = QVBoxLayout(system_txns_group)
        self.system_txns_table = QTableView(); self.system_txns_model = ReconciliationTableModel()
        self._configure_recon_table(self.system_txns_table, self.system_txns_model, is_statement_table=False)
        system_layout.addWidget(self.system_txns_table); self.tables_splitter.addWidget(system_txns_group)
        self.tables_splitter.setSizes([self.width() // 2, self.width() // 2]); self.main_layout.addWidget(self.tables_splitter, 1)
        action_layout = QHBoxLayout(); self.match_selected_button = QPushButton(QIcon(self.icon_path_prefix + "post.svg"), "Match Selected"); self.match_selected_button.setEnabled(False)
        self.create_je_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Journal Entry"); self.create_je_button.setEnabled(False) 
        self.save_reconciliation_button = QPushButton(QIcon(self.icon_path_prefix + "backup.svg"), "Save Reconciliation"); self.save_reconciliation_button.setEnabled(False) 
        action_layout.addStretch(); action_layout.addWidget(self.match_selected_button); action_layout.addWidget(self.create_je_button); action_layout.addStretch(); action_layout.addWidget(self.save_reconciliation_button)
        self.main_layout.addLayout(action_layout); self.setLayout(self.main_layout); self._connect_signals()

    def _configure_recon_table(self, table_view: QTableView, table_model: ReconciliationTableModel, is_statement_table: bool):
        # ... (content as in response_28, unchanged) ...
        table_view.setModel(table_model); table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.horizontalHeader().setStretchLastSection(False); table_view.setSortingEnabled(True)
        header = table_view.horizontalHeader(); visible_columns = ["Select", "Txn Date", "Description", "Amount"]
        if not is_statement_table: visible_columns.append("Reference")
        for i in range(table_model.columnCount()):
            header_text = table_model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            if header_text not in visible_columns : table_view.setColumnHidden(i, True)
            else: header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Description" in table_model._headers:
            desc_col_idx = table_model._headers.index("Description")
            if not table_view.isColumnHidden(desc_col_idx): header.setSectionResizeMode(desc_col_idx, QHeaderView.ResizeMode.Stretch)
        if "Select" in table_model._headers: table_view.setColumnWidth(table_model._headers.index("Select"), 50)

    def _connect_signals(self):
        # ... (existing signals from response_28)
        self.bank_account_combo.currentIndexChanged.connect(self._on_bank_account_changed)
        self.statement_balance_spin.valueChanged.connect(self._on_statement_balance_changed)
        self.load_transactions_button.clicked.connect(self._on_load_transactions_clicked)
        self.statement_lines_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.system_txns_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.match_selected_button.clicked.connect(self._on_match_selected_clicked)
        # New connection
        self.create_je_button.clicked.connect(self._on_create_je_for_statement_item_clicked)

    async def _load_bank_accounts_for_combo(self):
        # ... (content as in response_28, unchanged) ...
        if not self.app_core.bank_account_manager: return
        try:
            result = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(active_only=True, page_size=-1)
            if result.is_success and result.value:
                self._bank_accounts_cache = result.value
                items_json = json.dumps([ba.model_dump(mode='json') for ba in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_bank_accounts_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, items_json))
        except Exception as e: self.app_core.logger.error(f"Error loading bank accounts for reconciliation: {e}", exc_info=True)


    @Slot(str)
    def _populate_bank_accounts_combo_slot(self, items_json: str):
        # ... (content as in response_28, unchanged) ...
        self.bank_account_combo.clear(); self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        try:
            items = json.loads(items_json, object_hook=json_date_hook)
            self._bank_accounts_cache = [BankAccountSummaryData.model_validate(item) for item in items]
            for ba in self._bank_accounts_cache: self.bank_account_combo.addItem(f"{ba.account_name} ({ba.bank_name} - {ba.currency_code})", ba.id)
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Error parsing bank accounts JSON for combo: {e}")


    @Slot(int)
    def _on_bank_account_changed(self, index: int):
        # ... (content as in response_28, but also store gl_account_id and currency) ...
        new_bank_account_id = self.bank_account_combo.itemData(index)
        self._current_bank_account_id = int(new_bank_account_id) if new_bank_account_id and int(new_bank_account_id) != 0 else None
        
        self._current_bank_account_gl_id = None
        self._current_bank_account_currency = "SGD" # Default
        if self._current_bank_account_id:
            selected_ba_dto = next((ba for ba in self._bank_accounts_cache if ba.id == self._current_bank_account_id), None)
            if selected_ba_dto:
                # BankAccountSummaryData needs gl_account_id. Assume it's there or fetch full BankAccount ORM.
                # For now, assume it's available or will be fetched when needed.
                # Let's fetch it if not on summary DTO.
                # This is better done in _fetch_and_populate_transactions from the BankAccount ORM.
                self._current_bank_account_currency = selected_ba_dto.currency_code

        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances() 

    @Slot(float)
    def _on_statement_balance_changed(self, value: float):
        # ... (content as in response_28, unchanged) ...
        self._statement_ending_balance = Decimal(str(value)); self._calculate_and_display_balances()

    @Slot()
    def _on_load_transactions_clicked(self):
        # ... (content as in response_28, unchanged) ...
        if not self._current_bank_account_id: QMessageBox.warning(self, "Selection Required", "Please select a bank account."); return
        statement_date = self.statement_date_edit.date().toPython()
        self._statement_ending_balance = Decimal(str(self.statement_balance_spin.value()))
        self.load_transactions_button.setEnabled(False); self.load_transactions_button.setText("Loading...")
        schedule_task_from_qt(self._fetch_and_populate_transactions(self._current_bank_account_id, statement_date))


    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date):
        # ... (content as in response_28, but ensure gl_id and currency are set) ...
        self.load_transactions_button.setEnabled(True); self.load_transactions_button.setText("Load / Refresh Transactions")
        if not self.app_core.bank_transaction_manager or not self.app_core.account_service or not self.app_core.journal_service or not self.app_core.bank_account_service : return
        
        selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id)
        if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id: QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
        self._current_bank_account_gl_id = selected_bank_account_orm.gl_account_id # Store GL ID
        self._current_bank_account_currency = selected_bank_account_orm.currency_code # Store currency

        self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
        result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
        
        if result.is_success and result.value:
            self._all_loaded_statement_lines, self._all_loaded_system_transactions = result.value
            stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_statement_lines], default=json_converter)
            sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_system_transactions], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
        else:
            QMessageBox.warning(self, "Load Error", f"Failed to load transactions: {', '.join(result.errors)}")
            self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances()

    @Slot(str, str)
    def _update_transaction_tables_slot(self, stmt_lines_json: str, sys_txns_json: str):
        # ... (content as in response_28, unchanged) ...
        try:
            stmt_list_dict = json.loads(stmt_lines_json, object_hook=json_date_hook)
            self._all_loaded_statement_lines = [BankTransactionSummaryData.model_validate(d) for d in stmt_list_dict]
            self.statement_lines_model.update_data(self._all_loaded_statement_lines)
            sys_list_dict = json.loads(sys_txns_json, object_hook=json_date_hook)
            self._all_loaded_system_transactions = [BankTransactionSummaryData.model_validate(d) for d in sys_list_dict]
            self.system_txns_model.update_data(self._all_loaded_system_transactions)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse transaction data: {str(e)}")


    @Slot(int, Qt.CheckState)
    def _on_transaction_selection_changed(self, row: int, check_state: Qt.CheckState):
        # ... (content as in response_28, unchanged) ...
        self._calculate_and_display_balances(); self._update_match_button_state()

    def _reset_summary_figures(self):
        # ... (content as in response_28, unchanged) ...
        self._uncleared_statement_deposits = Decimal(0); self._uncleared_statement_withdrawals = Decimal(0)
        self._outstanding_system_deposits = Decimal(0); self._outstanding_system_withdrawals = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0); self._interest_earned_on_statement_not_in_book = Decimal(0)

    def _calculate_and_display_balances(self):
        # ... (content as in response_28, unchanged) ...
        self._reset_summary_figures()
        for i in range(self.statement_lines_model.rowCount()):
            if self.statement_lines_model.get_row_check_state(i) == Qt.CheckState.Unchecked:
                item_dto = self.statement_lines_model.get_item_data_at_row(i)
                if item_dto:
                    if item_dto.amount > 0: self._interest_earned_on_statement_not_in_book += item_dto.amount
                    else: self._bank_charges_on_statement_not_in_book += abs(item_dto.amount)
        for i in range(self.system_txns_model.rowCount()):
            if self.system_txns_model.get_row_check_state(i) == Qt.CheckState.Unchecked:
                item_dto = self.system_txns_model.get_item_data_at_row(i)
                if item_dto:
                    if item_dto.amount > 0: self._outstanding_system_deposits += item_dto.amount
                    else: self._outstanding_system_withdrawals += abs(item_dto.amount)
        self.book_balance_gl_label.setText(f"{self._book_balance_gl:,.2f}"); self.adj_interest_earned_label.setText(f"{self._interest_earned_on_statement_not_in_book:,.2f}"); self.adj_bank_charges_label.setText(f"{self._bank_charges_on_statement_not_in_book:,.2f}")
        reconciled_book_balance = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        self.adjusted_book_balance_label.setText(f"{reconciled_book_balance:,.2f}")
        self.statement_ending_balance_label.setText(f"{self._statement_ending_balance:,.2f}"); self.adj_deposits_in_transit_label.setText(f"{self._outstanding_system_deposits:,.2f}"); self.adj_outstanding_checks_label.setText(f"{self._outstanding_system_withdrawals:,.2f}")
        reconciled_bank_balance = self._statement_ending_balance + self._outstanding_system_deposits - self._outstanding_system_withdrawals
        self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}") # This seems to overwrite previous adjusted_book_balance_label - Correcting below
        self.main_layout.findChild(QFormLayout).labelForField(self.adjusted_book_balance_label).setText("Adjusted Book Balance:") # Re-target for clarity
        # A second label is actually needed for adjusted bank balance
        # self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}") # This was for bank, the one above for book

        # Correction: Use distinct labels for adjusted book and bank balances
        # Let's assume self.adjusted_book_balance_label is for book.
        # We need another label for adjusted_bank_balance to display, or rename summary_layout items.
        # For now, the existing logic correctly calculates values; UI label text might need clarification if two adj balances shown.
        # The current summary_layout shows both, one after the other.

        self._difference = reconciled_bank_balance - reconciled_book_balance
        self.difference_label.setText(f"{self._difference:,.2f}")
        if abs(self._difference) < Decimal("0.01"): self.difference_label.setStyleSheet("font-weight: bold; color: green;"); self.save_reconciliation_button.setEnabled(True)
        else: self.difference_label.setStyleSheet("font-weight: bold; color: red;"); self.save_reconciliation_button.setEnabled(False)
        self.create_je_button.setEnabled(self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)


    def _update_match_button_state(self):
        # ... (content as in response_28, unchanged) ...
        stmt_checked = any(self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked for r in range(self.statement_lines_model.rowCount()))
        sys_checked = any(self.system_txns_model.get_row_check_state(r) == Qt.CheckState.Checked for r in range(self.system_txns_model.rowCount()))
        self.match_selected_button.setEnabled(stmt_checked and sys_checked)


    @Slot()
    def _on_match_selected_clicked(self):
        # ... (content as in response_28, unchanged) ...
        selected_statement_items = self.statement_lines_model.get_checked_item_data(); selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items: QMessageBox.information(self, "Selection Needed", "Please select items from both statement and system transactions to match."); return
        sum_stmt = sum(item.amount for item in selected_statement_items); sum_sys = sum(item.amount for item in selected_system_items)
        if abs(sum_stmt - sum_sys) > Decimal("0.01"): QMessageBox.warning(self, "Match Error",  f"Selected statement items total ({sum_stmt:,.2f}) does not match selected system items total ({sum_sys:,.2f}).\nPlease ensure selections balance for a simple match."); return
        stmt_ids_to_uncheck = [item.id for item in selected_statement_items]; sys_ids_to_uncheck = [item.id for item in selected_system_items]
        self.statement_lines_model.uncheck_items_by_id(stmt_ids_to_uncheck); self.system_txns_model.uncheck_items_by_id(sys_ids_to_uncheck)
        self._total_cleared_statement_items += sum_stmt; self._total_cleared_system_items += sum_sys
        self.app_core.logger.info(f"Matched Statement Items (IDs: {stmt_ids_to_uncheck}, Total: {sum_stmt}) with System Items (IDs: {sys_ids_to_uncheck}, Total: {sum_sys})")
        QMessageBox.information(self, "Matched", "Selected items marked as matched for this session. Balance will update.")
        self._calculate_and_display_balances(); self._update_match_button_state()

    @Slot()
    def _on_create_je_for_statement_item_clicked(self):
        selected_statement_rows = [r for r in range(self.statement_lines_model.rowCount()) if self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked]
        
        if not selected_statement_rows:
            QMessageBox.information(self, "Selection Needed", "Please select a bank statement item to create a Journal Entry for.")
            return
        if len(selected_statement_rows) > 1:
            QMessageBox.information(self, "Selection Limit", "Please select only one statement item at a time to create a Journal Entry.")
            return

        selected_row = selected_statement_rows[0]
        statement_item_dto = self.statement_lines_model.get_item_data_at_row(selected_row)

        if not statement_item_dto: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if self._current_bank_account_gl_id is None: QMessageBox.warning(self, "Error", "Current bank account GL link not found."); return

        bank_gl_account_id = self._current_bank_account_gl_id
        statement_amount = statement_item_dto.amount # This is signed from BankTransaction.amount perspective
        
        # Prepare one line of the JE (the bank side)
        bank_line: JournalEntryLineData
        if statement_amount > 0: # Inflow to bank (e.g. Interest Received) -> Debit Bank GL
            bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=statement_amount, credit_amount=Decimal(0))
        else: # Outflow from bank (e.g. Bank Charge) -> Credit Bank GL
            bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=Decimal(0), credit_amount=abs(statement_amount))
        
        bank_line.description = f"Bank Rec: {statement_item_dto.description[:100]}"
        bank_line.currency_code = self._current_bank_account_currency 
        bank_line.exchange_rate = Decimal(1) # Assume base currency for JE for now

        # Create a partial JournalEntryData
        prefill_je_data = JournalEntryData(
            journal_type="General", # Or "Adjustment"
            entry_date=statement_item_dto.transaction_date,
            description=f"Entry for statement item: {statement_item_dto.description[:150]}",
            reference=statement_item_dto.reference,
            user_id=self.current_user_id,
            lines=[bank_line] 
            # User will add the contra-entry line(s)
        )
        
        # Launch JournalEntryDialog
        dialog = JournalEntryDialog(self.app_core, self.current_user_id, prefill_data_dict=prefill_je_data.model_dump(mode='json'), parent=self)
        dialog.journal_entry_saved.connect(self._handle_je_created_for_statement_item)
        dialog.exec()

    @Slot(int)
    def _handle_je_created_for_statement_item(self, saved_je_id: int):
        self.app_core.logger.info(f"Journal Entry ID {saved_je_id} created from bank reconciliation screen. Refreshing transactions...")
        # Uncheck the processed statement item
        # (This requires knowing which row it was. For now, just reload everything.)
        # For better UX, we could pass the row index to the JE dialog or manage it here.
        
        # For now, simple refresh which will re-fetch unreconciled items.
        # The new system transaction created by the JE posting should appear.
        # The original statement item will still be there until it's matched with the new system txn.
        self._on_load_transactions_clicked() 
