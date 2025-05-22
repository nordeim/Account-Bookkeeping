# File: app/ui/reports/reports_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Financial Reports Widget (To be implemented with report selection and viewing)")
        self.setLayout(self.layout)
