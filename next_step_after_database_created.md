**Next Steps:**

# /usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/16/main -c config_file=/etc/postgresql/16/main/postgresql.conf

1.  Replace your `scripts/initial_data.sql` with the updated version provided above.
2.  **Re-run the database initialization script** to apply these changes and seed the company settings (and ensure the admin user is set up):
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password PGAdmin1234 --dbname sg_bookkeeper --drop-existing
    ```
    *(Using `--drop-existing` ensures a clean state with the new initial data. If you have important data already, back it up or apply changes manually.)*
3.  After `db_init.py` completes successfully, grant permissions to `sgbookkeeper_user` again (as the database was dropped and recreated):
    ```bash
    sudo -u postgres PGPASSWORD=PGAdmin1234 psql -h localhost -d sg_bookkeeper
    ```
    Then run the `GRANT` commands from the previous step.

**Critical Missing Grant Step:**
The user `sgbookkeeper_user` needs `USAGE` on schemas and `SELECT, INSERT, UPDATE, DELETE` (etc.) on tables.
`GRANT ALL PRIVILEGES ON DATABASE` gives `CONNECT`, `CREATE` (schemas/temp tables), `TEMPORARY`. It does *not* grant rights to objects within the database unless the user owns them.

So, after `db_init.py` (run by `postgres`) creates everything, these grants are needed for `sgbookkeeper_user`:
```sql
-- Run as postgres user
-- create application user
CREATE USER sgbookkeeper_user WITH PASSWORD 'SGkeeperPass123';
-- grant user privileges
GRANT ALL PRIVILEGES ON DATABASE sg_bookkeeper TO sgbookkeeper_user;
-- connect to application specific database
\c sg_bookkeeper

GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;
-- For sequences (needed for INSERTs if app uses them directly or via default values)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
-- Grant privileges for future tables too
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA accounting GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA business GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
```
This is a crucial part of setting up a non-superuser role.

The `db_init.py` script could be enhanced to optionally take a `--app-user` and `--app-password` and then, after schema creation by the admin user, grant these privileges.
For now, the user needs to run these grants manually as the `postgres` user.

So, the next steps for the user *before* running the application with `sgbookkeeper_user` should be:
1.  Connect to `sg_bookkeeper` database as `postgres` user.
2.  Execute the `GRANT` statements listed above.


4.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

---
The user has successfully created a dedicated PostgreSQL user `sgbookkeeper_user` and granted it privileges on the `sg_bookkeeper` database. They've also updated their local `config.ini` file with these new credentials.

The database `sg_bookkeeper` was previously initialized successfully by `db_init.py` using the `postgres` superuser. The tables, views, functions, etc., are already in place.

**Current State:**
1.  PostgreSQL server is running.
2.  A dedicated user `sgbookkeeper_user` exists with `ALL PRIVILEGES` on the `sg_bookkeeper` database.
3.  The `sg_bookkeeper` database exists and has been fully populated with the schema and initial data (from the last successful run of `db_init.py`).
4.  The application's `config.ini` file (e.g., `~pete/.config/SGBookkeeper/config.ini`) is updated to use `sgbookkeeper_user` and its password.

**Reviewing `deployment_guide.md` for "Next Steps":**

The `deployment_guide.md` outlines these main steps:
1.  Obtain Code (Done)
2.  Install/Configure PostgreSQL (Done, user created)
3.  Setup Python Environment & Install Dependencies (Presumably done, as `db_init.py` was run via `poetry run`)
4.  Configure Database Connection (Done - `config.ini` updated)
5.  **Initialize the Database** (This step, using `poetry run sg_bookkeeper_db_init`, was already performed successfully with the `postgres` user).
6.  (Optional) Compile Qt Resources (Not strictly necessary to run)
7.  **Run the Application** (`poetry run sg_bookkeeper`)

**Considerations for the "Initialize the Database" step (Step 5):**
*   The database is *already* initialized. Re-running `poetry run sg_bookkeeper_db_init` is not strictly necessary unless there's a schema update or a desire to reset the data.
*   If the user were to re-run it *now*, the `db_init.py` script would connect using the credentials from `config.ini` (i.e., `sgbookkeeper_user`).
*   The `sgbookkeeper_user` was granted `ALL PRIVILEGES ON DATABASE sg_bookkeeper`. This typically includes permissions to create schemas and tables *within that database* if they don't exist.
*   However, operations like `DROP DATABASE` or `CREATE DATABASE` (which `db_init.py` attempts if `--drop-existing` is used or if the DB doesn't exist) usually require higher privileges than what `GRANT ALL PRIVILEGES ON DATABASE` provides. The `sgbookkeeper_user` typically wouldn't be a superuser and might not have `CREATEDB` attribute by default.
*   If `db_init.py` is run with `sgbookkeeper_user` *without* `--drop-existing`, and the database `sg_bookkeeper` already exists (which it does), the script will attempt to:
    *   Connect to `postgres` DB as `sgbookkeeper_user` (this needs to be allowed in `pg_hba.conf` for the user).
    *   Check if `sg_bookkeeper` DB exists (it does).
    *   It will then try to connect to `sg_bookkeeper` as `sgbookkeeper_user`.
    *   Then it will try to execute `schema.sql`. This involves `CREATE SCHEMA IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS` (implied by `CREATE TABLE`), `CREATE EXTENSION IF NOT EXISTS`.
        *   `CREATE SCHEMA IF NOT EXISTS core AUTHORIZATION sgbookkeeper_user;` might be better if the user should own the schemas. The current `CREATE SCHEMA IF NOT EXISTS core;` means the schemas will be owned by the user executing the command (sgbookkeeper_user). This is fine since this user has `ALL PRIVILEGES` on the database which includes `CREATE` privilege for schemas in that database.
        *   `CREATE EXTENSION` usually requires superuser privileges. If `sgbookkeeper_user` is not a superuser, this part of `schema.sql` might fail if the extensions aren't already present from the previous run by `postgres`. However, the extensions are already created by the previous `postgres` user run.
    *   The `ALTER DATABASE sg_bookkeeper SET search_path ...` command added to the updated `db_init.py` might also require ownership or superuser privileges. The database owner (which is `postgres` since `postgres` created it) or a superuser can run this. `sgbookkeeper_user` might not be able to if it's not the owner.

**Next Steps for the User:**

Since the database is already correctly initialized by the `postgres` user:

1.  **No need to re-run `db_init.py` *unless* they want the `ALTER DATABASE ... SET search_path` command (from the *updated* `db_init.py`) to be applied.**
    *   If they want to apply the `ALTER DATABASE ... SET search_path` using the `sgbookkeeper_user`: This user might not have permission. It's safer for the `postgres` user (or the database owner) to run this command once manually in `psql`, or for `db_init.py` to be run by the `postgres` user when this specific `ALTER DATABASE` command is involved.
    *   Alternatively, they can skip re-running `db_init.py` and just set the `search_path` in their `psql` sessions manually or configure their client tool if they need to browse the DB. The application itself will work because SQLAlchemy will use fully qualified names or the `search_path` set by `schema.sql` within its own session.

2.  **The primary next step is to run the application itself (Step 7 from the guide).**
    ```bash
    poetry run sg_bookkeeper
    ```
    The application will use the credentials from `config.ini` (`sgbookkeeper_user`) to connect to the already-initialized `sg_bookkeeper` database. Since `sgbookkeeper_user` has `ALL PRIVILEGES` on the database, it should be able to read and write to the tables created by the `postgres` user (as default table privileges usually allow the owner and users with database-level privileges to operate, or specific `GRANT`s would be needed if more restrictive).

**Recommendation for the User:**

*   **Option A (Simplest to run application):** Proceed directly to running the application. The database is ready.
    ```bash
    poetry run sg_bookkeeper
    ```
*   **Option B (To get the persistent `search_path` for the database using the new `db_init.py`):**
    Since `sgbookkeeper_user` might not have permission to `ALTER DATABASE` (if it's not the owner or superuser), and the database `sg_bookkeeper` is currently owned by `postgres`:
    1.  Temporarily revert `config.ini` to use the `postgres` user, or use command-line overrides with `db_init.py` to run as `postgres`.
    2.  Run the *updated* `db_init.py` (the one I provided in the previous step that includes `ALTER DATABASE ... SET search_path`). Crucially, run it *without* `--drop-existing` so it doesn't wipe the data.
        ```bash
        # Example assuming config.ini is still sgbookkeeper_user, so override:
        poetry run sg_bookkeeper_db_init --user postgres --password PGAdmin1234 --dbname sg_bookkeeper
        ```
        This run will skip DB creation, connect to the existing DB, re-run `schema.sql` (which is mostly idempotent with `IF NOT EXISTS`), re-run `initial_data.sql` (`ON CONFLICT DO NOTHING` handles existing data), and importantly, execute the `ALTER DATABASE ... SET search_path` command as the `postgres` user.
    3.  Then, switch `config.ini` back to `sgbookkeeper_user` for running the main application.

    Option B is more for development convenience when using `psql`. For the application itself, Option A is sufficient.

Let's advise the user to try Option A first. If they frequently use `psql` and want the `search_path` set persistently for the database, they can consider Option B or manually run `ALTER DATABASE sg_bookkeeper SET search_path TO core, accounting, business, audit, public;` as the `postgres` user in `psql`.

The `db_init.py` script also has `SCRIPT_DIR = Path(__file__).resolve().parent` etc. So, if running poetry from project root, `scripts/db_init.py` would be `python scripts/db_init.py` if not using the entry point. The entry point is `sg_bookkeeper_db_init`.

The key is that the database content is already there. The `sgbookkeeper_user` just needs to be able to connect and use it. `GRANT ALL PRIVILEGES ON DATABASE sg_bookkeeper TO sgbookkeeper_user;` is good. We also need to ensure this user has privileges on the schemas and tables within. `ALL PRIVILEGES ON DATABASE` does not automatically grant all privileges on all objects *within* the database to a new user. The *owner* of the objects (schemas, tables - currently `postgres`) can access them. Other users need explicit grants.

**Critical Missing Grant Step:**
The user `sgbookkeeper_user` needs `USAGE` on schemas and `SELECT, INSERT, UPDATE, DELETE` (etc.) on tables.
`GRANT ALL PRIVILEGES ON DATABASE` gives `CONNECT`, `CREATE` (schemas/temp tables), `TEMPORARY`. It does *not* grant rights to objects within the database unless the user owns them.

So, after `db_init.py` (run by `postgres`) creates everything, these grants are needed for `sgbookkeeper_user`:
```sql
-- Run as postgres user
GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;
-- For sequences (needed for INSERTs if app uses them directly or via default values)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
-- Grant privileges for future tables too
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA accounting GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA business GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
```
This is a crucial part of setting up a non-superuser role.

The `db_init.py` script could be enhanced to optionally take a `--app-user` and `--app-password` and then, after schema creation by the admin user, grant these privileges.
For now, the user needs to run these grants manually as the `postgres` user.

So, the next steps for the user *before* running the application with `sgbookkeeper_user` should be:
1.  Connect to `sg_bookkeeper` database as `postgres` user.
2.  Execute the `GRANT` statements listed above.

After that, running `poetry run sg_bookkeeper` with `config.ini` pointing to `sgbookkeeper_user` should work.
The `record "old" has no field "entry_no"` error from the `db_init.py` previously is likely a red herring or a misreported context of the actual `record "new" has no field "created_by"` error that was occurring within the `schema.sql` execution at that time. Since `schema.sql` now completes, that specific error message from `db_init.py` should not reappear for the same reason.

---
You've successfully set up the dedicated PostgreSQL user `sgbookkeeper_user` and configured the application to use it via `config.ini`. Since the database `sg_bookkeeper` was already successfully initialized in the previous step (using the `postgres` superuser), you do **not** need to run `poetry run sg_bookkeeper_db_init` again *unless* you want to apply the `ALTER DATABASE ... SET search_path` modification from the updated `db_init.py` script I provided in the last step.

However, there's a **crucial step missing**: granting the necessary permissions to your new `sgbookkeeper_user` on the schemas and objects *within* the `sg_bookkeeper` database. The `GRANT ALL PRIVILEGES ON DATABASE sg_bookkeeper TO sgbookkeeper_user;` command allows the user to connect and create temporary tables, but it doesn't grant permissions to existing objects created by another user (in this case, `postgres`).

**Next Steps:**

**Step 1: Grant Privileges to `sgbookkeeper_user` (Crucial)**

You need to connect to the `sg_bookkeeper` database as the `postgres` user (or another superuser/owner of the objects) and execute the following `GRANT` statements. This will allow `sgbookkeeper_user` to read from and write to the tables, use schemas, etc.

```bash
sudo -u postgres PGPASSWORD=PGAdmin1234 psql -h localhost -d sg_bookkeeper
```

Once connected to the `sg_bookkeeper` database as `postgres`, run these commands:

```sql
-- Grant usage on schemas
GRANT USAGE ON SCHEMA core TO sgbookkeeper_user;
GRANT USAGE ON SCHEMA accounting TO sgbookkeeper_user;
GRANT USAGE ON SCHEMA business TO sgbookkeeper_user;
GRANT USAGE ON SCHEMA audit TO sgbookkeeper_user;

