# app/ui/sales_invoices/__init__.py
from .sales_invoice_table_model import SalesInvoiceTableModel
from .sales_invoice_dialog import SalesInvoiceDialog
from .sales_invoices_widget import SalesInvoicesWidget # New import

__all__ = [
    "SalesInvoiceTableModel",
    "SalesInvoiceDialog",
    "SalesInvoicesWidget", # Added to __all__
]

