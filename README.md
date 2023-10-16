## Solana Tx Error Page!

### Status
Pre-alpha / demo only

### Screenshots

#### Transaction errors with messages
![Transaction Errors](docs/tx-errors.png "Transaction Errors")

##### Blocks fill rate / errors / total tx
![Recent Blocks](docs/blocks.png "Blocks Content")


### Development
```
# Unix/macOS
python3 -m venv .venv
source .venv/bin/activate
TEMPLATES_AUTO_RELOAD=True flask run --debug --reload
```

Open Firefox Browser and navigate to ...
* [Dashboard](http://localhost:5000/dashboard)
* [Blocks and Tx Errors](http://localhost:5000/recent-blocks)