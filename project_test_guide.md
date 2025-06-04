# Project Test Guide: SG Bookkeeper

This guide provides instructions on how to set up the testing environment and run the automated tests for the SG Bookkeeper application.

## 1. Prerequisites

*   **Python Environment**: Ensure you have Python (version specified in `pyproject.toml`, e.g., 3.9+) and Poetry installed.
*   **Dependencies**: All development dependencies, including testing libraries (`pytest`, `pytest-asyncio`, `pytest-cov`, `unittest.mock`), should be installed. If you set up the project using `poetry install --with dev` or `poetry install` (if dev dependencies are not in a group), these should already be available in your project's virtual environment.

## 2. Test Structure

The tests are organized as follows:

*   **`tests/`**: Root directory for all tests.
    *   **`conftest.py`**: Contains project-wide pytest fixtures and configuration.
    *   **`unit/`**: Contains unit tests that test individual modules or classes in isolation.
        *   `tax/`: Unit tests for tax-related components (e.g., `TaxCalculator`).
        *   `utils/`: Unit tests for utility classes and Pydantic models.
        *   `services/`: Unit tests for service layer classes.
        *   *(Other subdirectories will be added as more unit tests are developed)*
    *   **`integration/`**: (Planned) Will contain integration tests that verify interactions between multiple components, often involving a test database.
    *   **`ui_tests/`**: (Planned) Will contain UI-level functional tests using `pytest-qt`.

## 3. Running Tests

All tests are run using `pytest` from the root directory of the project. Ensure your Poetry virtual environment is activated (`poetry shell`) or run commands with `poetry run`.

### 3.1. Running All Tests

To run all discovered tests (unit, integration, UI - though currently only unit tests are substantially implemented):

```bash
poetry run pytest
```
or if your shell is already activated:
```bash
pytest
```

### 3.2. Running Specific Test Files or Directories

You can target specific files or directories:

*   Run all tests in the `tests/unit/utils/` directory:
    ```bash
    poetry run pytest tests/unit/utils/
    ```
*   Run a specific test file:
    ```bash
    poetry run pytest tests/unit/tax/test_tax_calculator.py
    ```
*   Run a specific test function within a file using `::`:
    ```bash
    poetry run pytest tests/unit/tax/test_tax_calculator.py::test_calculate_line_tax_gst_standard_rate
    ```
*   Run tests based on markers (if defined, e.g., `@pytest.mark.slow`):
    ```bash
    poetry run pytest -m slow
    ```

### 3.3. Test Verbosity

For more detailed output (e.g., to see individual test names as they run):

```bash
poetry run pytest -v
```
For even more verbose output (including captured stdout):
```bash
poetry run pytest -vv
```

### 3.4. Test Coverage

To generate a test coverage report (requires `pytest-cov`):

```bash
poetry run pytest --cov=app tests/
```
This will run tests and then print a coverage summary to the console.

To generate an HTML coverage report for more detailed inspection:
```bash
poetry run pytest --cov=app --cov-report=html tests/
```
The HTML report will typically be generated in an `htmlcov/` directory. You can open `htmlcov/index.html` in a browser.

### 3.5. Running Asynchronous Tests

Tests involving `async def` functions are automatically handled by `pytest-asyncio` (which should be configured in `pyproject.toml` or `pytest.ini`). No special commands are usually needed beyond the standard `pytest` invocation.

## 4. Viewing Test Results

Pytest will output test results to the console:
*   `.` indicates a passed test.
*   `F` indicates a failed test.
*   `E` indicates an error during test execution (not an assertion failure).
*   `s` indicates a skipped test.
*   `x` indicates an expected failure (xfail).

Detailed information about failures and errors will be printed, including tracebacks.

## 5. Writing New Tests

*   Place new unit tests in the appropriate subdirectory under `tests/unit/`.
*   Test file names should start with `test_` (e.g., `test_my_module.py`).
*   Test function names should start with `test_` (e.g., `def test_my_function():`).
*   Test class names should start with `Test` (e.g., `class TestMyClass:`).
*   Use `pytest` fixtures for setup and teardown where appropriate.
*   Use standard `assert` statements for checks.
*   For expected exceptions, use `with pytest.raises(ExceptionType):`.
*   For asynchronous code, use `async def` for test functions and ensure `pytest-asyncio` is installed.
*   Mock external dependencies for unit tests using `unittest.mock` (`Mock`, `MagicMock`, `AsyncMock`, `patch`).

By following these guidelines, we can build and maintain a robust suite of automated tests for SG Bookkeeper.
