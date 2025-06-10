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

---
https://drive.google.com/file/d/160xDsKvPVAoauLYynWiBe9NHBnZdTL8J/view?usp=sharing, https://drive.google.com/file/d/18TtNiuwMgTDNao0zAFm09n-jytG2YUGz/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221C3YLnRKPRGzPZnYLR1QTk7UWEwAsh3Nz%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1Ca9966PXKMDnjAxCsyT8OmVM2CPRlb-7/view?usp=sharing, https://drive.google.com/file/d/1JQqsPW16CEQ_KOYug004UPmNUP8BkdJ-/view?usp=sharing, https://drive.google.com/file/d/1Uej9gO7t12EkmldGnw5jk_V_fDjhTJMw/view?usp=sharing, https://drive.google.com/file/d/1ZsmOW6huYvGv9eyPviU1VZzh2YZqtxgW/view?usp=sharing, https://drive.google.com/file/d/1azUf7bWoZO_Niu3T7P81Vg8osVNEAvdG/view?usp=sharing, https://drive.google.com/file/d/1bI33CCtQPwhzoEUl854m3V002dxflsWg/view?usp=sharing, https://drive.google.com/file/d/1eFLuD4rI0YIctcHcXtE_aGXdEI19KS7A/view?usp=sharing, https://drive.google.com/file/d/1i0d3rPoQdMDESiN3d1xl0HwlhxsW8IKA/view?usp=sharing, https://drive.google.com/file/d/1peEbFNwTqJse_rI4-Cr6AHJC5VkdMEyJ/view?usp=sharing, https://drive.google.com/file/d/1wiAxnIzKK89xeuNXnUIwze7jX3IRpmh0/view?usp=sharing, https://drive.google.com/file/d/1y5m17YgZHBbDTW-m13LysnRiD55hfuaG/view?usp=sharing, https://drive.google.com/file/d/1z8Ad5AKfM2zETmgHi_8lWviUGZCQl1bF/view?usp=sharing

