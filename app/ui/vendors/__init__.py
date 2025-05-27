# app/ui/vendors/__init__.py
from .vendors_widget import VendorsWidget # Was previously just a stub, now functional
from .vendor_dialog import VendorDialog
from .vendor_table_model import VendorTableModel

__all__ = [
    "VendorsWidget",
    "VendorDialog",
    "VendorTableModel",
]

