import pg8000
import ssl
from os import environ

# global
_global_connection_pool = [None] * 6
_pool_round_robin_index = 0


def _create_new_connection():
    username = environ.get('PGUSER', 'mev_dashboard_query_user')
    password = environ.get('PGPASSWORD')
    assert password is not None, "PGPASSWORD environment variable must be set"
    host = environ.get('PGHOST', 'localhost')
    port = environ.get('PGPORT', '5432')
    database = environ.get('PGDATABASE', 'mangolana')
    if environ.get('PGSSL', 'false') == 'true':
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = False
        ssl_context.load_verify_locations("ca.cer")
        ssl_context.load_cert_chain("client.cer", keyfile="client-key.cer")

        con = pg8000.dbapi.Connection(username, host=host, port=port, password=password, database=database, ssl_context=ssl_context)
        return con
    else:
        con = pg8000.dbapi.Connection(username, host=host, port=port, password=password, database=database)
        return con


def get_connection():
    global _global_connection_pool
    global _pool_round_robin_index

    populate_connections()

    try:
        con = _global_connection_pool[_pool_round_robin_index]
        con.cursor().execute("SELECT 1")
        increment_index()
        return con
    except Exception as ex:
        print("PostgreSQL connection not working - create new: ", ex)
        new_con = _create_new_connection()
        _global_connection_pool[_pool_round_robin_index] = new_con
        increment_index()
        return new_con


def increment_index():
    global _global_connection_pool
    global _pool_round_robin_index
    _pool_round_robin_index = (_pool_round_robin_index + 1) % len(_global_connection_pool)


# note: this is quite slow as it requires N full TLS handshakes
def populate_connections():
    for index, con in enumerate(_global_connection_pool):
        if con is None:
            _global_connection_pool[index] = _create_new_connection()
