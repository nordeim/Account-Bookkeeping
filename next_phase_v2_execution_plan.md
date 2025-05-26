Create a detailed plan with an integrated checklist to address coding/logic errors, functional gaps, and inconsistencies. You need to use the provided `next_phase_detailed_plan.md` and the self-correction/suggestion file (`you_will_carefully_review_and_validated_attached_proposed_changes_before_adopting_what_are_necessary.md`) as input for your own deliberation and refinement. You should not just copy, but leverage your own expertise. The plan needs to map out files to be created/updated in a logical sequence, their goals, purpose, and interfaces.

This is essentially asking you to act as a lead developer/architect, reviewing the current state (which was just established), the user's proposed next steps, and then creating a comprehensive, actionable plan.

**Core Inputs for Deliberation:**

1.  **Current Project State**: have a good understanding from the previous detailed review and file generation. Key areas are stable (startup, async bridge, settings UI, basic CoA/JE UI shells).
2.  **User's `next_phase_detailed_plan.md` (recapitulated in the prompt):** This plan focuses on fully implementing core journal entry functionality (backend manager methods and frontend UI interactions).
3.  **User's `you_will_carefully_review_and_validated_attached_proposed_changes_before_adopting_what_are_necessary.md` (your previous internal thoughts and the user's confirmation):** This confirms the previous steps were successful and outlines the next immediate focus on Journal Entry functionality (Manager methods: `update_journal_entry`, `get_journal_entry_for_dialog`, `get_journal_entries_summary`; Service method: `get_all_summary`). It also highlighted the UI connections.
4.  **My previous analysis and suggestions:** Things like harmonizing DB functions with Python logic, ensuring audit trigger user context, GST data aggregation, sequence generation strategy, etc.

**High-Level Plan Structure:**

The plan should be structured, perhaps by feature or component, and include:
*   **Objective**: What is the goal of this phase/step?
*   **Target Files**: List of files to be created or modified.
*   **Detailed Tasks/Checklist Items**: Specific actions, logic to implement, fixes, or verifications.
    *   For each task, you can briefly note its purpose and interface considerations.
*   **Verification/Testing Notes**: How to confirm the step is complete.

**Refining the User's Plan and Integrating My Own Insights:**

The user's plan is good and aligns with the MVP's critical path (Journal Entries). You need to:
1.  **Formalize it** into the requested "Enhancement Execution Plan with Integrated Checklist."
2.  **Integrate your previous observations** as checklist items or refinement points. For example, the sequence generator strategy or the audit trigger context.
3.  **Ensure logical sequencing** of file modifications. Backend first, then frontend.
4.  **Address potential errors/gaps** You might have noticed during previous reviews, or that are common in such development.
5.  **Be very detailed** with code snippets and explanations where appropriate (though the request is for the *plan*, not the full code implementation of the plan).

**Key Areas from My Analysis to Integrate into the Plan:**

*   **Audit Trigger Context**: While not directly part of JE functionality, it's a cross-cutting concern that needs to be addressed. It should be part of `DatabaseManager`.
*   **Sequence Generation**: Clarify and implement the primary strategy (`db_init.py` and `SequenceGenerator` use different formatting/prefix defaults). DB function `core.get_next_sequence_value` is preferred for atomicity. The Python `SequenceGenerator` should ideally call this DB function or its logic should be made robust.
*   **DB Functions vs. Python Logic**: Specifically for JE creation/posting. The plan should make a decision or outline how to reconcile.
*   **Error Handling**: Emphasize robust error handling in manager methods and UI feedback.
*   **Service Method `get_all_summary`**: Ensure it's performant enough, or plan for SQL-level aggregation if needed later.
*   **Completeness of DTOs/Models**: Double-check if all necessary fields are being passed and handled.

**Structuring the Plan:**

You will structure the plan into phases, starting with the immediate goal of fully functional Journal Entries.

**Phase 1: Solidify Journal Entry Backend**
    *   Objective: Ensure `JournalService` and `JournalEntryManager` fully support CRUD for JEs, posting, reversal, and efficient data retrieval for UI.
    *   Checklist items will cover method implementations and refinements.

