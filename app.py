from flask import Flask, render_template
from turbo_flask import Turbo
import threading
import time

import transaction_database
import recent_blocks_database
import config

#
# MAIN
#

webapp = Flask(__name__)
# https://blog.miguelgrinberg.com/post/dynamically-update-your-flask-web-pages-using-turbo-flask
turbo = Turbo(webapp)
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
            turbo.push(turbo.replace(render_template('_txlist.html', config=this_config, transactions=maprows), 'datatable'))

            maprows = list(recent_blocks_database.run_query())
            turbo.push(turbo.replace(render_template('_blockslist.html', config=this_config, blocks=maprows), 'blockslist'))

            time.sleep(1)

