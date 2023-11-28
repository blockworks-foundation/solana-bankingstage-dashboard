from flask import Flask, render_template, request, make_response, redirect
import time
from flask_htmx import HTMX
import re

import transaction_database
import recent_blocks_database
import block_details_database
import config

#
# MAIN
#

webapp = Flask(__name__)
htmx = HTMX(webapp)

webapp.update_thread_started = False


print("SOLANA_CLUSTER", config.get_config()['cluster'])
transaction_database.run_query()
recent_blocks_database.run_query()
block_details_database.find_block_by_slotnumber(226352855)
print("SELFTEST passed")

#################gi#####

@webapp.route('/')
def index():
    return redirect("/tx-errors", code=302)


# fly.io service health check
@webapp.route('/health')
def health():
    return "UP\r\n", 200


@webapp.route('/dashboard')
def dashboard():
    return redirect("/tx-errors", code=302)


@webapp.route('/tx-errors')
def tx_errors():
    this_config = config.get_config()
    start = time.time()
    maprows = list(transaction_database.run_query())
    elapsed = time.time() - start
    if elapsed > .5:
        print("transaction_database.RunQuery() took", elapsed, "seconds")
    return render_template('tx-errors.html', config=this_config, transactions=maprows)


@webapp.route('/recent-blocks')
def recent_blocks():
    this_config = config.get_config()
    start = time.time()
    maprows = list(recent_blocks_database.run_query())
    elapsed = time.time() - start
    if elapsed > .5:
        print("recent_blocks_database.RunQuery() took", elapsed, "seconds")
    return render_template('recent_blocks.html', config=this_config, blocks=maprows)


@webapp.route('/block/<path:slot>')
def get_block(slot):
    this_config = config.get_config()
    start = time.time()
    maprows = list(block_details_database.find_block_by_slotnumber(slot))
    elapsed = time.time() - start
    if elapsed > .5:
        print("block_details_database.find_block_by_slotnumber() took", elapsed, "seconds")
    if len(maprows):
        return render_template('block_details.html', config=this_config, block=maprows[0])
    else:
        return "Block not found", 404


def is_slot_number(raw_string):
    return re.fullmatch("[0-9]+", raw_string) is not None


def is_block_hash(raw_string):
    # regex is not perfect - feel free to improve
    return re.fullmatch("[0-9a-zA-Z]{43,44}", raw_string) is not None


def is_tx_sig(raw_string):
    # regex is not perfect - feel free to improve
    if is_block_hash(raw_string):
        return False
    return re.fullmatch("[0-9a-zA-Z]{64,100}", raw_string) is not None


@webapp.route('/search', methods=["GET", "POST"])
def search():
    this_config = config.get_config()
    if htmx:
        search_string = request.form.get("search").strip()

        if search_string == "":
            return render_template('_search_noresult.html', config=this_config)

        if is_slot_number(search_string):
            maprows = list(recent_blocks_database.find_block_by_slotnumber(int(search_string)))
            if len(maprows):
                return render_template('_blockslist.html', config=this_config, blocks=maprows)
            else:
                return render_template('_search_noresult.html', config=this_config)
        elif is_block_hash(search_string):
            print("blockhash search=", search_string)
            maprows = list(recent_blocks_database.find_block_by_blockhash(search_string))
            if len(maprows):
                return render_template('_blockslist.html', config=this_config, blocks=maprows)
            else:
                return render_template('_search_noresult.html', config=this_config)
        elif is_tx_sig(search_string):
            print("txsig search=", search_string)
            maprows = list(transaction_database.find_transaction_by_sig(search_string))
            if len(maprows):
                return render_template('_txlist.html', config=this_config, transactions=maprows)
            else:
                return render_template('_search_noresult.html', config=this_config)
        else:
            return render_template('_search_unsupported.html', config=this_config, search_string=search_string)

    return render_template('search.html', config=this_config)


# uid INTEGER,
# name TEXT NOT NULL,
# email TEXT NOT NULL,
# tel TEXT NOT NULL,
def getusers(search):
    row = dict()
    row["uid"] = 42
    row["name"] = "John, Doe"
    row["email"] = "foo@bar.com"
    row["tel"] = "0121212"
    results = [row, row ,row]
    return results


