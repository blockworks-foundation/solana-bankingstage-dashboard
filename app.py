from flask import Flask, render_template
from turbo_flask import Turbo
import transaction_database
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


######################


@app.route('/dashboard')
def dashboard():
    start_if_needed()
    maprows = transaction_database.RunQuery()
    return render_template('dashboard.html', transactions=maprows)

@app.route('/recent-blocks')
def recent_blocks():
    return render_template('recent_blocks.html')


def start_if_needed():
    if app.update_thread_started:
        return
    app.update_thread_started = True
    threading.Thread(target=update_load).start()


# note: the poller needs to be started in web context to learn about the server parameters
def update_load():
    with app.app_context():
        print('start update poller')
        while True:
            time.sleep(1)
            maprows = transaction_database.RunQuery()
            # TODO remove - this is for testing only
            shuffle(maprows)
            # note: the push sends update to all subscribed clients
            turbo.push(turbo.replace(render_template('_table.html', transactions=maprows), 'datatable'))

