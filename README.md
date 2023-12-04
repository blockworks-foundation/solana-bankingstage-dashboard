## Solana Tx Error Page!

### Status
Pre-alpha / demo only

### Screenshots

#### Transaction errors with messages
![Transaction Errors](docs/tx-errors.png "Transaction Errors")

##### Blocks fill rate / errors / total tx
![Recent Blocks](docs/blocks.png "Blocks Content")


### Development
**Caution:** Port `5000` cannot be used on MacOS.

```
# Unix/macOS
python3 -m venv .venv
source .venv/bin/activate
SOLANA_CLUSTER=testnet POOLED_DB_MAX_SIZE=8 PGDATABASE=da11copy PGUSER=query_user PGPASSWORD=secret TEMPLATES_AUTO_RELOAD=True flask run --port 5050 --debug --reload
```

Use this to test with _gunicorn_: 
```
SOLANA_CLUSTER=testnet POOLED_DB_MAX_SIZE=8 PGDATABASE=da11copy PGPORT=5432 PGUSER=query_user PGPASSWORD=secret TEMPLATES_AUTO_RELOAD=True gunicorn app:webapp --bind :5050 --reload
```

Open Firefox Browser and navigate to ...
* [Dashboard](http://localhost:5050/dashboard)
* [Blocks and Tx Errors](http://localhost:5050/recent-blocks)
* [Search for one Block or Transaction](http://localhost:5050/search)

### Deployment
#### Limits
| Description                         | System      | Variable               | Config     |
|-------------------------------------|-------------|------------------------|------------|
| Max number of PostgreSQL connections | Application | POOLED_DB_MAX_SIZE     | fly.toml   |
| Limit of HTTP Requests              | fly.io      | soft_limit             | fly.toml   |
| Hard Limit of HTTP Requests         | fly.io      | hard_limit             | fly.toml   |
| Python HTTP Server                  | gunicorn    | --workers, --threads | Dockerfile |

