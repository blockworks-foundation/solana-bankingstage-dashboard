import pg8000
import time
import ssl
import copy
from os import environ
from dbutils.pooled_db import PooledDB


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
    pool_size = int(environ.get('POOLED_DB_MAX_SIZE', '4'))
    username = environ.get('PGUSER', 'mev_dashboard_query_user')
    password = environ.get('PGPASSWORD')
    assert password is not None, "PGPASSWORD environment variable must be set"
    host = environ.get('PGHOST', 'localhost')
    port = environ.get('PGPORT', '5432')
    database = environ.get('PGDATABASE', 'mangolana')
    ssl_context = _configure_sslcontext()
    application_name = "bankingstage-dashboard"
    the_pool = PooledDB(pg8000, pool_size,
                    database=database, user=username, password=password, host=host, port=port, application_name=application_name, ssl_context=ssl_context)
    print("Initialized database connection pool with size ", pool_size)
    return the_pool


pool = _init_pool()


def query(statement, args=[]):
    start = time.time()

    con = pool.connection()
    cursor = con.cursor()
    elapsed_connect = time.time() - start

    try:
        cursor.execute(statement, args=args)
        elapsed_total = time.time() - start
        keys = [k[0] for k in cursor.description]
        maprows = [dict(zip(keys, copy.deepcopy(row))) for row in cursor]
    except Exception as ex:
        print("Exception executing query:", ex)
        return []
    finally:
        cursor.close()
        con.close()

    if elapsed_total > .2:
        print("Database Query took", elapsed_total, "secs", "(", elapsed_connect, ")")

    return maprows

