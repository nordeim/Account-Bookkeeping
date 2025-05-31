Okay, I've carefully reviewed the `diff` output for `app/business_logic/sales_invoice_manager.py`.

**Overall Assessment:**

The changes are **valid and correctly implement the inventory movement and COGS journal entry generation** upon posting a Sales Invoice. The logic is well-integrated into the existing `post_invoice` method and maintains transactional integrity by using the provided session. No original features related to sales invoice posting (financial JE, status updates) appear to be lost or negatively impacted. The new functionality aligns with standard perpetual inventory accounting practices.

**Detailed Review of Changes (Diff Analysis):**

1.  **Import Changes:**
    *   `+from sqlalchemy import text # Added for text()`: Correctly added as raw SQL (`text()`) is used to query the `business.inventory_summary` view.
    *   `+from app.models.business.inventory_movement import InventoryMovement # New import`: Necessary for creating `InventoryMovement` ORM objects.
    *   `+from app.services.business_services import SalesInvoiceService, CustomerService, ProductService, InventoryMovementService # Added InventoryMovementService`: Correctly adds the new `InventoryMovementService` dependency.
    *   `+from app.common.enums import InvoiceStatusEnum, ProductTypeEnum, JournalTypeEnum, InventoryMovementTypeEnum # Added InventoryMovementTypeEnum`: Correctly adds the new enum for inventory movement types.

2.  **`__init__` Method Update:**
    *   `+                 inventory_movement_service: InventoryMovementService): # New dependency`
    *   `+        self.inventory_movement_service = inventory_movement_service # New dependency`
    *   **Validation**: Correct. The new `InventoryMovementService` is injected and stored.

3.  **`_validate_and_prepare_invoice_data` Method Update:**
    *   `calculated_lines_for_orm.append({... "_product_type": product_type_for_line})`:
    *   **Validation**: Correctly adds the `_product_type` to the prepared line data. This is used later in `post_invoice` to determine if an item is an 'Inventory' type. This is a good way to pass this information through.

