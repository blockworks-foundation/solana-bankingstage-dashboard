import pg8000
import ssl
import base64
from os import environ


# note: passwordless auth is not supported
def create_connection():
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