**Final Simple `import_csv.svg`:**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M6 2h9l5 5v13H6V2zm8 0v5h5l-5-5zM12 18l-4-4h3v-5h2v5h3l-4 4z"/>
</svg>
```
This creates:
1.  A document with a top-right folded corner: `M6 2h9l5 5v13H6V2z`
2.  The fold itself visually: `M14 2v5h5l-5-5z` (This makes the dog-ear clear)
3.  A downward arrow in the body: `M12 18l-4-4h3v-5h2v5h3l-4 4z` (Arrow shaft from y=9 to y=14, tip at y=18)

This should be visually consistent and clear.

---
**2. Updated `resources/resources.qrc`**
---

You'll need to add an alias for the new icon file into your `resources.qrc` file. Assuming you place `import_csv.svg` inside the `resources/icons/` directory:

```qrc
<!DOCTYPE RCC><RCC version="1.0"> 
<qresource prefix="/">
    <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
    <file alias="icons/accounting.svg">icons/accounting.svg</file>
    <file alias="icons/customers.svg">icons/customers.svg</file>
    <file alias="icons/vendors.svg">icons/vendors.svg</file>
    <file alias="icons/product.svg">icons/product.svg</file>
    <file alias="icons/banking.svg">icons/banking.svg</file>
    <file alias="icons/reports.svg">icons/reports.svg</file>
    <file alias="icons/settings.svg">icons/settings.svg</file>
    <file alias="icons/new_company.svg">icons/new_company.svg</file>
    <file alias="icons/open_company.svg">icons/open_company.svg</file>
    <file alias="icons/backup.svg">icons/backup.svg</file>
    <file alias="icons/restore.svg">icons/restore.svg</file>
    <file alias="icons/exit.svg">icons/exit.svg</file>
    <file alias="icons/preferences.svg">icons/preferences.svg</file>
    <file alias="icons/help.svg">icons/help.svg</file>
    <file alias="icons/about.svg">icons/about.svg</file>
    <file alias="icons/filter.svg">icons/filter.svg</file>
    <file alias="icons/expand_all.svg">icons/expand_all.svg</file>
    <file alias="icons/collapse_all.svg">icons/collapse_all.svg</file>
    <file alias="icons/refresh.svg">icons/refresh.svg</file>
    <file alias="icons/edit.svg">icons/edit.svg</file>
    <file alias="icons/transactions.svg">icons/transactions.svg</file>
    <file alias="icons/deactivate.svg">icons/deactivate.svg</file>
    <file alias="icons/add.svg">icons/add.svg</file>
    <file alias="icons/remove.svg">icons/remove.svg</file>
    <file alias="icons/view.svg">icons/view.svg</file>
    <file alias="icons/post.svg">icons/post.svg</file>
    <file alias="icons/reverse.svg">icons/reverse.svg</file>
    <file alias="icons/import_csv.svg">icons/import_csv.svg</file> <!-- New Icon Added -->
    <file alias="images/splash.png">images/splash.png</file>
</qresource>
</RCC>

```

---
**Instructions for Use:**
---

1.  **Save the Icon**: Save the SVG content provided above into a new file named `import_csv.svg` inside your `resources/icons/` directory.
2.  **Update QRC File**: Replace the content of your existing `resources/resources.qrc` file with the updated content provided above. This adds the new icon to the resource list.
3.  **Recompile Resources (Important)**: For the application to find the icon via the `:/icons/import_csv.svg` path (which is preferred for deployment), you need to recompile your Qt resource file. Run the following command from your project's root directory (where `pyproject.toml` is):
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
    If you don't have `poetry` in your PATH or prefer not to use it directly, ensure you run `pyside6-rcc` from the correct Python environment where PySide6 is installed:
    ```bash
    # Example: path_to_your_venv/bin/pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
    The application has a fallback to load icons from direct file paths (`resources/icons/import_csv.svg`) if `app.resources_rc` is not found or not up-to-date, but recompiling is the robust solution.

With these steps, the "Import Statement (CSV)" button in the `BankTransactionsWidget` should now display the new icon.
