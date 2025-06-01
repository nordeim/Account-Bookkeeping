# File: app/ui/banking/banking_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore
from app.ui.banking.bank_accounts_widget import BankAccountsWidget # New import

class BankingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0) # Use full space

        # Replace stub label with BankAccountsWidget
        self.bank_accounts_view = BankAccountsWidget(self.app_core, self)
        self.main_layout.addWidget(self.bank_accounts_view)
        
        # If planning for more tabs within Banking (e.g., Transactions, Reconciliation)
        # you would use a QTabWidget here:
        # self.banking_tab_widget = QTabWidget()
        # self.bank_accounts_view = BankAccountsWidget(self.app_core, self)
        # self.banking_tab_widget.addTab(self.bank_accounts_view, "Bank Accounts")
        # self.main_layout.addWidget(self.banking_tab_widget)

        self.setLayout(self.main_layout)
