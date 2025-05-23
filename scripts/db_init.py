# File: scripts/db_init.py
import asyncio
import asyncpg # type: ignore
import argparse
import getpass
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_SQL_PATH = SCRIPT_DIR / 'schema.sql'
INITIAL_DATA_SQL_PATH = SCRIPT_DIR / 'initial_data.sql'

async def create_database(args):
    """Create PostgreSQL database and initialize schema using reference SQL files."""
    conn = None 
    db_conn = None # Connection to the target database
    try:
        conn_params_admin = { # Parameters for connecting to 'postgres' db
            "user": args.user,
            "password": args.password,
            "host": args.host,
            "port": args.port,
        }
        conn = await asyncpg.connect(**conn_params_admin, database='postgres') # type: ignore
    except Exception as e:
        print(f"Error connecting to PostgreSQL server (postgres DB): {e}", file=sys.stderr)
        return False
    
    try:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Terminating connections to '{args.dbname}'...")
                # It's safer to run pg_terminate_backend on the 'postgres' db or another admin db
                # rather than the db being dropped, if possible.
                await conn.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{args.dbname}' AND pid <> pg_backend_pid();
                """)
                print(f"Dropping existing database '{args.dbname}'...")
                await conn.execute(f"DROP DATABASE IF EXISTS \"{args.dbname}\"") 
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                await conn.close()
                return False 
        
        print(f"Creating database '{args.dbname}'...")
        await conn.execute(f"CREATE DATABASE \"{args.dbname}\"") 
        
        await conn.close() # Close admin connection
        conn = None # Ensure it's not reused accidentally
        
        # Connect to the newly created database
        conn_params_db = {**conn_params_admin, "database": args.dbname}
        db_conn = await asyncpg.connect(**conn_params_db) # type: ignore
        
        if not SCHEMA_SQL_PATH.exists():
            print(f"Error: schema.sql not found at {SCHEMA_SQL_PATH}", file=sys.stderr)
            return False # db_conn will be closed in finally
            
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
        # The ALTER DATABASE command should ideally be run by a superuser,
        # or the database owner. The user running db_init.py (args.user) is assumed to have these rights.
        # It's better to run this on the specific DB connection (db_conn) if it has enough privileges,
        # or briefly reconnect as admin user if necessary, though ALTER DATABASE itself is not session-specific.
        # For simplicity, using db_conn which is connected to args.dbname as args.user.
        await db_conn.execute(f"""
            ALTER DATABASE "{args.dbname}" 
            SET search_path TO core, accounting, business, audit, public;
        """)
        print("Default search_path set.")
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error during database creation/initialization: {e}", file=sys.stderr)
        # Attempt to print more detailed asyncpg error if possible
        if isinstance(e, asyncpg.PostgresError):
            print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr)
            print(f"  Details: {e.details}", file=sys.stderr)
            print(f"  Query: {e.query}", file=sys.stderr) # Might be None for script execution
            print(f"  Position: {e.position}", file=sys.stderr)
        return False
    
    finally:
        if conn and not conn.is_closed():
            await conn.close()
        if db_conn and not db_conn.is_closed():
            await db_conn.close()

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize SG Bookkeeper database from reference SQL files.')
    parser.add_argument('--host', default=os.getenv('PGHOST', 'localhost'), help='PostgreSQL server host (Env: PGHOST)')
    parser.add_argument('--port', type=int, default=os.getenv('PGPORT', 5432), help='PostgreSQL server port (Env: PGPORT)')
    parser.add_argument('--user', default=os.getenv('PGUSER', 'postgres'), help='PostgreSQL username (Env: PGUSER)')
    parser.add_argument('--password', help='PostgreSQL password (Env: PGPASSWORD, or prompts if empty)')
    parser.add_argument('--dbname', default=os.getenv('PGDATABASE', 'sg_bookkeeper'), help='Database name (Env: PGDATABASE)')
    parser.add_argument('--drop-existing', action='store_true', help='Drop database if it already exists')
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not args.password:
        pgpassword_env = os.getenv('PGPASSWORD')
        if pgpassword_env:
            args.password = pgpassword_env
        else:
            try:
                args.password = getpass.getpass(f"Password for PostgreSQL user '{args.user}' on host '{args.host}': ")
            except (EOFError, KeyboardInterrupt): 
                print("\nPassword prompt cancelled or non-interactive environment. Exiting.", file=sys.stderr)
                sys.exit(1)
            except Exception as e: # Catch potential getpass.GetPassWarning if sys.stdin is not a tty
                print(f"Could not read password securely: {e}. Try setting PGPASSWORD environment variable or using --password.", file=sys.stderr)
                sys.exit(1)


    try:
        success = asyncio.run(create_database(args))
    except KeyboardInterrupt:
        print("\nDatabase initialization cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred in main: {e}", file=sys.stderr)
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
