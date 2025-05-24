1.  **Re-initialize Database**: Since `initial_data.sql` has significant changes (especially the order of inserts and column names), a clean initialization is highly recommended.
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password PGAdmin1234 --dbname sg_bookkeeper --drop-existing
    ```
2.  **Re-grant Privileges**: After the database is re-initialized, you'll need to re-grant permissions to your `sgbookkeeper_user` as the `postgres` user (the same `GRANT` statements as before).
    reference `create_database_user.sql`

3.  **Run the Application**:
    ```bash   
    poetry run sg_bookkeeper
    ```

# sudo -u postgres PGPASSWORD=PGAdmin1234 psql -h localhost -d sg_bookkeeper -f scripts/initial_data.sql

$ cat ~/.config/SGBookkeeper/config.ini 
[Database]
username = sgbookkeeper_user
password = SGkeeperPass123
host = localhost
port = 5432
database = sg_bookkeeper
echo_sql = False

$ cat ~/.config/SGBookkeeperOrg/SGBookkeeper.conf 
[MainWindow]
geometry=@ByteArray(\x1\xd9\xd0\xcb\0\x3\0\0\0\0\0\0\0\0\0\0\0\0\x4\xff\0\0\x3\x1f\0\0\0\0\0\0\0\0\0\0\x4\xff\0\0\x3\x1f\0\0\0\0\0\0\0\0\a\x80\0\0\0\0\0\0\0\0\0\0\x4\xff\0\0\x3\x1f)
state=@ByteArray(\0\0\0\xff\0\0\0\0\xfd\0\0\0\0\0\0\x5\0\0\0\x2\xb0\0\0\0\x4\0\0\0\x4\0\0\0\b\0\0\0\b\xfc\0\0\0\x1\0\0\0\x2\0\0\0\x1\0\0\0\x16\0M\0\x61\0i\0n\0T\0o\0o\0l\0\x62\0\x61\0r\x1\0\0\0\0\xff\xff\xff\xff\0\0\0\0\0\0\0\0)

