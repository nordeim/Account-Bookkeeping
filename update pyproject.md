**1. Update `pyproject.toml`**

```toml
# pyproject.toml
[tool.poetry]
name = "sg-bookkeeper"
version = "1.0.0"
description = "Singapore small business bookkeeping application"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/yourusername/sg_bookkeeper"
repository = "https://github.com/yourusername/sg_bookkeeper"
keywords = ["accounting", "bookkeeping", "singapore", "gst", "tax"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12", 
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: Office/Business :: Financial :: Accounting",
]
packages = [{include = "app", from = "."}]

[tool.poetry.dependencies]
python = ">=3.9,<3.13" 
PySide6 = "^6.9.0"   
SQLAlchemy = {extras = ["asyncio"], version = ">=2.0.0"}
asyncpg = ">=0.25.0"
alembic = ">=1.7.5"
# Changed pydantic line below
pydantic = {version = "^2.0", extras = ["email"]}
reportlab = ">=3.6.6"
openpyxl = ">=3.0.9"
python-dateutil = ">=2.8.2"
bcrypt = ">=3.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
flake8 = "^6.0"
black = "^24.0" 
mypy = "^1.0" 
pre-commit = "^3.0"
pytest-qt = "^4.0"
pytest-asyncio = "^0.21.0" 

[tool.poetry.scripts]
sg_bookkeeper = "app.main:main"
sg_bookkeeper_db_init = "scripts.db_init:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.pytest.ini_options]
python_files = "test_*.py tests.py" 
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
```

**Validation of `pyproject.toml` changes:**
*   The line `pydantic = "^2.0"` has been changed to `pydantic = {version = "^2.0", extras = ["email"]}`. This tells Poetry to install Pydantic along with the dependencies required for email validation (which is the `email-validator` package).
*   No other parts of the file were altered.

---

**Next Steps for You:**

1.  **Replace your `pyproject.toml`** with the content provided above.
2.  **Open your terminal in the project root directory (`SG-Bookkeeper`) where `pyproject.toml` is located.**
3.  **Run the following Poetry commands:**
    *   To update the lock file based on the changes in `pyproject.toml` and install the new dependency:
        ```bash
        poetry lock
        poetry install
        ```
    *   Alternatively, `poetry update pydantic` might also resolve this by picking up the "extras" change and installing `email-validator`. However, `poetry lock && poetry install` is more explicit for ensuring the environment matches the `pyproject.toml`.

After these commands complete successfully, the `email-validator` package will be installed in your project's virtual environment. You should then be able to run `poetry run sg_bookkeeper` without encountering the `ImportError`.

