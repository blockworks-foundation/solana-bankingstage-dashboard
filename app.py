from flask import Flask, render_template, request, make_response
from turbo_flask import Turbo
import threading
import time
from flask_htmx import HTMX
import re

import transaction_database
import recent_blocks_database
import config

#
# MAIN
#

webapp = Flask(__name__)
# https://blog.miguelgrinberg.com/post/dynamically-update-your-flask-web-pages-using-turbo-flask
turbo = Turbo(webapp)
htmx = HTMX(webapp)

webapp.update_thread_started = False


print("SOLANA_CLUSTER", config.get_config()['cluster'])
transaction_database.run_query()
recent_blocks_database.run_query()
print("SELFTEST passed")

######################


@webapp.route('/dashboard')
def dashboard():
    start_if_needed()
    this_config = config.get_config()
    start = time.time()
    maprows = list(transaction_database.run_query())
    elapsed = time.time() - start
    if elapsed > .5:
        print("transaction_database.RunQuery() took", elapsed, "seconds")
    return render_template('dashboard.html', config=this_config, transactions=maprows)


@webapp.route('/recent-blocks')
def recent_blocks():
    start_if_needed()
    this_config = config.get_config()
    start = time.time()
    maprows = list(recent_blocks_database.run_query())
    elapsed = time.time() - start
    if elapsed > .5:
        print("recent_blocks_database.RunQuery() took", elapsed, "seconds")
    return render_template('recent_blocks.html', config=this_config, blocks=maprows)


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

        if is_slot_number(search_string):
            print("slot search=", search_string)
            maprows = list(recent_blocks_database.find_block_by_slotnumber(int(search_string)))
            if len(maprows):
                return render_template('_blockslist.html', config=this_config, blocks=maprows)
            else:
                return render_template('_search_noresult.html')
        elif is_block_hash(search_string):
            print("blockhash search=", search_string)
            maprows = list(recent_blocks_database.find_block_by_blockhash(search_string))
            if len(maprows):
                return render_template('_blockslist.html', config=this_config, blocks=maprows)
            else:
                return render_template('_search_noresult.html')
        elif is_tx_sig(search_string):
            print("txsig search=", search_string)
            maprows = list(transaction_database.find_transaction_by_sig(search_string))
            if len(maprows):
                return render_template('_txlist.html', config=this_config, transactions=maprows)
            else:
                return render_template('_search_noresult.html')
        else:
            return render_template('_search_unsupported.html', search_string=search_string)

    return render_template('search.html')


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


def start_if_needed():
    if webapp.update_thread_started:
        return
    webapp.update_thread_started = True
    threading.Thread(target=update_load).start()


# note: the poller needs to be started in web context to learn about the server parameters
def update_load():
    with webapp.app_context():
        print('start turbo.js update poller')
        this_config = config.get_config()
        while True:
            # note: the push sends update to all subscribed clients

            maprows = list(transaction_database.run_query())
            turbo.push(turbo.replace(render_template('_txlist.html', config=this_config, transactions=maprows), 'txlist'))

            maprows = list(recent_blocks_database.run_query())
            turbo.push(turbo.replace(render_template('_blockslist.html', config=this_config, blocks=maprows), 'blockslist'))

            time.sleep(1)