4.  **`post_invoice` Method - Significant Changes (Core of this update):**
    *   **Eager Loading**:
        ```diff
        -                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.tax_code_obj).selectinload(TaxCode.affects_account),
        +                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.inventory_account), # For COGS inventory account
        +                        selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product).selectinload(Product.purchase_account), # For COGS expense account
        ```
        *   **Validation**: Correct. Eager loading for `inventory_account` and `purchase_account` (used as COGS account) of the product is added, which is necessary for the new COGS JE logic. The `tax_code_obj` for the product line itself wasn't directly used in the COGS JE logic but was correctly used for the main financial JE tax lines, so its removal from this specific `options` list (if it was solely for COGS) is fine, as `line.tax_code_obj` is still loaded for the main JE.

    *   **Default COGS Account**:
        *   `+                default_cogs_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultCOGS", "5100") # New default`
        *   **Validation**: Correct. A new default account key 'SysAcc_DefaultCOGS' is introduced for COGS. This implies this key should be added to `initial_data.sql` and potentially `pydantic_models.py` if there's a DTO for system configurations. For this change, it's correctly fetched.

    *   **Inventory Movements and COGS JE Logic Block**: This entire new block is added after the main financial JE is created and posted, but within the same session.
        *   `+                cogs_je_lines_data: List[JournalEntryLineData] = []`
        *   `+                for line in invoice_to_post.lines:`
        *   `+                    if line.product and ProductTypeEnum(line.product.product_type) == ProductTypeEnum.INVENTORY:`
            *   **Validation**: Correctly checks if the line item is an 'Inventory' type product.
        *   **Fetching WAC**:
            ```python
            +                        wac_query = text("SELECT average_cost FROM business.inventory_summary WHERE product_id = :pid")
            +                        wac_result = await session.execute(wac_query, {"pid": line.product_id})
            +                        current_wac = wac_result.scalar_one_or_none()
            +                        if current_wac is None: current_wac = line.product.purchase_price or Decimal(0) # Fallback
            ```
            *   **Validation**: Correctly queries the `business.inventory_summary` view using raw SQL (`text()`) executed via the current `session`. This ensures transactional consistency for reading the WAC *before* the current sale's impact. The fallback to `product.purchase_price` or `Decimal(0)` is a reasonable approach if the product has no prior summary (e.g., first transaction).
        *   `cogs_amount_for_line` calculation: Correct.
        *   **Creating `InventoryMovement`**:
            ```python
            +                        inv_movement = InventoryMovement(
            +                            product_id=line.product_id, movement_date=invoice_to_post.invoice_date,
            +                            movement_type=InventoryMovementTypeEnum.SALE.value, quantity=-line.quantity, # Negative for outflow
            +                            unit_cost=current_wac, total_cost=cogs_amount_for_line,
            +                            reference_type='SalesInvoiceLine', reference_id=line.id, created_by_user_id=user_id
            +                        )
            +                        await self.inventory_movement_service.save(inv_movement, session=session)
            ```
            *   **Validation**: Correct. `movement_type` is 'Sale', `quantity` is negative, `unit_cost` is the fetched WAC, `total_cost` is derived. `reference_type` and `reference_id` correctly link to the `SalesInvoiceLine`. `created_by_user_id` is passed. The `save` method of `inventory_movement_service` is called with the current `session`.
        *   **Determining COGS and Inventory Accounts for JE**:
            ```python
            +                        cogs_acc_id = line.product.purchase_account_id if line.product.purchase_account and line.product.purchase_account.is_active else (await self.account_service.get_by_code(default_cogs_acc_code)).id # type: ignore
            +                        inv_asset_acc_id = line.product.inventory_account_id if line.product.inventory_account and line.product.inventory_account.is_active else None
            +                        if not cogs_acc_id or not inv_asset_acc_id: return Result.failure(["COGS or Inventory Asset account setup issue for product."])
            ```
            *   **Validation**: Correct. COGS account uses `product.purchase_account_id` as a primary source (this is a common simplification; a dedicated COGS account on the product would be an alternative) and falls back to `default_cogs_acc_code`. Inventory Asset account uses `product.inventory_account_id`. Both are checked for activity. Returns failure if accounts cannot be determined.
        *   **Creating COGS JE Lines**:
            ```python
            +                        cogs_je_lines_data.append(JournalEntryLineData(account_id=cogs_acc_id, debit_amount=cogs_amount_for_line, credit_amount=Decimal(0), description=f"COGS: {line.description[:50]}"))
            +                        cogs_je_lines_data.append(JournalEntryLineData(account_id=inv_asset_acc_id, debit_amount=Decimal(0), credit_amount=cogs_amount_for_line, description=f"Inventory Sold: {line.description[:50]}"))
            ```
            *   **Validation**: Correct. Debits COGS account, Credits Inventory Asset account with the `cogs_amount_for_line`.
        *   **Creating and Posting COGS JE**:
            ```python
            +                if cogs_je_lines_data:
            +                    cogs_je_dto = JournalEntryData(journal_type=JournalTypeEnum.GENERAL.value, entry_date=invoice_to_post.invoice_date, description=f"COGS for SI {invoice_to_post.invoice_no}", source_type="SalesInvoiceCOGS", source_id=invoice_to_post.id, user_id=user_id, lines=cogs_je_lines_data)
            +                    create_cogs_je_result = await self.app_core.journal_entry_manager.create_journal_entry(cogs_je_dto, session=session)
            +                    if not create_cogs_je_result.is_success or not create_cogs_je_result.value: return Result.failure(["Failed to create COGS JE."] + create_cogs_je_result.errors)
            +                    post_cogs_je_result = await self.app_core.journal_entry_manager.post_journal_entry(create_cogs_je_result.value.id, user_id, session=session)
            +                    if not post_cogs_je_result.is_success: return Result.failure([f"COGS JE (ID: {create_cogs_je_result.value.id}) created but failed to post."] + post_cogs_je_result.errors)
            ```
            *   **Validation**: Correct. If there are COGS lines (i.e., inventory items were sold), a new 'General' type JE is created and posted using `JournalEntryManager`, passing the current `session` to ensure it's part of the overall transaction. `source_type` is appropriately 'SalesInvoiceCOGS'.

    *   **Error Handling & Logging**: The existing `try-except` block for the overall posting process remains, which will catch exceptions from the new inventory/COGS logic. Log messages are appropriate.

**Conclusion on `app/business_logic/sales_invoice_manager.py` Changes:**

The modifications are **valid, robust, and correctly implement the required inventory outflow tracking and COGS accounting** for sales of 'Inventory' type products.
*   **Transactional Integrity**: The new operations (InventoryMovement creation, COGS JE creation/posting) are correctly integrated within the existing database transaction of the `post_invoice` method by passing the `session` object.
*   **WAC Usage**: Fetching WAC from the `inventory_summary` view within the transaction is a good approach to get a cost reflective of the state before the current sale.
*   **Account Determination**: Logic for COGS and Inventory Asset accounts, including fallbacks, is sound and consistent with other account determination patterns in the codebase.
*   **No Loss of Functionality**: The original financial JE creation for the sale (AR, Revenue, GST) is preserved and executed before the inventory/COGS logic.
*   **Modularity**: The use of `InventoryMovementService` and `JournalEntryManager` keeps the `SalesInvoiceManager` focused on orchestrating the sales process.

The changes are well-implemented and address the roadmap item effectively. The application will now correctly account for inventory depletion and COGS when sales invoices with inventory items are posted.