**Phase 2: Integrate Journal Entry UI**
    *   Objective: Connect `JournalEntriesWidget` and `JournalEntryDialog` to the backend, enabling full JE lifecycle management from the UI.
    *   Checklist items will cover UI logic, data binding, async calls, and user feedback.

**Phase 3: Cross-Cutting Concerns & Refinements**
    *   Objective: Address architectural items like audit context, sequence generation strategy, and review critical helper utilities.
    *   Checklist items will cover these broader points.

**Phase 4: Review and Testing**
    *   Objective: Perform thorough testing of the implemented JE functionality.
    *   Checklist items for different test types.

This structure will allow for a logical progression. You will be specific about which files need attention in each step.
The "File Generation" part of the prompt means you should list the complete path of the files you are proposing to modify or create and ensure the plan leads to their correct, updated state.
The output will be a single Markdown document for the plan.
</think>

Absolutely! Based on the successful progress and the detailed inputs, here's a comprehensive "Enhancement Execution Plan (v1)" with an integrated checklist. This plan aims to address potential coding/logic errors, functional gaps, and inconsistencies, focusing on fully implementing the Core Journal Entry functionality as outlined in Step 2 of your MVP plan, while also integrating necessary refinements from your previous analyses.

---

# Enhancement Execution Plan (v1): Core Journal Entry & System Refinements

**Overall Objective:** Achieve robust and fully functional Journal Entry creation, editing (drafts), viewing, posting, and listing capabilities, integrated with a refined backend. Address key cross-cutting concerns for system stability and correctness.

---

## Phase 1: Solidify Journal Entry Backend Logic

**Objective:** Ensure `JournalService` and `JournalEntryManager` are complete, robust, and provide all necessary methods for UI interaction and data integrity regarding Journal Entries.

### 1.1 Enhance `app/services/journal_service.py`
   *   **Goal:** Optimize data retrieval and ensure save operations are robust for `JournalEntry` and its lines.
   *   **File to Update:** `app/services/journal_service.py`
   *   **Checklist & Tasks:**
        *   [ ] **Review `save(journal_entry: JournalEntry)`:**
            *   **Purpose:** Persist new or update existing `JournalEntry` entities along with their lines.
            *   **Action:** Confirm that SQLAlchemy's `cascade="all, delete-orphan"` on `JournalEntry.lines` correctly handles additions, updates, and deletions of `JournalEntryLine` objects when the parent `JournalEntry` is saved.
            *   **Action:** Verify that `session.flush()` and `session.refresh(journal_entry, attribute_names=['lines'])` (and refreshing individual lines if necessary) are used appropriately to ensure the ORM object graph reflects the database state, especially after modifications or for returning the saved entity.
            *   **Interface:** Called by `JournalEntryManager`.
        *   [ ] **Refine/Confirm `get_by_id(journal_id: int)`:**
            *   **Purpose:** Fetch a single `JournalEntry` with all its related data for detailed view/edit.
            *   **Action:** Ensure `selectinload` options are comprehensive for `JournalEntry.lines` and their nested relationships (e.g., `JournalEntryLine.account`, `JournalEntryLine.tax_code_obj`, `JournalEntryLine.currency`, `JournalEntryLine.dimension1`, `JournalEntryLine.dimension2`).
            *   **Interface:** Called by `JournalEntryManager.get_journal_entry_for_dialog()`.
        *   [ ] **Implement/Refine `get_all_summary(...)` more efficiently (Stretch Goal for Performance):**
            *   **Purpose:** Fetch a summarized list of journal entries for `JournalEntriesWidget`.
            *   **Current State:** The previous update uses Python-side summarization after fetching full JE objects with lines.
            *   **Action (Consideration):** For larger datasets, this could be slow. Evaluate if a more direct SQL query (e.g., using `func.sum` within the query itself or a database view) can be constructed to get `total_amount` directly, reducing data transfer and Python processing. This might be a future optimization if performance becomes an issue. For now, the Python-side summary in the service is acceptable for MVP.
            *   **Action:** Ensure the existing `get_all_summary` correctly applies filters (date range, status) and returns the dictionary structure expected by `JournalEntryManager` and `JournalEntryTableModel`.
            *   **Interface:** Called by `JournalEntryManager.get_journal_entries_for_listing()`.
        *   [ ] **Review `delete(id_val: int)`:**
            *   **Purpose:** Delete a *draft* journal entry.
            *   **Action:** Confirm logic correctly prevents deletion of posted entries.
            *   **Interface:** Called by `JournalEntryManager` (if a direct delete feature for drafts is added to UI).

