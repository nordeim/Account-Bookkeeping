# app/business_logic/__init__.py
from .customer_manager import CustomerManager
from .vendor_manager import VendorManager
from .product_manager import ProductManager # New import

__all__ = [
    "CustomerManager",
    "VendorManager",
    "ProductManager", # Added to __all__
]

