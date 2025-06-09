<think>
The user has confirmed that the previous bug fix was successful by providing a new screenshot and console log showing the application runs without the `NameError`. They are now asking me to proceed with the next step from the roadmap.

**Roadmap's "Current Focus / Next Steps"**:

1.  **Refine Bank Reconciliation**:
    *   ~~Implement UI and logic for handling complex matches...~~ (Done)
    *   ~~UI improvements for visually linking matched items...~~ (Done)
    *   **More robust error handling and user feedback during CSV import...** (This is a strong candidate for the next step).
2.  **Enhance Dashboard KPIs (Phase 2)**:
    *   Add more financial ratios (Quick Ratio, Debt-to-Equity).
    *   Investigate and implement simple graphical representations for KPIs.
    *   Allow user customization or period selection.

Given the focus on refining the Bank Reconciliation module, improving the **CSV import process** is the most logical next step. It directly addresses a point in the roadmap and enhances a core part of the reconciliation workflow. The current implementation is functional but lacks detailed feedback if a CSV file has errors, making it hard for users to diagnose and fix their import files.

My primary goal for this response is: **Implement more robust error handling and user feedback for the Bank Statement CSV import feature.**

---
### **Part 1: Systematic Diagnosis and Solution Architecture**

**Problem Statement:**
The current `BankTransactionManager.import_bank_statement_csv` method returns a simple summary dictionary: `{"imported_count": X, "skipped_duplicates_count": Y, ...}`. If a row fails due to a bad date format, invalid number, or missing required field, it is logged to the console and counted in `failed_rows_count`, but the user receives no specific information in the UI about *which* rows failed and *why*. This forces the user to check console logs (which they may not have open) or manually inspect their large CSV file to find the issue.

**Goal:**
Enhance the CSV import process to provide detailed, row-by-row feedback on parsing errors directly to the user in the UI. This will allow users to quickly identify and correct issues in their CSV files.

**Implementation Options Exploration:**

1.  **Simple QMessageBox with All Errors:**
    *   **Description:** Modify the `import_bank_statement_csv` manager method to collect a list of all error messages (e.g., `["Row 5: Invalid date format", "Row 12: Missing amount"]`). Return this list in the `Result` object. The UI dialog would then display all these errors in a large `QMessageBox`.
    *   **Pros:** Relatively simple to implement. Requires changes only to the manager and the dialog's result handling slot.
    *   **Cons:** Unwieldy for large files with many errors. A message box with 50+ lines of errors is a poor user experience. The message box is modal and not copy-paste friendly.

2.  **Generate a Separate Error Report File:**
    *   **Description:** After the import attempt, generate a new file (e.g., `import_errors.csv` or `.txt`) that lists the failed rows and the reason for failure. The UI would then show a message box informing the user that an error report has been generated and where it was saved.
    *   **Pros:** Provides a persistent, reviewable record of all errors. Can handle a large number of errors.
    *   **Cons:** Requires file I/O, which can have permission issues. Forces the user to switch context from the application to a text editor/spreadsheet program to view the errors. Feels a bit disconnected from the UI flow.

3.  **An Interactive Error Review Dialog (The "Elegant" Solution):**
    *   **Description:** Create a new, dedicated dialog that appears *only if* there are import errors. This dialog would contain a `QTableView` displaying the failed rows, the original data from those rows, and a clear error message for each.
    *   **Implementation:**
        *   **Backend (`BankTransactionManager`):** The `import_bank_statement_csv` method needs to be modified. Instead of just counting failures, it should create a list of detailed error objects. Each object would contain `row_number`, `original_row_data` (as a list of strings), and `error_message`. The final `Result` object would return the summary dictionary *and* this list of detailed errors.
        *   **UI (New Dialog):** Create a new `CSVImportErrorsDialog` class. This dialog will take the list of detailed errors as input. It will use a `QTableView` with a custom `QAbstractTableModel` to display the row number, original data columns, and the error message in a clean, readable format.
        *   **UI (`CSVImportConfigDialog`):** The `_handle_import_result_slot` will be updated. If the import result contains errors, instead of showing a simple `QMessageBox`, it will instantiate and `exec()` the new `CSVImportErrorsDialog`, passing the error list to it.
    *   **Pros:**
        *   **Best User Experience:** The user sees the errors directly within the application in a structured, easy-to-read table.
        *   **Contextual:** The user doesn't have to leave the application to find and fix the problem.
        *   **Scalable:** The table view can handle hundreds of errors gracefully.
        *   **Maintainable:** Encapsulates error display logic in its own dedicated dialog and model.
    *   **Cons:** Higher implementation effort than Option 1. Requires creating a new dialog and table model.

