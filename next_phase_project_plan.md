**Current Project Status Recap (Relevant for README/TDS updates):**

*   **Purchase Invoicing**:
    *   Backend for Draft Management (`PurchaseInvoiceManager`): Logic for creating/updating draft PIs is implemented. Posting logic is a stub.
    *   `PurchaseInvoiceDialog`: Fully functional for creating/editing draft purchase invoices, including dynamic calculations and saving.
    *   `PurchaseInvoicesWidget` (List View): Not yet created.
*   **Sales Invoicing**: Fully functional (Draft CRUD, Posting with JE, List View, Dialog with "Save & Approve").
*   **User and Role Management UI**: Fully functional.
*   **Reporting**: BS/P&L on-screen display and export enhanced. TB/GL functional. Reporting options for BS/P&L (comparative, zero-balance) added.
*   All previously implemented features (Core Accounting, Customer/Vendor/Product Management, GST F5) remain stable.

The main change since the last README/TDS update (v9 of TDS) is the completion of draft management for Purchase Invoices via `PurchaseInvoiceDialog` and its backend manager.

**Plan for Updating Documentation:** 

1.  **Update `README.md`**:
    *   **Key Features Section**: 
        *   Update "Purchase Invoicing and Accounts Payable" status from "Foundational" to "UI Dialog Implemented - Draft CRUD for Purchase Invoices. List view and posting planned."
    *   **Usage Guide**: Add a brief mention that a dialog for creating/editing draft Purchase Invoices is available (though the main list view widget is not yet present in a dedicated tab).
    *   **Roadmap**:
        *   Under "Current Focus / Short-term" for "Purchase Invoicing", update from "Begin implementation" to "Complete UI for listing, viewing, and managing Purchase Invoices. Implement posting logic (JE creation)."
        
2.  **Update `Technical_Design_Specification_Document.md` (to v10.0)**: 
    *   **Version and Date**: Update to 10.0 and current date.
    *   **1.1 Purpose / 1.2 Scope / 1.4 System Overview / Current Implementation Status**: Reflect the addition of draft management for Purchase Invoices (backend logic and `PurchaseInvoiceDialog`).
    *   **2.2 Component Architecture**:
        *   `PurchaseInvoiceManager`: Detail its implemented draft management logic (`_validate_and_prepare_pi_data`, `create_draft_purchase_invoice`, `update_draft_purchase_invoice`).
        *   `UI Components (`app/ui/purchase_invoices/`)`: Detail the new `PurchaseInvoiceDialog` and its functionalities. Note that `PurchaseInvoicesWidget` is planned. 
    *   **3.3 Data Transfer Objects (DTOs)**: Confirm `PurchaseInvoice` DTOs are listed and used.
    *   **4. Module and Component Specifications**:
        *   Add/Expand section for "Purchase Invoicing Module".
        *   Detail `PurchaseInvoiceManager` methods for draft management.
    *   **5. User Interface Implementation**:
        *   Detail `PurchaseInvoiceDialog` (header fields, line item table, dynamic calculations, save draft functionality). Note its current invocation point (if any, or state it's ready for integration into a list widget).
    *   **9. Conclusion**: Reflect the new capability for managing draft purchase invoices.

This will bring both documents up to date with the latest major progress.

---
**Current Project Status Recap:**

*   **Sales Invoicing**: Fully functional for draft CRUD, posting with JE, list view, dialog with "Save & Approve".
*   **User and Role Management UI**: Fully functional.
*   **Reporting**:
    *   `ReportsWidget` UI enhanced with options for comparative periods (BS/P&L) and zero-balance accounts (BS).
    *   On-screen display for BS & P&L in `QTreeView` improved with better structure and formatting.
    *   PDF/Excel export for BS & P&L has enhanced formatting.
    *   TB & GL display/export are functional with simpler table views/exports.
*   All previously implemented features remain stable.
    
**Next Step Identification (from Roadmap):**
    
Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`. <-- DONE
    *   Enhance line item entry (e.g., better product search/selection). <-- Basic enhancement done. Advanced popup search is still an option.
    *   **(Future)** Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting and layout. <-- DONE for BS/P&L. Could extend to TB/GL.
    *   Add more reporting options/filters. <-- DONE for BS/P&L comparative/zero-balance. Could add more dimension/status filters.
3.  **Purchase Invoicing**: Begin implementation. <-- This is the next major new module.
    
Given the current state:
*   Sales Invoicing is quite complete for its initial scope (drafts, posting). Inventory updates are explicitly marked "Future". Advanced product search is a "nice-to-have" polish for later.
*   Reporting has seen significant refinement in display and export for key statements, and new options. Further refinements can be iterative.
*   User/Role Management is complete.

The most impactful next step according to the roadmap would be to **begin implementation of Purchase Invoicing**. This is a substantial new module.
    
**Plan for this Turn: Begin Purchase Invoicing - Part 1 (Models, DTOs, Service Interface, Basic Manager & Service Stubs).**

This is analogous to how Sales Invoicing was started: laying the foundational backend structures.

---
**Current Project Status Recap:**

*   **Sales Invoicing**: Fully functional (Draft CRUD, Posting with JE, List View, "Save & Approve" in dialog).
*   **User and Role Management UI**: Fully functional (User CRUD, Role CRUD, Permission Assignment).
*   **Reporting**:
    *   On-screen display for BS, P&L, TB, GL is functional.
    *   PDF/Excel export for BS & P&L has enhanced formatting.
    *   PDF/Excel export for TB & GL uses a simpler, generic table format.
*   All previously implemented features remain stable.
            
**Next Step Identification (from Roadmap):**
        
Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`. <-- DONE
    *   **Enhance line item entry (e.g., better product search/selection).** <-- Did basic enhancement. Advanced popup search is still an option.
    *   (Future) Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting and layout. <-- DONE for BS/P&L. Could extend to TB/GL.
    *   **Add more reporting options/filters.** <-- This is a good candidate.
3.  **Purchase Invoicing**: Begin implementation. <-- Major new module.
            
Let's consider the remaining "Refine Reporting" items.
*   **"Improve PDF/Excel export formatting and layout" for TB/GL**: While possible, the current generic table export for TB/GL is functional. The BS/P&L improvements were higher impact. This can be a polish item later.
*   **"Add more reporting options/filters"**: This is a good area for enhancement. Currently, `ReportsWidget` has basic date pickers. We could add:
    *   Comparative period selection for BS/P&L (the generator supports it, UI needs to pass the dates).
    *   Dimension filtering for reports (major, requires generator changes).
    *   Option to include/exclude zero-balance accounts (generator supports it for BS, UI needs checkbox).
    *   Specific filters for GL (e.g., transaction type, reference).
        
The "Purchase Invoicing" module is the next large, new functional area.
Before diving into a new major module like Purchase Invoicing, it might be good to add some smaller, valuable enhancements to existing features. Adding comparative period selection and zero-balance account toggles to the BS/P&L reports in `ReportsWidget` seems like a good, contained next step.

**Plan for this Turn: Enhance Reporting Options in `ReportsWidget` for BS & P&L.**
    
**Objective:** 
Modify `app/ui/reports/reports_widget.py` to:
1.  Allow users to select a comparative period for Balance Sheet and Profit & Loss reports.
2.  Provide an option to include/exclude zero-balance accounts in the Balance Sheet.
3.  Pass these new options to the `FinancialStatementGenerator`.
        
**Detailed Plan & Checklist for `app/ui/reports/reports_widget.py`:**

