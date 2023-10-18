from flask import Flask, render_template
from turbo_flask import Turbo
import transaction_database
import recent_blocks_database
import threading
import time
from random import shuffle

#
# MAIN
#

app = Flask(__name__)
# https://blog.miguelgrinberg.com/post/dynamically-update-your-flask-web-pages-using-turbo-flask
turbo = Turbo(app)
app.update_thread_started = False


transaction_database.run_query()
recent_blocks_database.run_query()
print("SELFTEST passed")

######################


@app.route('/dashboard')
def dashboard():
    start_if_needed()
    start = time.time()
    maprows = transaction_database.run_query()
    elapsed = time.time() - start
    if elapsed > .5:
        print("transaction_database.RunQuery() took", elapsed, "seconds")
    return render_template('dashboard.html', transactions=maprows)

@app.route('/recent-blocks')
def recent_blocks():
    start_if_needed()
    start = time.time()
    maprows = recent_blocks_database.run_query()
    elapsed = time.time() - start
    if elapsed > .5:
        print("recent_blocks_database.RunQuery() took", elapsed, "seconds")
    return render_template('recent_blocks.html', blocks=maprows)


def start_if_needed():
    if app.update_thread_started:
        return
    app.update_thread_started = True
    threading.Thread(target=update_load).start()


# note: the poller needs to be started in web context to learn about the server parameters
def update_load():
    with app.app_context():
        print('start turbo.js update poller')
        while True:
            # note: the push sends update to all subscribed clients

            maprows = transaction_database.run_query()
            turbo.push(turbo.replace(render_template('_table.html', transactions=maprows), 'datatable'))

            maprows = recent_blocks_database.run_query()
            # turbo.push(turbo.replace(render_template('_blockslist.html', blocks=maprows), 'blockslist'))

            time.sleep(1)

