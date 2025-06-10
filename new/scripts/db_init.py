# File: scripts/db_init.py
import asyncio
import asyncpg # type: ignore
import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import NamedTuple, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_SQL_PATH = SCRIPT_DIR / 'schema.sql'
INITIAL_DATA_SQL_PATH = SCRIPT_DIR / 'initial_data.sql'

class DBInitArgs(NamedTuple):
    """A simple data class to hold arguments for programmatic calls."""
    user: Optional[str]
    password: Optional[str]
    host: str
    port: int
    dbname: str
    drop_existing: bool = False

async def initialize_new_database(args: DBInitArgs) -> bool:
    """Create PostgreSQL database and initialize schema using reference SQL files."""
    conn_admin = None 
    db_conn = None 
    
    # Use environment variables or provided args for admin connection
    admin_user = args.user or os.getenv('PGUSER', 'postgres')
    admin_password = args.password or os.getenv('PGPASSWORD')

    if not admin_password:
        print(f"Error: Admin password for user '{admin_user}' is required for database creation but was not provided.", file=sys.stderr)
        # In a real app, this would be handled more gracefully, maybe by re-prompting if interactive.
        # For programmatic use, failing fast is better.
        return False

    try:
        conn_params_admin = { 
            "user": admin_user,
            "password": admin_password,
            "host": args.host,
            "port": args.port,
        }
        conn_admin = await asyncpg.connect(**conn_params_admin, database='postgres') 
    except Exception as e:
        print(f"Error connecting to PostgreSQL server (postgres DB): {type(e).__name__} - {str(e)}", file=sys.stderr)
        return False
    
    try:
        exists = await conn_admin.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Terminating connections to '{args.dbname}'...")
                await conn_admin.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{args.dbname}' AND pid <> pg_backend_pid();
                """)
                print(f"Dropping existing database '{args.dbname}'...")
                await conn_admin.execute(f"DROP DATABASE IF EXISTS \"{args.dbname}\"") 
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                await conn_admin.close()
                return False 
        
        print(f"Creating database '{args.dbname}'...")
        await conn_admin.execute(f"CREATE DATABASE \"{args.dbname}\"") 
        
        await conn_admin.close() 
        conn_admin = None 
        
        # Connect to the newly created database to run schema and data scripts
        conn_params_db = {**conn_params_admin, "database": args.dbname}
        db_conn = await asyncpg.connect(**conn_params_db) 
        
        if not SCHEMA_SQL_PATH.exists():
            print(f"Error: schema.sql not found at {SCHEMA_SQL_PATH}", file=sys.stderr)
            return False
            
        print(f"Initializing database schema from {SCHEMA_SQL_PATH}...")
        with open(SCHEMA_SQL_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        await db_conn.execute(schema_sql)
        print("Schema execution completed.")
        
        if not INITIAL_DATA_SQL_PATH.exists():
            print(f"Warning: initial_data.sql not found at {INITIAL_DATA_SQL_PATH}. Skipping initial data.", file=sys.stderr)
        else:
            print(f"Loading initial data from {INITIAL_DATA_SQL_PATH}...")
            with open(INITIAL_DATA_SQL_PATH, 'r', encoding='utf-8') as f:
                data_sql = f.read()
            await db_conn.execute(data_sql)
            print("Initial data loading completed.")

        print(f"Setting default search_path for database '{args.dbname}'...")
        await db_conn.execute(f"""
            ALTER DATABASE "{args.dbname}" 
            SET search_path TO core, accounting, business, audit, public;
        """)
        print("Default search_path set.")
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error during database creation/initialization: {type(e).__name__} - {str(e)}", file=sys.stderr)
        # Provide more detail for debugging asyncpg errors
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
            print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr)
        if hasattr(e, 'detail') and e.detail: # type: ignore
             print(f"  DETAIL: {e.detail}", file=sys.stderr)
        if hasattr(e, 'query') and e.query: # type: ignore
            print(f"  Query context: {e.query[:200]}...", file=sys.stderr)
        return False
    
    finally:
        if conn_admin and not conn_admin.is_closed():
            await conn_admin.close()
        if db_conn and not db_conn.is_closed():
            await db_conn.close()

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize SG Bookkeeper database from reference SQL files.')
    parser.add_argument('--host', default=os.getenv('PGHOST', 'localhost'), help='PostgreSQL server host (Env: PGHOST)')
    parser.add_argument('--port', type=int, default=os.getenv('PGPORT', 5432), help='PostgreSQL server port (Env: PGPORT)')
    parser.add_argument('--user', default=os.getenv('PGUSER', 'postgres'), help='PostgreSQL admin/superuser (Env: PGUSER)')
    parser.add_argument('--password', help='PostgreSQL admin/superuser password (Env: PGPASSWORD, or prompts if empty)')
    parser.add_argument('--dbname', default=os.getenv('PGDATABASE', 'sg_bookkeeper'), help='Database name to create (Env: PGDATABASE)')
    parser.add_argument('--drop-existing', action='store_true', help='Drop database if it already exists')
    return parser.parse_args()

def main():
    args = parse_args()
    
    password = args.password
    if not password:
        pgpassword_env = os.getenv('PGPASSWORD')
        if pgpassword_env:
            password = pgpassword_env
        else:
            try:
                password = getpass.getpass(f"Password for PostgreSQL user '{args.user}' on host '{args.host}': ")
            except (EOFError, KeyboardInterrupt): 
                print("\nPassword prompt cancelled or non-interactive environment. Exiting.", file=sys.stderr)
                sys.exit(1)
            except Exception as e: 
                print(f"Could not read password securely: {e}. Try setting PGPASSWORD environment variable or using --password.", file=sys.stderr)
                sys.exit(1)
    
    init_args = DBInitArgs(
        user=args.user,
        password=password,
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        drop_existing=args.drop_existing
    )

    try:
        success = asyncio.run(initialize_new_database(init_args))
    except KeyboardInterrupt:
        print("\nDatabase initialization cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred in main: {type(e).__name__} - {str(e)}", file=sys.stderr)
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
             print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr) 
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
