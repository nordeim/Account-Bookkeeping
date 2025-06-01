# File: app/ui/banking/banking_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSplitter
from PySide6.QtCore import Qt # Added Qt for orientation
from app.core.application_core import ApplicationCore
from app.ui.banking.bank_accounts_widget import BankAccountsWidget 
from app.ui.banking.bank_transactions_widget import BankTransactionsWidget # New Import

class BankingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5,5,5,5) # Add some margins back for overall widget

        self.splitter = QSplitter(Qt.Orientation.Horizontal) # Use Horizontal splitter

        self.bank_accounts_widget = BankAccountsWidget(self.app_core, self)
        self.bank_transactions_widget = BankTransactionsWidget(self.app_core, self)

        self.splitter.addWidget(self.bank_accounts_widget)
        self.splitter.addWidget(self.bank_transactions_widget)
        
        # Set initial sizes for the splitter panes (e.g., 1/3 for accounts, 2/3 for transactions)
        # These are just suggestions, can be adjusted by user.
        initial_accounts_width = self.width() // 3 if self.width() > 0 else 300
        self.splitter.setSizes([initial_accounts_width, self.width() - initial_accounts_width if self.width() > 0 else 600])
        
        self.main_layout.addWidget(self.splitter)
        
        # Connect signals for master-detail view
        self.bank_accounts_widget.bank_account_selected.connect(
            self.bank_transactions_widget.set_current_bank_account
        )
        self.bank_accounts_widget.selection_cleared.connect(
            lambda: self.bank_transactions_widget.set_current_bank_account(None, "N/A (No bank account selected)")
        )
        
        self.setLayout(self.main_layout)
