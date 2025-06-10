# File: app/core/company_manager.py
import json
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING
import os
import sys

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CompanyManager:
    """Manages the central registry of company database files."""
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        if os.name == 'nt':
            config_dir = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / "SGBookkeeper"
        elif sys.platform == 'darwin':
            config_dir = Path.home() / 'Library' / 'Application Support' / "SGBookkeeper"
        else:
            config_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / "SGBookkeeper"
        
        os.makedirs(config_dir, exist_ok=True)
        self.registry_file = config_dir / "companies.json"
        
        self._companies: List[Dict[str, str]] = self._load_registry()

    def _load_registry(self) -> List[Dict[str, str]]:
        if not self.registry_file.exists():
            return []
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, IOError):
            return []

    def _save_registry(self):
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._companies, f, indent=2)
        except IOError as e:
            self.app_core.logger.error(f"Failed to save company registry to {self.registry_file}: {e}")
            # In a real UI app, we'd show an error dialog here.
            # For now, logging is sufficient.

    def get_company_list(self) -> List[Dict[str, str]]:
        """Returns a copy of the company list."""
        return list(self._companies)

    def add_company(self, company_info: Dict[str, str]):
        """Adds a new company to the registry if it doesn't already exist."""
        if not all(k in company_info for k in ['display_name', 'database_name']):
            raise ValueError("Company info must contain 'display_name' and 'database_name'.")
        
        # Check for duplicates based on database_name
        if any(c['database_name'] == company_info['database_name'] for c in self._companies):
            self.app_core.logger.warning(f"Attempted to add duplicate company database '{company_info['database_name']}'. Ignoring.")
            return

        self._companies.append(company_info)
        self._save_registry()

    def remove_company(self, company_info: Dict[str, str]):
        """Removes a company from the registry based on its database_name."""
        db_name_to_remove = company_info.get("database_name")
        if not db_name_to_remove:
            return

        original_count = len(self._companies)
        self._companies = [c for c in self._companies if c.get("database_name") != db_name_to_remove]
        
        if len(self._companies) < original_count:
            self._save_registry()
            
    def get_company_by_db_name(self, db_name: str) -> Optional[Dict[str, str]]:
        """Finds a company by its database name."""
        return next((c for c in self._companies if c.get("database_name") == db_name), None)
