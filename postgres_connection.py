import pg8000
from os import environ


# note: passwordless auth is not supported
def create_connection():
    username = environ.get('PGUSER', 'mev_dashboard_query_user')
    password = environ.get('PGPASSWORD')
    assert password is not None, "PGPASSWORD environment variable must be set"
    host = environ.get('PGHOST', 'localhost')
    port = environ.get('PGPORT', '5432')
    database = environ.get('PGDATABASE', 'mangolana')
    con = pg8000.dbapi.Connection(username, host=host, port=port, password=password, database=database)
    return con