-- Grant DML privileges on existing tables in each schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;

-- Grant privileges on existing sequences (important for auto-incrementing IDs used by the app)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user;
-- Note: SERIAL columns automatically create sequences, usually in the same schema as the table.

-- Grant execute on functions (if your application calls them directly as sgbookkeeper_user)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;
-- Note: business schema currently has no functions in schema.sql

-- Set default privileges for future tables/sequences created by the 'postgres' user (or other roles)
-- This ensures sgbookkeeper_user will have access to them automatically.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;

-- Exit psql
\q
```

**Step 2: (Optional) Set Persistent `search_path` for the Database**

If you want the `search_path` to be set automatically for all new connections to `sg_bookkeeper` (including your `psql` sessions with `sgbookkeeper_user`), you have two options:

*   **Option 2a: Manually run the command as `postgres` user:**
    Connect to `psql` as `postgres` (can be any database, like `postgres` db itself) and run:
    ```sql
    ALTER DATABASE sg_bookkeeper SET search_path TO core, accounting, business, audit, public;
    ```
*   **Option 2b: Re-run the *updated* `db_init.py` script as `postgres` user (without `--drop-existing`):**
    If you've updated `scripts/db_init.py` with the `ALTER DATABASE ... SET search_path` command I provided in the previous response, you can run it. Make sure your `config.ini` temporarily points to the `postgres` user or use command-line overrides for `db_init.py` for this run.
    ```bash
    # Example assuming config.ini is for sgbookkeeper_user, so override:
    poetry run sg_bookkeeper_db_init --user postgres --password PGAdmin1234 --dbname sg_bookkeeper 
    ```
    This will re-apply the schema (idempotently) and initial data (idempotently due to `ON CONFLICT DO NOTHING`), and then execute the `ALTER DATABASE` command. Then, change `config.ini` back to `sgbookkeeper_user`.

**Step 3: Run the Application**

Now that the `sgbookkeeper_user` has the necessary permissions and your `config.ini` is correctly set up for this user, you can start the application:

```bash
poetry run sg_bookkeeper
```

The application should now connect as `sgbookkeeper_user` and be able to perform all necessary database operations.

**Summary of Next Steps for You:**
1.  **Crucial:** Execute the `GRANT` statements from **Step 1** above by connecting to the `sg_bookkeeper` database as the `postgres` user.
2.  **(Optional but Recommended for `psql` convenience):** Perform **Step 2** (either 2a or 2b) to set the persistent `search_path` for the database.
3.  **Run the application:** `poetry run sg_bookkeeper`.

