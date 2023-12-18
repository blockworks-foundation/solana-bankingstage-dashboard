import pg8000
from dbutils.pooled_db import PooledDB
import ssl
import time
from os import environ

# keep default threadsafety
# If the underlying DB-API module is not thread-safe,
# thread locks will be used to ensure that the pooled_db connections are thread-safe.
# So you don't need to worry about that, but you should be careful to use dedicated
# connections whenever you change the database session or perform transactions spreading over more than one SQL command.

def _configure_sslcontext():
    if environ.get('PGSSL', 'false') == 'true':
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = False
        ssl_context.load_verify_locations("ca.cer")
        ssl_context.load_cert_chain("client.cer", keyfile="client-key.cer")
        return ssl_context
    else:
        return None


# see https://webwareforpython.github.io/DBUtils/main.html#pooleddb-pooled-db
def _init_pool():
    print("Setting up database connection pool...")
    pool_size = int(environ.get('POOLED_DB_MAX_SIZE', '4'))
    username = environ.get('PGUSER', 'mev_dashboard_query_user')
    password = environ.get('PGPASSWORD')
    assert password is not None, "PGPASSWORD environment variable must be set"
    host = environ.get('PGHOST', 'localhost')
    port = environ.get('PGPORT', '5432')
    database = environ.get('PGDATABASE', 'mangolana')
    ssl_context = _configure_sslcontext()
    if ssl_context is not None:
        print("... use SSL for database connection")
    application_name = "bankingstage-dashboard"
    timeout = 10

    # note: for some unknown reason, database sees maxconnections+1 connections
    the_pool = PooledDB(pg8000, maxconnections=pool_size, blocking=True, maxusage=100,
                    database=database, user=username, password=password, host=host, port=port,
                    application_name=application_name, timeout=timeout, ssl_context=ssl_context)
    print("Initialized database connection pool with size ", pool_size)
    return the_pool


pool = _init_pool()


def query(statement, args=[]):
    start = time.time()

    with pool.connection() as db:
        with db.cursor() as cursor:
            try:
                elapsed_connect_ms = (time.time() - start) * 1000
                cursor.execute(statement, args=args)
                elapsed_total_ms = (time.time() - start) * 1000
                keys = [k[0] for k in cursor.description]
                maprows = [dict(zip(keys, row)) for row in cursor]
            except Exception as ex:
                print("Exception executing statement:", ex, statement)
                raise ex

    if elapsed_total_ms > 400:
        print("SLOW Database Query took", "%.2fms" % elapsed_total_ms, "(conn=" + "%.2f" % elapsed_connect_ms + "ms)")
    else:
        print("Database Query took", "%.2fms" % elapsed_total_ms, "(conn=" + "%.2f" % elapsed_connect_ms + "ms)")

    return maprows