### 1.2 Enhance `app/accounting/journal_entry_manager.py`
   *   **Goal:** Implement all business logic for Journal Entry lifecycle, ensuring correctness, validation, and interaction with services.
   *   **File to Update:** `app/accounting/journal_entry_manager.py`
   *   **Checklist & Tasks:**
        *   [ ] **Review `create_journal_entry(entry_data: JournalEntryData)`:**
            *   **Purpose:** Create a new draft journal entry.
            *   **Action:** Verify `is_posted` is set to `False`. Ensure `created_by_user_id` and `updated_by_user_id` are correctly assigned from `entry_data.user_id`. Validate fiscal period status.
            *   **Action:** Confirm `SequenceGenerator` is used for `entry_no`.
            *   **Interface:** Called by `JournalEntryDialog` via UI actions.
        *   [ ] **Implement `update_journal_entry(entry_id: int, entry_data: JournalEntryData)`:**
            *   **Purpose:** Update an existing *draft* journal entry.
            *   **Action:**
                *   Fetch existing `JournalEntry` using `journal_service.get_by_id()`.
                *   Return `Result.failure` if not found or if `is_posted` is `True`.
                *   Validate fiscal period for `entry_data.entry_date`.
                *   Update header fields of the fetched ORM object from `entry_data`.
                *   Handle `JournalEntryLine` updates:
                    *   Clear `existing_entry.lines` (e.g., `existing_entry.lines.clear()`).
                    *   Save the entry to flush line deletions (due to cascade).
                    *   Create new `JournalEntryLine` ORM objects from `entry_data.lines`, linking them to `existing_entry.id`.
                    *   Append new lines: `existing_entry.lines.extend(new_lines_orm)`.
                *   Set `updated_by_user_id`.
                *   Save via `journal_service.save()`.
            *   **Interface:** Called by `JournalEntryDialog` via UI actions.
        *   [ ] **Review `post_journal_entry(entry_id: int, user_id: int)`:**
            *   **Purpose:** Mark a draft JE as posted.
            *   **Action:** Validate fiscal period status. Ensure `updated_by_user_id` is set.
            *   **Interface:** Called by `JournalEntriesWidget` via UI actions.
        *   [ ] **Review `reverse_journal_entry(...)`:**
            *   **Purpose:** Create a counter-entry for a posted JE.
            *   **Action:** Confirm the transactional atomicity (creation of reversal JE and update of original JE happen together or not at all) using `async with self.app_core.db_manager.session()`.
            *   **Action:** Verify correct calculation of reversed line amounts and tax.
            *   **Action:** Ensure reversal entry is correctly linked (`source_type`, `source_id`) and original entry is updated (`is_reversed`, `reversing_entry_id`).
            *   **Interface:** Called by `JournalEntriesWidget` via UI actions.
        *   [ ] **Implement `get_journal_entry_for_dialog(entry_id: int)`:**
            *   **Purpose:** Fetch a complete `JournalEntry` (with lines and related line data) for the dialog.
            *   **Action:** Call `self.journal_service.get_by_id(entry_id)`. The service method should handle eager loading.
            *   **Interface:** Called by `JournalEntryDialog` and `JournalEntriesWidget`.
        *   [ ] **Implement `get_journal_entries_for_listing(filters: Optional[Dict[str, Any]] = None)`:**
            *   **Purpose:** Provide a summarized list of JEs for the table view.
            *   **Action:** Call `self.journal_service.get_all_summary(filters)`.
            *   **Action:** Ensure the returned `List[Dict[str, Any]]` matches the fields expected by `JournalEntryTableModel` (`id`, `entry_no`, `date`, `description`, `type`, `total_amount`, `status`). Dates should be `python_date` objects.
            *   **Interface:** Called by `JournalEntriesWidget._load_entries()`.
        *   [ ] **Review `generate_recurring_entries(...)`**:
            *   **Purpose**: Generate JEs based on active recurring patterns.
            *   **Action**: Confirm `_calculate_next_generation_date` handles various frequencies correctly, especially weekly logic involving specific `day_of_week`.
            *   **Action**: Ensure the template JE's lines are correctly copied to the new JE.
            *   **Action**: Verify that the `RecurringPattern`'s `last_generated_date`, `next_generation_date`, and `is_active` status are updated correctly after generation.
            *   **Interface**: Called by a scheduled task or a manual trigger (UI for this is future).

