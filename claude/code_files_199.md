Okay, I have meticulously reviewed the `diff` output for `app/reporting/report_engine.py` comparing the "previous" version (which had enhanced Trial Balance exports) with the "latest generated" version (which adds enhanced General Ledger exports).

**Overall Assessment:**

The changes are **valid, correct, and successfully implement enhanced PDF and Excel export functionality for the General Ledger (GL) report.** The dispatcher logic in `export_report` has been correctly updated to route GL reports to these new methods. Existing functionalities, including the recently enhanced Trial Balance exports and the BS/P&L exports, appear to be preserved and unaffected. The generic export methods now serve as true fallbacks.

**Detailed Review of Changes (Diff Analysis):**

1.  **`_setup_custom_styles()` Method:**
    *   `+ self.styles.add(ParagraphStyle(name='GLAccountHeader', parent=self.styles['h3'], fontSize=10, spaceBefore=0.1*inch, spaceAfter=0.05*inch, alignment=TA_LEFT))`
    *   **Validation**: Correct. A new `ParagraphStyle` named `GLAccountHeader` is added for formatting the account-specific header (Code, Name, Period) in the GL PDF report. This is a good, specific style.

2.  **`export_report()` Method:**
    *   The `elif title == "General Ledger":` conditions for both "pdf" and "excel" format types now correctly call the new dedicated methods:
        *   `return await self._export_general_ledger_to_pdf(report_data)`
        *   `return await self._export_general_ledger_to_excel(report_data)`
    *   The comments indicating these were fallbacks (`# Fallback for now`) have been removed.
    *   The final `else` clauses correctly call the generic export methods, now truly acting as fallbacks.
    *   **Validation**: Correct. The dispatcher logic is updated to use the new specialized GL export functions.

3.  **`_format_decimal()` Method:**
    *   `if value is None: return "" if show_blank_for_zero else "0.00"`
        changed to
        `if value is None: return "" if show_blank_for_zero else self._format_decimal(Decimal(0), places) # Ensure 0.00 for non-blank zero`
    *   **Validation**: This is a good refinement. If `show_blank_for_zero` is false and the value is `None`, it now explicitly calls itself with `Decimal(0)` and the specified `places` to ensure consistent formatting like "0.00" (or "0.0000" if `places=4`). Previously, it would have hardcoded "0.00". This makes the non-blank zero formatting respect the `places` parameter. Valid.

4.  **`_add_pdf_header_footer()` Method:**
    *   The comments like `# Header` and `# Footer` were removed.
    *   The calculation of `page_width` and `header_y_start` and `footer_y` is the same.
    *   The Y-coordinates for drawing strings in the header were slightly adjusted:
        *   Company Name Y: `header_y_start` (was `doc.height + doc.topMargin - 0.5*inch`) - equivalent.
        *   Report Title Y: `header_y_start - 0.25*inch` (was `doc.height + doc.topMargin - 0.75*inch`) - raises it slightly.
        *   Date Desc Y: `header_y_start - 0.5*inch` (was `doc.height + doc.topMargin - 1.0*inch`) - raises it slightly.
    *   The Y-coordinate for footer strings `footer_y` is still `0.5*inch`.
    *   The X-coordinate for `drawRightString` changed from `doc.width + doc.leftMargin - 0.1*inch` to `page_width - doc.rightMargin`. This is more robust as `page_width` directly considers all margins.
    *   **Validation**: These are minor positional adjustments and a more robust way to calculate right-alignment X. The core functionality is preserved. Valid.

5.  **NEW: `_export_general_ledger_to_pdf()` Method:**
    *   **Validation**: Correctly implemented as per the plan.
        *   Sets `pagesize=landscape(A4)`.
        *   Uses `_add_pdf_header_footer` for the overall page frame.
        *   Adds report-specific headers (Account Code, Name, Period) using `Paragraph` and the new `GLAccountHeader` style.
        *   Displays Opening Balance using `AccountNameBold` style.
        *   Creates a `Table` for transactions with the correct columns. Data is formatted using `_format_decimal` and `Paragraph` for text wrapping (descriptions are truncated to `[:40]` which is a pragmatic choice for PDF fixed-width cells to avoid overly complex flowable calculations for this iteration).
        *   Applies `TableStyle` with grid, header styling, and text alignments.
        *   Displays Closing Balance using `AmountBold` style.
        *   Defines specific `col_widths_gl` appropriate for the landscape layout and content.
    *   **Impact**: Provides a well-formatted, dedicated PDF export for General Ledger.

6.  **`_export_generic_table_to_pdf()` Method (Fallback):**
    *   A warning log message `self.app_core.logger.warning(...)` is added if this generic method is hit.
    *   The GL-specific data extraction logic previously in this generic method has been removed (as it's now in the dedicated `_export_general_ledger_to_pdf`).
    *   The fallback now expects a simpler `report_data` structure with `'data_rows'` and `'headers'` keys if it's ever used for truly generic tables.
    *   **Validation**: Correct. This method is now a cleaner fallback. The removal of GL-specific logic from here is appropriate.

7.  **`_apply_excel_header_style()` Method:**
    *   `wrap_text=True` added to `Alignment` for `center` and `left` alignments.
    *   **Validation**: Good improvement for Excel headers, allowing text to wrap if column width is constrained.

8.  **Excel Export Methods (`_export_balance_sheet_to_excel`, `_export_profit_loss_to_excel`, `_export_trial_balance_to_excel`):**
    *   These methods are unchanged from the previous version, which is correct as they were already enhanced or created for their respective reports. No regressions.

9.  **NEW: `_export_general_ledger_to_excel()` Method:**
    *   **Validation**: Correctly implemented as per the plan.
        *   Sets an appropriate worksheet title like "GL-ACCCODE".
        *   Writes Company Name, "General Ledger", Account Info, and Period as main report headers, styled using `_apply_excel_header_style`.
        *   Sets styled column headers for the transaction list.
        *   Adds a distinct row for Opening Balance, styled.
        *   Iterates through transactions, writing data to cells and applying formatting (dates, numbers via `_apply_excel_amount_style`).
        *   Adds a distinct row for Closing Balance, styled with an underline.
        *   Adjusts column widths for readability, giving more space to description fields.
    *   **Impact**: Provides a well-formatted, dedicated Excel export for General Ledger.

10. **`_export_generic_table_to_excel()` Method (Fallback):**
    *   A warning log message added.
    *   The logic simplified to work with a generic `headers` list and `data_rows` (list of dicts or list of lists).
    *   Column widths set to a default of 20.
    *   **Validation**: Correctly simplified to be a more generic fallback. The removal of TB-specific logic is appropriate as TB now has its own dedicated Excel export.

**Conclusion on `app/reporting/report_engine.py` Changes:**

The changes are **valid, well-executed, and successfully introduce dedicated, enhanced export functionalities for the General Ledger report in both PDF and Excel formats.**
*   **Dedicated GL Exports**: The new methods provide a much more professional and readable output for GL compared to the previous generic table exports.
*   **Improved Styling**: Enhancements to PDF styles (`GLAccountHeader`) and Excel styling helpers (`_apply_excel_header_style` with `wrap_text`, `_apply_excel_amount_style` with better zero handling) benefit all relevant reports.
*   **Dispatcher Logic**: The `export_report` method now correctly routes GL reports to their dedicated functions.
*   **Fallbacks**: The generic export methods are now cleaner and serve as true fallbacks.
*   **No Loss of Functionality**: Exports for BS, P&L, and TB remain fully functional and as previously enhanced.

The `ReportEngine` has been significantly improved, offering high-quality export options for all primary financial statements.
