**Phase 4 Testing and Verification for Product/Service Module**

This involves manually testing the entire Product/Service Management workflow:
*   Navigating to the "Products & Services" tab.
*   Verifying the (initially empty) list loads.
*   Using the "Add Product/Service" action:
    *   Testing the `ProductDialog` opens.
    *   Testing population of Account and Tax Code combo boxes.
    *   Testing dynamic UI changes based on "Product Type" (e.g., inventory fields enabled/disabled).
    *   Entering data for different product types (Inventory, Service, Non-Inventory) and testing validation (e.g., inventory account required for Inventory type).
    *   Saving new products/services.
*   Verifying new items appear in the `ProductsWidget` table.
*   Testing filter functionality:
    *   Search by code, name, description.
    *   Filter by Product Type.
    *   Filter by "Show Inactive".
    *   "Clear Filters" button.
*   Using the "Edit Product/Service" action:
    *   Selecting an item and launching `ProductDialog`.
    *   Verifying fields are pre-populated correctly.
    *   Modifying data (including changing product type and seeing UI adapt) and saving.
*   Verifying changes are reflected in the table.
*   Using the "Toggle Active Status" action.
*   Checking data persistence in the `business.products` table in PostgreSQL.
*   Checking audit logs for product creation/updates.

