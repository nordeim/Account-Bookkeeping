<think>
The user wants me to update the `project_test_guide (draft).md`.
My sources for this update are:
1.  `project_test_guide (draft).md` (the input file).
2.  `project_codebase_tests_files.md` (this is crucial as it contains the actual test file structure and some content, including `conftest.py`).
3.  `README.md` (the version I just generated, which has an up-to-date "Testing" section).
4.  Other documents for general project context (like Python versions, Poetry usage).

The goal is a *complete* updated *replacement* file for the test guide. It needs to be self-contained and reflect the current state.

**Plan of Action:**

I will go through the `project_test_guide (draft).md` section by section and compare/update it based on the provided sources.

*   **Section 1: Prerequisites**:
    *   Confirm Python version and Poetry mention.
    *   Verify the list of testing libraries (`pytest`, `pytest-asyncio`, `pytest-cov`, `unittest.mock`). `project_codebase_tests_files.md` doesn't list dependencies directly, but their usage in test files implies they are needed. The `README.md`'s "Technology Stack" section listed these.

*   **Section 2: Test Structure**:
    *   This is a key area to update based on `project_codebase_tests_files.md`.
    *   **`tests/`**: Root directory.
    *   **`conftest.py`**: The draft says it "can remain empty or have basic configurations". The provided `project_codebase_tests_files.md` shows `conftest.py` with an example fixture. I should reflect this.
    *   **`unit/`**:
        *   The draft lists: `tax/`, `utils/`, `services/`, and `*(Other subdirectories will be added...)*`.
        *   `project_codebase_tests_files.md` shows a more extensive structure under `tests/unit/`:
            *   `accounting/` (currently empty according to my README generation's project structure, but should be listed if the test files imply its existence as a directory) - *Correction*: the README structure for tests indicates `accounting/`, `business_logic/`, `core/` are currently empty *as directories for tests*. The test file structure from `project_codebase_tests_files.md` *does not explicitly show* these directories, but shows tests directly in `services/`, `tax/`, `utils/`, and `reporting/`.
            *   `reporting/`: (e.g., `test_dashboard_manager.py`, `test_financial_statement_generator.py`) - This is a new one to add to the test guide structure.
            *   The list of files in `services/` is very long. I don't need to list every file, but I should mention that it's well-populated.
    *   **`integration/`**: Draft says "(Planned)". `project_codebase_tests_files.md` shows `tests/integration/__init__.py` and `tests/integration/test_example_integration.py` (empty). So, "basic structure exists, more tests planned" is more accurate.
    *   **`ui_tests/`**: Draft says "(Planned)". `project_codebase_tests_files.md` shows `tests/ui/__init__.py` and `tests/ui/test_example_ui.py` (empty). Similar to integration tests, "basic structure exists, more tests planned". The draft guide calls it `ui_tests/`, while the actual files show `ui/`. I should use `ui/`.

*   **Section 3: Running Tests**:
    *   **3.1 Running All Tests**: Commands `poetry run pytest` and `pytest` are standard.
    *   **3.2 Running Specific Test Files or Directories**: Examples are good. I'll verify the paths match the actual structure (e.g., `tests/unit/tax/test_tax_calculator.py`).
    *   **3.3 Test Verbosity**: `-v` and `-vv` are standard.
    *   **3.4 Test Coverage**:
        *   Command `poetry run pytest --cov=app tests/` is standard.
        *   Command for HTML report `poetry run pytest --cov=app --cov-report=html tests/` and mention of `htmlcov/` directory are correct.
    *   **3.5 Running Asynchronous Tests**: The draft correctly states `pytest-asyncio` handles this automatically. The `pyproject.toml` or `pytest.ini` would ideally contain `asyncio_mode = auto`. I can add a note that this is the typical setup.

*   **Section 4: Viewing Test Results**: Description of `.`, `F`, `E`, `s`, `x` is standard.

*   **Section 5: Writing New Tests**:
    *   Placement of unit tests: Should reflect the updated structure (`tax/`, `utils/`, `services/`, `reporting/`).
    *   Naming conventions are standard.
    *   Mention of `pytest` fixtures, `assert`, `pytest.raises`, `async def`, and `unittest.mock` is good.

**Self-contained and No References:**
I will ensure the final document stands alone and doesn't refer to "this draft" or previous versions.

**Specific changes based on `project_codebase_tests_files.md`:**

*   Update `conftest.py` description to mention it can contain project-wide fixtures, and give an example as shown in the provided file content.
*   Update the `unit/` subdirectory list in Section 2 to include `reporting/` and specify the kinds of tests within each.
*   Update `integration/` and `ui/` descriptions to "Basic structure exists; more tests planned." and use `ui/` instead of `ui_tests/`.
*   The `pytest-asyncio` configuration note: I'll add a small sentence like "Ensure `pytest-asyncio` is installed (it's a dev dependency) and pytest is configured for asyncio mode (e.g., `asyncio_mode = auto` in `pytest.ini` or `pyproject.toml`), which is typically the default for `pytest-asyncio`."