---

## Phase 2: Integrate Journal Entry UI

**Objective:** Ensure `JournalEntriesWidget` and `JournalEntryDialog` are fully functional and correctly interact with the `JournalEntryManager`.

### 2.1 Refine `app/ui/accounting/journal_entry_dialog.py`
   *   **Goal:** A robust dialog for creating, viewing, and editing (drafts) of Journal Entries.
   *   **File to Update:** `app/ui/accounting/journal_entry_dialog.py`
   *   **Checklist & Tasks:**
        *   [ ] **Data Loading (`_load_existing_journal_entry`)**:
            *   **Purpose:** Populate dialog fields when an existing JE is opened.
            *   **Action:** Call `self.app_core.journal_entry_manager.get_journal_entry_for_dialog()`.
            *   **Action:** Use the returned ORM object (`JournalEntry`) to populate header fields and lines. The serialization to JSON (`_serialize_je_for_ui`) and deserialization (`_populate_dialog_from_data_slot`) for cross-thread passing should correctly handle all fields, including dates and decimals.
            *   **Action:** Implement read-only mode: If `JournalEntry.is_posted` is true or `self.view_only_mode` is true, disable all input fields, hide "Save" buttons, possibly change window title.
        *   [ ] **ComboBox Population (`_populate_combos_for_row`)**:
            *   **Purpose:** Fill Account and Tax Code dropdowns for each line.
            *   **Action:** Ensure `self._accounts_cache` and `self._tax_codes_cache` (loaded in `_load_initial_combo_data`) are used. Handle cases where a loaded JE line refers to an inactive account/tax code (display it, but perhaps mark as inactive).
        *   [ ] **Line Amount/Tax Calculation (`_recalculate_tax_for_line`, `_calculate_totals`)**:
            *   **Purpose:** Update tax amount when base amount or tax code changes; update total debits/credits.
            *   **Action:** `_recalculate_tax_for_line` should be robust. Consider calling `self.app_core.tax_calculator.calculate_line_tax()` for accurate tax amounts if the logic becomes complex (current implementation is a simple percentage).
            *   **Action:** Ensure `_calculate_totals` accurately reflects sums and balance status (OK/Out of Balance).
        *   [ ] **Data Collection (`_collect_data`)**:
            *   **Purpose:** Gather data from UI fields into a `JournalEntryData` DTO.
            *   **Action:** Correctly retrieve values from `QComboBox.currentData()` (for IDs), `QDoubleSpinBox.value()`, `QDateEdit.date().toPython()`. Handle potential `None` or empty values. Perform basic client-side validation (e.g., at least one line, account selected if amounts are present).
        *   [ ] **Save Logic (`_perform_save`)**:
            *   **Purpose:** Call the appropriate `JournalEntryManager` method.
            *   **Action:** If editing (`self.journal_entry_id` exists), call `manager.update_journal_entry()`.
            *   **Action:** If new, call `manager.create_journal_entry()`.
            *   **Action:** If "Save & Post", and save is successful, call `manager.post_journal_entry()`.
            *   **Action:** Handle `Result` object from manager calls, display success/error messages using `QMessageBox` (invoked on main thread). Emit `self.journal_entry_saved` on success.
        *   [ ] **Error Handling**: Display clear error messages from manager results or validation failures.

