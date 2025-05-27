You have a couple of solid options to determine which version of **PySide6** will be installed given your current dependency constraint (`PySide6 = ">=6.5.0"`):

1. **Use the Dry Run Feature**  
   You can simulate the installation without modifying your project by running:
   ```bash
   poetry add PySide6@latest --dry-run
   ```
   This command tells Poetry to resolve the dependency (respecting your constraint of `>=6.5.0`) and report what version it would install as if you were adding the package in its latest available form. The output will indicate the specific version that meets your requirements without making any changes to your `pyproject.toml`.

2. **Inspect the Locked Version**  
   If you’ve already run a lock update with `poetry lock` or have an existing `poetry.lock`, you can simply inspect that file. Look for the section referencing **PySide6** in the lock file. The resolved version there is the one Poetry will install. If you haven’t generated a lock file yet, you can create or update it by running:
   ```bash
   poetry lock
   ```
   Then, open the `poetry.lock` file and search for **PySide6** to see the exact version that was chosen in resolving dependencies.

3. **Check Using Poetry’s Show Command**  
   If you already have the package installed (or after generating the lock file), you can run:
   ```bash
   poetry show --latest PySide6
   ```
   This command displays the version currently installed (if any) alongside the latest version available that matches your specified constraints. It provides a quick overview of both the resolution and what updates might be available.

poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py

All these methods rely on Poetry’s dependency resolver to find the latest available version that complies with the constraint `>=6.5.0` for PySide6. In practice, because no upper bound is defined, Poetry will pick the newest version available in PyPI that satisfies any additional compatibility restrictions, such as those related to your Python version (which in your case are 3.9 through 3.12).

https://copilot.microsoft.com/shares/3kzfQD94L6ppvVTsciwoP