The overall structure of the draft guide is good. The main work is to align Section 2 (Test Structure) with the reality of the `project_codebase_tests_files.md` and make minor enhancements for clarity and completeness.

Let's prepare the updated document.
The name of the file should be `project_test_guide.md`.
The draft is already quite good. The provided `project_codebase_tests_files.md` mostly confirms and slightly expands on the structure.
The `conftest.py` from the source files:
```python
# File: tests/conftest.py
# This file can be used for project-wide pytest fixtures.
# For now, it can remain empty or have basic configurations if needed later.

import pytest

# Example of a fixture if needed later:
# @pytest.fixture(scope="session")
# def db_url():
#     return "postgresql+asyncpg://testuser:testpass@localhost/test_db"
```
This is good, I can directly use this description.

Okay, proceeding with the generation.Okay, I have reviewed the `project_test_guide (draft).md` and the other relevant documents, especially `project_codebase_tests_files.md` which shows the current test structure and content.

Here is the complete updated replacement file for `project_test_guide.md`:

```markdown
# Project Test Guide: SG Bookkeeper

This guide provides instructions on how to set up the testing environment and run the automated tests for the SG Bookkeeper application.

## 1. Prerequisites

*   **Python Environment**: Ensure you have Python (version specified in `pyproject.toml`, e.g., 3.9+) and Poetry installed.
*   **Dependencies**: All development dependencies, including testing libraries (`pytest`, `pytest-asyncio`, `pytest-cov`, `unittest.mock`), should be installed. If you set up the project using `poetry install --with dev` (recommended) or `poetry install` (if dev dependencies are not in a separate group), these should already be available in your project's virtual environment.

## 2. Test Structure

The tests are organized as follows within the `tests/` root directory:

*   **`tests/conftest.py`**:
    *   This file is used for project-wide pytest fixtures and configuration. It might contain shared setup/teardown logic or helper fixtures accessible by all tests.
    *   Example content (from the project):
        ```python
        # File: tests/conftest.py
        import pytest

        # Example of a fixture if needed later:
        # @pytest.fixture(scope="session")
        # def db_url():
        #     return "postgresql+asyncpg://testuser:testpass@localhost/test_db"
        ```

*   **`tests/unit/`**:
    *   Contains unit tests designed to test individual modules, classes, or functions in isolation, often using mocks for external dependencies.
    *   Subdirectories further organize these tests by application module:
        *   `tax/`: Unit tests for tax-related components (e.g., `TaxCalculator`, `GSTManager`).
        *   `utils/`: Unit tests for utility classes (e.g., `SequenceGenerator`) and Pydantic models.
        *   `services/`: Unit tests for service layer classes (e.g., `AccountService`, `BankReconciliationService`, `CustomerService`, etc.). This directory contains a comprehensive suite of tests for various data access and business support services.
        *   `reporting/`: Unit tests for reporting logic components (e.g., `DashboardManager`, `FinancialStatementGenerator`).
        *   Other directories like `accounting/`, `business_logic/`, `core/` are placeholders for future unit tests related to those specific manager layers or core components if not covered under services or other categories.

*   **`tests/integration/`**:
    *   Contains integration tests that verify interactions between multiple components. These tests might involve a real (test) database to ensure components work together correctly.
    *   Currently, a basic structure (`__init__.py`, `test_example_integration.py`) exists, with more comprehensive integration tests planned.

*   **`tests/ui/`**:
    *   Intended for UI-level functional tests, likely using frameworks like `pytest-qt`.
    *   Currently, a basic structure (`__init__.py`, `test_example_ui.py`) exists, with UI test implementation planned for the future.

## 3. Running Tests

All tests are run using `pytest` from the root directory of the project. Ensure your Poetry virtual environment is activated (e.g., by running `poetry shell` in the project root) or prepend commands with `poetry run`.

### 3.1. Running All Tests

To run all discovered tests (unit, integration, UI):

```bash
poetry run pytest
```
Or, if your Poetry shell is activated:
```bash
pytest
```

### 3.2. Running Specific Test Files or Directories

You can target specific parts of the test suite:

*   Run all tests in a directory (e.g., `tests/unit/services/`):
    ```bash
    poetry run pytest tests/unit/services/
    ```
*   Run a specific test file (e.g., `tests/unit/tax/test_tax_calculator.py`):
    ```bash
    poetry run pytest tests/unit/tax/test_tax_calculator.py
    ```
*   Run a specific test function within a file using `::test_function_name`:
    ```bash
    poetry run pytest tests/unit/tax/test_tax_calculator.py::test_calculate_line_tax_gst_standard_rate
    ```
*   Run tests based on markers (if defined in tests, e.g., `@pytest.mark.slow`):
    ```bash
    poetry run pytest -m slow
    ```

### 3.3. Test Verbosity

For more detailed output from pytest:

*   Show individual test names as they run:
    ```bash
    poetry run pytest -v
    ```
*   Show even more verbose output, including captured standard output from tests:
    ```bash
    poetry run pytest -vv
    ```

### 3.4. Test Coverage

To generate a test coverage report (requires the `pytest-cov` plugin, which is included in dev dependencies):

*   Print a coverage summary to the console for the `app` directory:
    ```bash
    poetry run pytest --cov=app tests/
    ```
*   Generate an HTML coverage report for a more detailed, browsable view:
    ```bash
    poetry run pytest --cov=app --cov-report=html tests/
    ```
    This will create an `htmlcov/` directory in your project root. Open `htmlcov/index.html` in a web browser to view the report.

### 3.5. Running Asynchronous Tests

Tests involving `async def` functions are automatically discovered and run by `pytest` when `pytest-asyncio` is installed (it is a dev dependency). Typically, `pytest-asyncio` is configured with `asyncio_mode = auto` (often set in `pyproject.toml` or `pytest.ini`, or as a default), which handles most asynchronous test cases seamlessly.

## 4. Viewing Test Results

Pytest provides immediate feedback in the console:
*   `.` (dot): Indicates a passed test.
*   `F`: Indicates a test that failed an assertion.
*   `E`: Indicates an error occurred during test setup or execution (not an assertion failure).
*   `s`: Indicates a skipped test (e.g., marked with `@pytest.mark.skip` or `pytest.skip()`).
*   `x`: Indicates an "expected failure" (marked with `@pytest.mark.xfail`).

For `F` and `E` results, pytest will print detailed information, including tracebacks and assertion differences, to help diagnose the issue.

## 5. Writing New Tests

When adding new tests, adhere to the following conventions:

*   **Location**:
    *   Place new unit tests in the appropriate subdirectory under `tests/unit/` (e.g., a new service test in `tests/unit/services/`).
    *   Integration tests go into `tests/integration/`.
    *   UI tests go into `tests/ui/`.
*   **File Naming**: Test files should start with `test_` (e.g., `test_my_new_feature.py`).
*   **Function Naming**: Test functions should start with `test_` (e.g., `def test_specific_behavior():`).
*   **Class Naming**: If using classes to group tests, class names should start with `Test` (e.g., `class TestMyComponent:`).
*   **Fixtures**: Utilize `pytest` fixtures (defined in `conftest.py` or locally in test files) for setting up test preconditions and managing resources.
*   **Assertions**: Use standard Python `assert` statements for checks.
*   **Expected Exceptions**: To test for expected exceptions, use `with pytest.raises(ExceptionType):`.
*   **Asynchronous Tests**: For testing asynchronous code, define test functions with `async def`.
*   **Mocking**: For unit tests, isolate the component under test by mocking its external dependencies. The `unittest.mock` library (providing `Mock`, `MagicMock`, `AsyncMock`, `patch`) is commonly used for this.

By following these guidelines, we aim to build and maintain a comprehensive and robust suite of automated tests, ensuring the quality and stability of the SG Bookkeeper application.
```