### 2.2 Refine `app/ui/accounting/journal_entries_widget.py`
   *   **Goal:** A functional widget to list, filter, and manage Journal Entries.
   *   **File to Update:** `app/ui/accounting/journal_entries_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **Data Loading (`_load_entries`)**:
            *   **Purpose:** Populate the `QTableView` with a summary of JEs.
            *   **Action:** Call `self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters)`.
            *   **Action:** Pass filter values from `QDateEdit`s and `QComboBox` to the manager.
            *   **Action:** The received `List[Dict[str, Any]]` (via JSON for thread safety) should be passed to `self.table_model.update_data()`.
        *   [ ] **Action `on_new_entry()`**:
            *   **Purpose:** Launch `JournalEntryDialog` for creating a new JE.
            *   **Action:** Instantiate `JournalEntryDialog` with `journal_entry_id=None`. Connect its `journal_entry_saved` signal to `self._load_entries` for refreshing the list.
        *   [ ] **Action `on_edit_entry()`**:
            *   **Purpose:** Launch `JournalEntryDialog` for editing a selected draft JE.
            *   **Action:** Get selected `entry_id` and `status`. If draft, instantiate `JournalEntryDialog` with the `entry_id`. Connect `journal_entry_saved` signal.
        *   [ ] **Action `on_view_entry()` / `on_view_entry_double_click()`**:
            *   **Purpose:** Launch `JournalEntryDialog` in view-only mode.
            *   **Action:** Get selected `entry_id`. Instantiate `JournalEntryDialog` with the `entry_id` and `view_only=True`.
        *   [ ] **Action `on_post_entry()` / `_perform_post_entries()`**:
            *   **Purpose:** Post selected draft JEs.
            *   **Action:** Collect IDs of selected draft entries. Call `manager.post_journal_entry()` for each. Display aggregated success/failure messages. Refresh list.
        *   [ ] **Action `on_reverse_entry()` / `_perform_reverse_entry()`**:
            *   **Purpose:** Reverse a selected posted JE.
            *   **Action:** Get selected posted `entry_id`. Use `QInputDialog` for reversal date. Call `manager.reverse_journal_entry()`. Display result. Refresh list.
        *   [ ] **Action State Management (`_update_action_states`)**:
            *   **Purpose:** Enable/disable toolbar actions based on selection and JE status.
            *   **Action:** Ensure logic correctly handles single vs. multiple selections and draft/posted states.

### 2.3 Review `app/ui/accounting/journal_entry_table_model.py`
   *   **Goal:** Confirm the table model correctly displays summary data and provides necessary helper methods.
   *   **File to Review:** `app/ui/accounting/journal_entry_table_model.py`
   *   **Checklist & Tasks:**
        *   [ ] **`data()` method**: Verify correct formatting for date and `total_amount` (currency). Ensure `entry_id` is retrievable via `UserRole`.
        *   [ ] **Column Headers**: Match the fields being provided in the summary data (e.g., "Entry No.", "Date", "Description", "Type", "Total", "Status").
        *   [ ] **Helper methods**: `get_journal_entry_id_at_row` and `get_journal_entry_status_at_row` are functional.

---

## Phase 3: Cross-Cutting Concerns & System Refinements

**Objective:** Address system-wide architectural considerations for robustness and correctness.

### 3.1 Audit Trigger User Context
   *   **Goal:** Ensure that database audit triggers correctly capture the ID of the application user performing an action.
   *   **File to Update:** `app/core/database_manager.py`
   *   **Checklist & Tasks:**
        *   [ ] **Modify `DatabaseManager.session()` context manager**:
            *   **Purpose:** Set the `app.current_user_id` session variable in PostgreSQL.
            *   **Action:**
                ```python
                # Inside DatabaseManager.session()
                async with self.session_factory() as session:
                    try:
                        if self.app_core and self.app_core.current_user: # app_core needs to be passed to DBManager or accessible
                            user_id_str = str(self.app_core.current_user.id)
                            await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id_str}';"))
                        yield session
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
                    finally:
                        # Optional: Reset session variable if pool is reused extensively by different users in other contexts (less likely for desktop app)
                        # await session.execute(text("RESET app.current_user_id;")) 
                        await session.close()
                ```
            *   **Note:** `DatabaseManager` will need access to `ApplicationCore` or directly to `SecurityManager.current_user` to get the user ID. This might require passing `app_core` to `DatabaseManager` during initialization. (It seems `app_core` is already passed to services, which then use `db_manager.session()`, so `db_manager` itself might not need `app_core` if services using the session handle setting this. However, setting it centrally in `db_manager.session()` is cleaner if `db_manager` can access the current user.)
            *   **Alternative/Refinement**: If `DatabaseManager` cannot easily access `app_core.current_user`, the responsibility to set `app.current_user_id` could fall to the service layer methods *before* they perform DB operations within the session they obtain from `DatabaseManager`. This is less ideal as it's decentralized.
            *   **Decision for MVP**: The `ApplicationCore` is passed to services, and services obtain sessions from `db_manager`. The simplest way is for each service method that uses a session to set this variable if `app_core.current_user` is available. A better long-term solution would be to have the `DatabaseManager` accept an optional `user_id` in its `session()` method or have it aware of `app_core`. For now, let's assume the services will handle it or we will pass `app_core` to `DatabaseManager`.
            *   **Chosen Strategy**: Modify `DatabaseManager.initialize` to accept `app_core` and store it. Then `session()` can access `self.app_core.current_user`.

### 3.2 Sequence Generation Strategy
   *   **Goal:** Standardize and ensure robust document number generation.
   *   **Files to Update/Review:** `app/utils/sequence_generator.py`, `scripts/schema.sql` (DB function `core.get_next_sequence_value`), `app/accounting/journal_entry_manager.py` (and other managers using sequences).
   *   **Checklist & Tasks:**
        *   [ ] **Decision Point:** Prioritize either the PostgreSQL function `core.get_next_sequence_value()` or the Python `SequenceGenerator` class.
            *   **Recommendation:** The DB function is generally preferred for atomicity and concurrency safety.
        *   [ ] **If DB Function is Primary:**
            *   **Action:** Modify `app/utils/sequence_generator.py`: `SequenceGenerator.next_sequence()` should primarily call the `core.get_next_sequence_value()` DB function via `db_manager.execute_scalar()`.
            *   **Action:** The Python class can still handle formatting if the DB function only returns the numeric part, or the DB function can also handle formatting as it currently does. Ensure consistency.
        *   [ ] **If Python Class is Primary (Current State):**
            *   **Action:** The existing `SequenceGenerator` fetches the `Sequence` ORM object, increments `next_value`, and saves. This is less safe for high concurrency but may be acceptable for a desktop app.
            *   **Action:** Ensure the formatting logic in `SequenceGenerator` (handling `{VALUE:06}` type padding) is robust and matches the `format_template` stored in `core.sequences`.
        *   [ ] **Review `scripts/initial_data.sql` for `core.sequences`:** Ensure default `format_template` values are consistent with desired output.

### 3.3 Database Functions vs. Python Logic for Core Operations
   *   **Goal:** Clarify the primary implementation point for operations like JE creation and posting.
   *   **Files to Review:** `scripts/schema.sql` (DB functions `accounting.generate_journal_entry`, `accounting.post_journal_entry`), `app/accounting/journal_entry_manager.py`.
   *   **Checklist & Tasks:**
        *   [ ] **Decision Point:**
            *   **Option 1 (Python Primary):** `JournalEntryManager` methods contain all logic, using services for ORM operations. DB functions are not used by the app or are removed. (Current predominant approach).
            *   **Option 2 (DB Function Primary):** `JournalEntryManager` methods become thin wrappers calling the corresponding PostgreSQL functions. This can be good for complex atomic operations.
        *   [ ] **Action (For MVP with Python Primary):**
            *   Confirm that Python manager methods (`create_journal_entry`, `post_journal_entry`) are comprehensive and transactional where needed (e.g., `reverse_journal_entry` uses `async with session:`).
            *   The DB functions in `schema.sql` can remain as potential alternatives or for direct DB operations if needed by admins, but the application will primarily use the Python logic.

---

## Phase 4: Testing and Verification

**Objective:** Ensure the implemented Journal Entry functionality is working correctly and the system remains stable.

### 4.1 Manual Testing Checklist:
   *   [ ] **Application Launch/Shutdown**: Verify clean startup and exit.
   *   [ ] **Settings UI**:
        *   [ ] Company settings: Load, edit, save all fields.
        *   [ ] Fiscal Years:
            *   [ ] List existing FYs.
            *   [ ] Add New Fiscal Year: With monthly period generation. Verify FY and periods in DB.
            *   [ ] Add New Fiscal Year: With quarterly period generation.
            *   [ ] Add New Fiscal Year: With "None" for periods.
            *   [ ] Validate FY name uniqueness and date overlaps.
   *   [ ] **Chart of Accounts UI**:
        *   [ ] View account tree.
        *   [ ] Add new account (root and child).
        *   [ ] Edit existing account.
        *   [ ] Deactivate account (check balance/transaction validation if implemented).
        *   [ ] Activate account.
   *   [ ] **Journal Entries UI (`JournalEntriesWidget`)**:
        *   [ ] **List View**:
            *   [ ] Load and display initial list of JEs (if any seeded, or after creating some).
            *   [ ] Test date range filters.
            *   [ ] Test status filter ("All", "Draft", "Posted").
            *   [ ] Verify column data: Entry No, Date, Desc, Type, Total, Status.
        *   [ ] **New Entry**:
            *   [ ] Click "New Entry", `JournalEntryDialog` opens.
            *   [ ] Fill header (Date, Type, Desc, Ref).
            *   [ ] Add multiple lines: Select Accounts, enter Descriptions, Debits/Credits. Test mutual exclusivity of Debit/Credit.
            *   [ ] Select Tax Codes, verify Tax Amount auto-calculates (basic percentage for now).
            *   [ ] Check "Totals" labels update correctly (Debits, Credits, Balance status).
            *   [ ] Try to save with unbalanced entry (should fail with message).
            *   [ ] Save as Draft. Verify it appears in list with "Draft" status.
            *   [ ] Re-open "New Entry", save and post. Verify it appears with "Posted" status.
        *   [ ] **Edit Draft Entry**:
            *   [ ] Select a "Draft" JE, click "Edit Draft". `JournalEntryDialog` opens populated.
            *   [ ] Modify header and line items.
            *   [ ] Save changes (as draft). Verify changes in list and when re-opened.
            *   [ ] Edit draft and then "Save & Post". Verify.
        *   [ ] **View Entry**:
            *   [ ] Select any JE, click "View Entry" (or double-click). `JournalEntryDialog` opens.
            *   [ ] Verify all fields are read-only if entry is "Posted".
            *   [ ] Verify fields are editable if entry is "Draft" (though "Edit Draft" is the primary action for this).
        *   [ ] **Post Entry**:
            *   [ ] Select one or more "Draft" JEs. Click "Post Selected".
            *   [ ] Verify success/failure message.
            *   [ ] Verify status changes to "Posted" in the list.
            *   [ ] Try to re-post a "Posted" entry (Post button should be disabled).
        *   [ ] **Reverse Entry**:
            *   [ ] Select a "Posted" JE. Click "Reverse Selected".
            *   [ ] `QInputDialog` for reversal date appears. Enter date.
            *   [ ] Verify new reversal JE (RJE-xxxx) is created and original JE is marked (e.g. `is_reversed=True`).
            *   [ ] Verify reversal JE has opposite debit/credit amounts.
            *   [ ] (Optional) Verify reversal JE is initially a draft or auto-posted based on design.

### 4.2 Code Review & Static Analysis:
   *   [ ] Run `black .` for formatting.
   *   [ ] Run `flake8 .` for linting.
   *   [ ] Run `mypy app scripts` for type checking. Address any new errors.

---

This detailed plan should guide the next phase of development effectively. I will generate the files based on this plan, starting with the backend changes.