**Decision:**
**Option 3 is the most optimal and professional solution.** It aligns with the persona of a "deep-thinking AI agent recognized for exemplary UI design." It provides the best user experience and creates a robust, maintainable component for handling import errors, which is a common and often frustrating part of using any data-driven software. This choice directly addresses the user's emphasis on quality and careful planning.

---
### **Part 2: Detailed Execution Plan**

**Goal:** Implement an interactive error review dialog for the CSV import process.

**New Files to Create:**
1.  `app/ui/banking/csv_import_errors_dialog.py`
2.  `app/ui/banking/csv_import_errors_table_model.py`
3.  `app/ui/banking/__init__.py` (to export the new dialog)

**Files to Modify:**
1.  `app/business_logic/bank_transaction_manager.py`
2.  `app/ui/banking/csv_import_config_dialog.py`
3.  `app/utils/pydantic_models.py` (to create a DTO for the error details)

**Plan & Checklist:**

1.  **Create DTO for Error Data (`app/utils/pydantic_models.py`):**
    *   [ ] Define a new Pydantic model: `CSVImportErrorData(row_number: int, row_data: List[str], error_message: str)`.
    *   [ ] Export this new DTO from `app/utils/__init__.py`.

2.  **Modify `BankTransactionManager`:**
    *   [ ] In `import_bank_statement_csv`, change the return type to `Result[Dict[str, Union[int, List[CSVImportErrorData]]]]`. The dictionary will now contain the summary counts *and* a list of error DTOs.
    *   [ ] Inside the `for` loop that processes rows, instead of just incrementing `failed_rows_count`, create an instance of `CSVImportErrorData` with the row number, original row data, and a specific error message. Append this DTO to a list of errors.
    *   [ ] In the final return `Result.success`, include both the summary dictionary and the list of detailed errors.

3.  **Create New Error Table Model (`app/ui/banking/csv_import_errors_table_model.py`):**
    *   [ ] Create a new class `CSVImportErrorsTableModel` that inherits from `QAbstractTableModel`.
    *   [ ] Define headers like "Row #", "Error Message", and then dynamically add headers for the original data columns (e.g., "Original Col 1", "Original Col 2", ...).
    *   [ ] Implement `rowCount`, `columnCount`, `headerData`, and `data` methods to display the list of `CSVImportErrorData` DTOs.

4.  **Create New Error Review Dialog (`app/ui/banking/csv_import_errors_dialog.py`):**
    *   [ ] Create a `QDialog` subclass `CSVImportErrorsDialog`.
    *   [ ] Its `__init__` should accept the list of `CSVImportErrorData` DTOs.
    *   [ ] The UI will consist of a `QTableView` and a "Close" button.
    *   [ ] Instantiate `CSVImportErrorsTableModel` and set it as the model for the table view.
    *   [ ] Populate the model with the received error data.
    *   [ ] Add a helpful introductory label, e.g., "The following errors were found in the CSV file. Please correct them in your source file and try importing again."

5.  **Modify `CSVImportConfigDialog`:**
    *   [ ] Import the new `CSVImportErrorsDialog`.
    *   [ ] In `_handle_import_result_slot`, check if the `Result` object contains a list of errors.
    *   [ ] If errors are present, instantiate `CSVImportErrorsDialog` with the error list and `exec()` it. Then, show the summary `QMessageBox` (which will now include `failed_rows_count > 0`).
    *   [ ] If no errors are present, show the success `QMessageBox` as before and accept the dialog.

6.  **Update `app/ui/banking/__init__.py`:**
    *   [ ] Add the new `CSVImportErrorsDialog` to the `__all__` export list.

7.  **Final Validation:**
    *   [ ] Review all new and modified files.
    *   [ ] Perform a diff for each modified file against its original version to ensure no unintended changes.
    *   [ ] Mentally trace the flow: UI -> Manager -> Service -> Manager returns Result with errors -> UI catches errors and displays new dialog. This confirms the logic is sound.

This comprehensive plan ensures the new feature is implemented robustly, professionally, and adheres to the project's existing architecture. I will now proceed with the implementation.

