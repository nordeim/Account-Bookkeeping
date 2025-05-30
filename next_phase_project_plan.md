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
            
---
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

