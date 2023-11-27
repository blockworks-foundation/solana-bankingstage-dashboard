import pg8000
import time
import ssl
from os import environ

def query(statement, args=[]):
    start = time.time()
    con = _create_new_connection()
    cursor = con.cursor()
    elapsed_connect = time.time() - start

    cursor.execute(statement, args=args)

    elapsed_total = time.time() - start

    keys = [k[0] for k in cursor.description]
    maprows = [dict(zip(keys, row)) for row in cursor]

    con.close()

    if elapsed_total > .2:
        print("Database Query took", elapsed_total, "secs", "(", elapsed_connect, ")")

    return maprows


# caution: must not expose this due to "pg8000 is designed to be used with one thread per connection."
def _create_new_connection():
    username = environ.get('PGUSER', 'mev_dashboard_query_user')
    password = environ.get('PGPASSWORD')
    assert password is not None, "PGPASSWORD environment variable must be set"
    host = environ.get('PGHOST', 'localhost')
    port = environ.get('PGPORT', '5432')
    database = environ.get('PGDATABASE', 'mangolana')
    timeout = 10 # seconds
    ssl_context = configure_sslcontext()
    application_name="bankingstage-dashboard"

    con = pg8000.dbapi.Connection(username, host=host, port=port, password=password, database=database,
                                  application_name=application_name, timeout=timeout, ssl_context=ssl_context)
    return con


def configure_sslcontext():
    if environ.get('PGSSL', 'false') == 'true':
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = False
        ssl_context.load_verify_locations("ca.cer")
        ssl_context.load_cert_chain("client.cer", keyfile="client-key.cer")
        return ssl_context
    else:
        return None
