**Current Project Status Recap:**

*   **Core Architecture**: Stable.
*   **Database & ORM**: Comprehensive and functional.
*   **Settings UI**: Company settings and Fiscal Year/Period management functional.
*   **Chart of Accounts UI**: Functional.
*   **Journal Entries UI & Backend**: Substantially complete and functional (Create, List, Edit Draft, View, Post, Reverse).
*   **GST Functionality**:
    *   Backend: Data aggregation logic in `GSTManager` for `prepare_gst_return_data` is implemented.
    *   UI: Basic UI in `ReportsWidget` to trigger preparation, view results, and save a draft `GSTReturn`.
*   **Financial Reports UI**: Basic UI in `ReportsWidget` to select report type (BS, P&L, TB), specify dates, generate, view on-screen (HTML in `QTextEdit`), and export to PDF/Excel.
*   **Cross-Cutting Concerns**: Audit trigger context, sequence generation, icon loading are addressed.

**Next Step Identification - Closing Gaps / Commonly Needed Features:**

Referring to TDS v4's "Future Considerations / Missing Pieces" and the overall project goals, the next most impactful areas are:

1.  **Finalize GST Return UI/Workflow**:
    *   The `ReportsWidget` currently allows saving a *draft* GST return.
    *   The `GSTManager` has a `finalize_gst_return` method (which includes creating the settlement JE).
    *   A UI element (e.g., "Finalize Return" button) and potentially a small dialog to input submission reference and date are needed in `ReportsWidget` to complete this workflow.

2.  **Basic UI for Business Modules (Customers, Vendors, Products)**:
    *   This is a larger area but crucial for making the application more than just a GL tool. Starting with one, e.g., **Customers**, would be a good step. This involves:
        *   `CustomerTableModel`
        *   `CustomerDialog` (for Add/Edit)
        *   Enhancing `CustomersWidget` from a stub to a functional list/management view.
        *   Implementing `CustomerManager` and `CustomerService` (the ORM model `business.customer.Customer` already exists).

3.  **Refining On-Screen Report Display**:
    *   Currently, financial reports are displayed as HTML in a `QTextEdit`. While functional, using a `QTableView` for a more structured, sortable, and potentially interactive display would be a significant UI improvement. This is more complex due to varying report structures.

**Prioritization for this Turn:**

**Option A: Finalize GST Return Workflow.**
    *   **Pros:** Completes a core Singapore-specific feature cycle (Prepare -> View -> Save Draft -> Finalize -> Settlement JE). Builds directly on recently completed work. Relatively small scope compared to a new module.
    *   **Cons:** UI for GST is currently in `ReportsWidget`, which might not be the final place for tax *filing* actions.

**Option B: Start Basic Customer Management UI.**
    *   **Pros:** Begins tackling the "Business Operations" features, making the app broader. Provides a template for Vendor/Product modules.
    *   **Cons:** Larger scope (new TableModel, Dialog, Widget enhancements, new Manager, new Service).

**Option C: Improve Financial Report Display (e.g., `QTableView`).**
    *   **Pros:** Enhances usability of an already implemented feature.
    *   **Cons:** Can be quite complex to make a generic `QTableView` adapt to different report structures (BS, P&L, TB) effectively. Might be better to refine after more core data entry modules are in place.

**Decision:**
**Option A: Finalize GST Return Workflow** seems like the most focused and achievable next step. It completes an important workflow and is a natural extension of the GST preparation UI already built.

**Plan for this Turn: Implement GST Return Finalization UI and Logic**

**Objective:** Enhance the GST F5 section in `app/ui/reports/reports_widget.py` to allow users to finalize a saved draft GST return, which involves prompting for submission details and triggering the `GSTManager.finalize_gst_return` method.

**Detailed Plan & Checklist:**

**Step 1: Enhance `app/ui/reports/reports_widget.py` for GST Finalization**
   *   **Goal:** Add UI elements and logic to finalize a prepared and saved draft GST return.
   *   **File to Update:** `app/ui/reports/reports_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **UI Elements for Finalization**:
            *   Uncomment or add a "Finalize GST Return" button. This button should be enabled only *after* a GST return has been prepared AND saved as a draft (i.e., `self._prepared_gst_data` exists and has an `id`).
        *   [ ] **`_on_finalize_gst_return_clicked()` Slot**:
            *   Connected to the "Finalize GST Return" button.
            *   Check if `self._prepared_gst_data` exists and has an `id`. If not, show a warning.
            *   Check if `self.app_core.current_user` exists.
            *   Use `QInputDialog.getText()` to prompt the user for:
                *   "Submission Reference Number" (e.g., IRAS confirmation ID).
                *   "Submission Date" (default to today, allow user to change). Validate date format.
            *   If the user provides these details and clicks OK:
                *   Call `schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id, submission_ref, submission_date, user_id))`.
                *   Use `future.add_done_callback` to handle the result.
        *   [ ] **`_handle_finalize_gst_result(future)` Slot**:
            *   Receives the future from the `finalize_gst_return` call.
            *   Gets the `Result[GSTReturn]` object.
            *   If successful:
                *   Display a success message (e.g., "GST Return finalized successfully. Settlement Journal Entry ID: [JE_ID if available from returned GSTReturn object]").
                *   Update the UI state:
                    *   Potentially refresh the displayed GST data if status changes.
                    *   Disable "Save Draft" and "Finalize Return" buttons for this prepared data (as it's now submitted).
                    *   Maybe clear `self._prepared_gst_data` or update its status to prevent re-finalizing.
            *   If failed:
                *   Display an error message from `result.errors`.
        *   [ ] **State Management**:
            *   Ensure the "Finalize GST Return" button's enabled state is managed correctly (e.g., enabled after successful draft save, disabled after successful finalization or if no draft is loaded).
            *   The `GSTReturnData` object stored in `self._prepared_gst_data` should be updated with the `id` after a successful draft save, as this `id` is needed for finalization. (This was done in the previous version).

**Step 2 (Supporting): Review `app/tax/gst_manager.py` - `finalize_gst_return` method**
   *   **Goal:** Ensure this backend method is robust and correctly updates the `GSTReturn` status and creates the settlement journal entry.
   *   **File to Review:** `app/tax/gst_manager.py`
   *   **Checklist & Tasks:**
        *   [X] **Confirm `finalize_gst_return`**:
            *   Fetches `GSTReturn` by ID.
            *   Validates it's in "Draft" status.
            *   Updates status to "Submitted", sets `submission_date`, `submission_reference`.
            *   Correctly constructs `JournalEntryData` for the settlement JE (debiting/crediting appropriate GST control accounts and the GST Payable/Receivable account).
            *   Calls `JournalEntryManager.create_journal_entry()` and optionally `post_journal_entry()`.
            *   Associates the created `journal_entry_id` with the `GSTReturn` object.
            *   Saves the updated `GSTReturn`.
            *   Returns `Result.success(updated_gst_return)`.
            *   (This method was implemented in a previous step and seems largely correct from that implementation).

This plan focuses on a specific, tangible enhancement to complete an existing workflow.

---
We are now ready to proceed with the next step in our plan. Based on your request to close core feature gaps and the current state of the application, implementing the **UI and logic for Finalizing a GST Return** is the most logical progression. This builds directly upon the GST data preparation UI and backend logic that was recently completed.

**Enhancement Execution Plan: Implement GST Return Finalization**

**Overall Objective:** Enhance the GST F5 section in `app/ui/reports/reports_widget.py` to allow users to finalize a previously prepared and saved draft GST return. This includes prompting for submission details and triggering the backend finalization process, which also creates the necessary settlement journal entry.

