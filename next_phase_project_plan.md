**Current Project Status Recap:**

*   **Sales Invoicing**: 
    *   `SalesInvoiceDialog`: Fully functional for creating/editing drafts, dynamic calculations, "Save Draft", and "Save & Approve" (which includes posting JE).
    *   `SalesInvoicesWidget`: Lists invoices, allows opening dialog, and batch posting of drafts.
    *   `SalesInvoiceManager`: Backend logic for draft CRUD and posting is complete.
*   **User and Role Management UI**: Fully functional.
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`. <-- **DONE**
    *   **Enhance line item entry (e.g., better product search/selection).** <-- Previously, I made minor enhancements to the product combo text. A more robust product search popup could still be an option.
    *   (Future) Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   **Improve PDF/Excel export formatting and layout.** <-- This is a good candidate.
    *   Add more reporting options/filters.
3.  **Purchase Invoicing**: Begin implementation. 
    
Considering the options:
*   Further enhancing product search in `SalesInvoiceDialog` (e.g., a popup search dialog) is a UX improvement but might be a larger piece of work than initially anticipated if done fully.
*   Beginning Purchase Invoicing is a major new module.
*   Improving PDF/Excel export formatting for the existing reports (BS, P&L, TB, GL) is a valuable refinement and builds on already functional reporting logic. It directly addresses a "Refine Reporting" roadmap item.
        
**Decision for this Turn: Refine Reporting - Improve PDF/Excel Export Formatting for Balance Sheet and Profit & Loss.**
    
The current `ReportEngine._export_to_pdf_generic` and `_export_to_excel_generic` methods produce very basic tabular layouts. We can make them more professional.
    
**Plan for this Turn: Enhance PDF/Excel Export for BS & P&L.**

**Objective:**
Improve the visual presentation and structure of Balance Sheet and Profit & Loss reports when exported to PDF and Excel via `ReportEngine`.
        
---
**Current Project Status Recap:**
                
*   **Sales Invoicing**:
    *   `SalesInvoiceDialog`: Fully functional for creating/editing drafts, including dynamic calculations and the "Save & Approve" workflow (draft save then post).
    *   `SalesInvoicesWidget`: Lists invoices, allows opening dialog for new/edit/view, and has a "Post Invoice(s)" action for batch posting drafts.
    *   `SalesInvoiceManager`: Backend logic for draft CRUD and posting (including JE creation) is complete.
*   **User and Role Management UI**: Fully functional for managing users, roles, and permissions between them.
*   All previously implemented features (Core Accounting, Customer/Vendor/Product Management, GST F5, Basic Reporting) remain stable.
                
**Next Step Identification (from Roadmap):**

Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`. <-- **DONE**
    *   **Enhance line item entry (e.g., better product search/selection).** <-- This is a good candidate.
    *   (Future) Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   **Improve PDF/Excel export formatting and layout.**
    *   Add more reporting options/filters.
3.  **Purchase Invoicing**: Begin implementation.
                
From the remaining short-term items, enhancing the line item entry in `SalesInvoiceDialog` or improving PDF/Excel export formatting are both viable. Let's prioritize a UI/UX improvement within the already functional `SalesInvoiceDialog`.   
    
**Plan for this Turn: Enhance `SalesInvoiceDialog` Line Item Product Selection.**
        
**Current Product Selection in `SalesInvoiceDialog` Lines:**
*   A `QComboBox` is used for "Product/Service".
*   It's populated with all active products/services.
*   It has an editable text field and a completer for basic searching within the combo list.
    
**Potential Enhancements & Options for "Better Product Search/Selection":**
        
1.  **Improved `QComboBox` Completer**:
    *   Ensure the completer is case-insensitive and matches substrings effectively. (Already uses `MatchContains`).
    *   Display more info in the completer popup (e.g., "Code - Name - Price"). This requires a custom completer model.
2.  **Dedicated Product Search Button/Popup**:
    *   Next to the product combo (or instead of it), have a "Search" button.
    *   Clicking it opens a small dialog with a search field and a table/list view of products, allowing for more advanced filtering (e.g., by category, type) and selection.
    *   Selected product from this popup then populates the invoice line.
3.  **Type-Ahead with Server-Side/Manager-Side Filtering (for very large product lists)**:
    *   As the user types in the product field, asynchronously query the `ProductManager` for matching products and update a popup list. This is more complex and likely overkill for now given the current architecture.

**Chosen Approach for this Turn:**
Option 1: **Improved `QComboBox` Completer**. This is a non-intrusive enhancement that improves usability without major structural changes to the dialog. We can make the product combo display more information in its dropdown list if we use a `QStandardItemModel` for it, rather than just `addItem()`.

**Detailed Plan & Checklist for Improving Product Selection in `SalesInvoiceDialog`:**

