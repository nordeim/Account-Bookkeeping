# app/ui/sales_invoices/__init__.py    
from .sales_invoice_table_model import SalesInvoiceTableModel
from .sales_invoice_dialog import SalesInvoiceDialog # Ensure this is exported
# from .sales_invoices_widget import SalesInvoicesWidget # To be added later

__all__ = [
    "SalesInvoiceTableModel",
    "SalesInvoiceDialog", # Added to __all__
    # "SalesInvoicesWidget",
]

