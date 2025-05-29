# Technical Design Specification Document: SG Bookkeeper (v9)

**Version:** 9.0
**Date:** 2025-05-29 <!-- Or current date -->

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 9, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities. This version specifically details the addition of comprehensive **User and Role Management capabilities (including Permission Assignment to Roles)**, alongside previously documented features like Sales Invoicing (Drafts & Posting), Customer, Vendor, Product/Service Management, GST F5 workflow, and Financial Reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Alignment with `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend.
-   Core Business Logic: Component structures, including those for business entity management and system administration (Users, Roles).
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, authorization (RBAC with UI for User/Role/Permission management), and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting implemented features, including the new User and Role Management UI.

### 1.3 Intended Audience
(Remains the same as TDS v8)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It provides comprehensive accounting for Singaporean SMBs, including double-entry bookkeeping, GST management, interactive financial reporting, modules for business operations (Customer, Vendor, Product/Service, Sales Invoicing), and robust system administration features for managing Users, Roles, and Permissions. The application emphasizes data integrity, compliance, and user-friendliness. Data structures are defined in `scripts/schema.sql` and seeded by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram and core description remain the same as TDS v8)

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
-   **`SecurityManager` (`app/core/security_manager.py`) (Enhanced)**: Now includes comprehensive methods for:
    -   User CRUD: `get_all_users_summary`, `get_user_by_id_for_edit`, `create_user_with_roles` (handles DTO, password hashing, role assignment), `update_user_from_dto` (handles user details and role updates), `toggle_user_active_status`, `change_user_password`.
    -   Role CRUD: `get_all_roles`, `get_role_by_id` (eager loads permissions), `create_role` (handles name, description, permission assignment), `update_role` (handles details and permission reassignment), `delete_role` (with checks for assignments and protected roles).
    -   Permission Listing: `get_all_permissions`.
-   Other core components (`Application`, `ApplicationCore`, `ConfigManager`, `DatabaseManager`, `ModuleManager`) descriptions remain largely the same, with `ApplicationCore` providing access to the enhanced `SecurityManager`.

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same as TDS v8)

#### 2.2.3 Services (`app/services/`)
(No new services added specifically for User/Role management beyond what `SecurityManager` uses from ORM directly or existing core services. `CoreServices` like `UserService`, `RoleService` could be abstracted later if `SecurityManager` becomes too large, but currently, it manages these ORM interactions directly.)

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
(No changes to existing managers. `SecurityManager` acts as the "manager" for user/role/permission logic directly interacting with ORM models or basic services if any were used.)

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: Contains "Settings" tab.
-   **`SettingsWidget` (`app/ui/settings/settings_widget.py`) (Enhanced)**:
    -   Now uses a `QTabWidget` to organize settings into "Company", "Fiscal Years", "Users", and "Roles & Permissions".
    -   Hosts `UserManagementWidget` and `RoleManagementWidget` in their respective tabs.
-   **User Management UI (`app/ui/settings/`)**:
    -   **`UserManagementWidget` (New)**: Provides a `QTableView` (using `UserTableModel`) to list users. Includes a toolbar with "Add User", "Edit User", "Toggle Active", "Change Password", and "Refresh" actions. Interacts with `UserDialog`, `UserPasswordDialog`, and `SecurityManager`.
    -   **`UserTableModel` (New)**: `QAbstractTableModel` for displaying `UserSummaryData`.
    -   **`UserDialog` (New)**: `QDialog` for adding/editing user details (username, full name, email, active status) and assigning roles via a multi-select `QListWidget`. Handles password input for new users.
    -   **`UserPasswordDialog` (New)**: `QDialog` for changing a selected user's password.
-   **Role Management UI (`app/ui/settings/`)**:
    -   **`RoleManagementWidget` (New)**: Provides a `QTableView` (using `RoleTableModel`) to list roles. Includes a toolbar with "Add Role", "Edit Role", "Delete Role", and "Refresh" actions. Interacts with `RoleDialog` and `SecurityManager`.
    -   **`RoleTableModel` (New)**: `QAbstractTableModel` for displaying `RoleData`.
    -   **`RoleDialog` (New)**: `QDialog` for adding/editing role name and description. Critically, includes a multi-select `QListWidget` to display all system permissions and allows assigning/unassigning them to the role. Special handling for "Administrator" role (name read-only, all permissions selected and disabled).
-   Other module widgets (`AccountingWidget`, `SalesInvoicesWidget`, etc.) remain as per TDS v8.

### 2.3 Technology Stack
(Same as TDS v8)

### 2.4 Design Patterns
(Same as TDS v8. New User/Role management UI follows established patterns of async data loading, DTOs for data transfer, and manager interaction.)

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent. `core.users`, `core.roles`, `core.permissions`, `core.user_roles`, `core.role_permissions` tables are now actively managed via the UI.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(`app/models/core/user.py` defining `User`, `Role`, `Permission` and their many-to-many relationships via `user_roles_table` and `role_permissions_table` is central to this update.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
The following DTOs related to User and Role Management are now actively used:
-   **User DTOs**: `UserSummaryData`, `UserBaseData`, `UserCreateData` (with password validation), `UserUpdateData`, `UserPasswordChangeData`, `UserRoleAssignmentData`, `UserCreateInternalData`.
-   **Role DTOs**: `RoleData`, `RoleCreateData` (includes `permission_ids`), `RoleUpdateData` (includes `permission_ids`).
-   **Permission DTO**: `PermissionData`.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
(No new *repository interfaces* were strictly added for User/Role management as `SecurityManager` currently handles these ORM operations directly. If abstracted, `IUserRepository`, `IRoleRepository`, `IPermissionRepository` could be defined.)

## 4. Module and Component Specifications

### 4.1 - 4.4 Core Accounting, Tax, Reporting, Business Operations Modules
(Functionality as detailed in TDS v8 remains current.)

### 4.5 System Administration Modules (New Section, or expansion of Security)

#### 4.5.1 User Management Module (Backend and UI Implemented)
This module allows administrators to manage user accounts.
-   **Manager (`app/core/security_manager.py`)**:
    -   Handles fetching user summaries (`get_all_users_summary`).
    -   Fetches full user details with roles for editing (`get_user_by_id_for_edit`).
    -   Creates new users, including password hashing and role assignments (`create_user_with_roles` using `UserCreateData`).
    -   Updates existing user details and role assignments (`update_user_from_dto` using `UserUpdateData`).
    -   Toggles user active status (`toggle_user_active_status`) with safety checks (cannot deactivate self or last admin).
    -   Changes user passwords (`change_user_password` using `UserPasswordChangeData`).
-   **UI (`app/ui/settings/user_management_widget.py`, `user_dialog.py`, `user_password_dialog.py`)**:
    -   `UserManagementWidget`: Displays users in `UserTableModel`. Toolbar provides Add, Edit, Toggle Active, Change Password actions.
    -   `UserDialog`: Form for user details (username, full name, email, active). Password fields for new users. `QListWidget` for multi-selecting roles to assign.
    -   `UserPasswordDialog`: Simple dialog to input and confirm new password for a selected user.

#### 4.5.2 Role & Permission Management Module (Backend and UI Implemented)
This module allows administrators to manage roles and their associated permissions.
-   **Manager (`app/core/security_manager.py`)**:
    -   Handles fetching all roles (`get_all_roles` - ORM returned, DTO mapping in UI widget).
    -   Fetches a specific role with its assigned permissions (`get_role_by_id`).
    -   Creates new roles, including assigning selected permissions (`create_role` using `RoleCreateData`).
    -   Updates existing role names, descriptions, and re-assigns permissions (`update_role` using `RoleUpdateData`).
    -   Deletes roles (`delete_role`) with checks (cannot delete "Administrator", cannot delete if assigned to users).
    -   Fetches all available system permissions (`get_all_permissions` returning `List[PermissionData]`).
-   **UI (`app/ui/settings/role_management_widget.py`, `role_dialog.py`)**:
    -   `RoleManagementWidget`: Displays roles in `RoleTableModel`. Toolbar provides Add, Edit, Delete actions.
    -   `RoleDialog`: Form for role name and description. `QListWidget` (multi-select) displays all system permissions (module: code - description) allowing an admin to check/uncheck permissions for the role. Special handling for "Administrator" role (name read-only, all permissions selected and list disabled).

## 5. User Interface Implementation (`app/ui/`)

### 5.1 - 5.5 Core UI, Accounting, Reports, Business Entity Modules
(Functionality as detailed in TDS v8.)

### 5.6 Settings Module UI (`app/ui/settings/settings_widget.py`) (Enhanced)
-   **`SettingsWidget`**:
    -   Now structured with a `QTabWidget`.
    -   **"Company" Tab**: Contains company information settings (as before).
    -   **"Fiscal Years" Tab**: Contains fiscal year management (as before).
    -   **"Users" Tab (New)**: Hosts the `UserManagementWidget`.
        -   `UserManagementWidget`: Lists users in a `QTableView` via `UserTableModel`. Toolbar allows adding new users (launching `UserDialog`), editing selected users (launching `UserDialog`), toggling active status of selected users (with confirmation and safety checks), and changing a selected user's password (launching `UserPasswordDialog`).
        -   `UserDialog`: Collects username, full name, email, active status. For new users, collects password and confirmation. Includes a `QListWidget` populated with all available roles, allowing multi-selection for role assignment.
        -   `UserPasswordDialog`: Takes new password and confirmation for the selected user.
    -   **"Roles & Permissions" Tab (New)**: Hosts the `RoleManagementWidget`.
        -   `RoleManagementWidget`: Lists roles in a `QTableView` via `RoleTableModel`. Toolbar allows adding new roles (launching `RoleDialog`), editing selected roles (launching `RoleDialog`), and deleting selected roles (with confirmation and safety checks like not deleting "Administrator" or roles in use).
        -   `RoleDialog`: Collects role name and description. Includes a `QListWidget` populated with all system permissions, allowing multi-selection to assign permissions to the role. The "Administrator" role's name is read-only, and its permissions list is shown as all selected and disabled.

## 6. Security Considerations (Enhanced)
-   The RBAC system is now fully manageable through the UI.
-   `SecurityManager` provides backend logic for all user and role CRUD operations, including password hashing and permission assignments.
-   Protection mechanisms are in place to prevent deactivating/deleting critical users (self, last admin) or roles ("Administrator").
-   Audit trails continue to log changes, now including user/role modifications if audit triggers cover `core.users`, `core.roles`, `core.user_roles`, `core.role_permissions`.

## 7. Database Access Implementation (`app/services/`)
(No new *services* directly for User/Role management, as `SecurityManager` handles these. `SecurityManager` itself uses `DatabaseManager` for sessions and SQLAlchemy ORM operations on `User`, `Role`, `Permission` models.)

## 8. Deployment and Installation
(Unchanged from TDS v8. `initial_data.sql` seeds default users, roles, permissions, and configurations which are now more critical.)

## 9. Conclusion
This TDS (v9) documents a significantly more mature SG Bookkeeper application with comprehensive User and Role Management capabilities integrated into the Settings UI. Administrators can now manage user accounts, define custom roles, and assign granular permissions to these roles, providing a robust security framework. This complements the strong accounting and business entity management features. Future work will continue to build out transactional modules and enhance reporting.
