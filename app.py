from flask import Flask, render_template, request, make_response, redirect
from flask_htmx import HTMX
import time
import re
import transaction_database
import transaction_details_database
import recent_blocks_database
import block_details_database
import config

#
# MAIN
#

print("Setting up Flask webapp...")
webapp = Flask(__name__)
htmx = HTMX(webapp)


print("SOLANA_CLUSTER", config.get_config()['cluster'])
transaction_database.run_query()
recent_blocks_database.run_query()
block_details_database.find_block_by_slotnumber(226352855)
print("SELFTEST passed")


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
    to_slot = request.args.get('to_slot', default = 0, type = int)
    if to_slot == 0:
        to_slot = None

    start = time.time()
    maprows = list(recent_blocks_database.run_query(to_slot))
    elapsed = time.time() - start
    if elapsed > .5:
        print("recent_blocks_database.RunQuery() took", elapsed, "seconds")

    enable_polling = "true" if to_slot is None else "false"

    return render_template('recent_blocks.html', config=this_config, blocks=maprows, enable_polling=enable_polling)


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

    if request.method == "GET":
        return render_template('search.html', config=this_config)

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


@webapp.route('/transaction/<path:signature>')
def get_transaction_details(signature):
    this_config = config.get_config()
    start = time.time()
    maprows = list(transaction_details_database.find_transaction_details_by_sig(signature))
    elapsed = time.time() - start
    if elapsed > .5:
        print("transaction_database.find_transaction_details_by_sig() took", elapsed, "seconds")
    if len(maprows):
        return render_template('transaction_details.html', config=this_config, transaction=maprows[0])
    else:
        return "Transaction not found", 404


# format 123456789 to "123,456,789"
@webapp.template_filter('lamports')
def lamports_filter(number: int):
    if number is None:
        return ""
    else:
        # https://realpython.com/python-formatted-output/#the-group-subcomponent
        # return format(number, ",.2f")
        return format(number, ",")
