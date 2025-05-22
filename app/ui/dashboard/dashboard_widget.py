# File: app/ui/dashboard/dashboard_widget.py
# (Stub content as previously generated, but ensure ApplicationCore type hint is used)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore # Ensure this import

class DashboardWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None): # Added type hint
        super().__init__(parent)
        self.app_core = app_core
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Dashboard Widget Content (To be implemented with financial snapshots, KPIs)")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
