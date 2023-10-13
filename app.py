from flask import Flask, render_template
from turbo_flask import Turbo
import transaction_database
import threading
import time
from random import shuffle

app = Flask(__name__)
# https://blog.miguelgrinberg.com/post/dynamically-update-your-flask-web-pages-using-turbo-flask
turbo = Turbo(app)
app.update_thread_started = False


@app.route('/dashboard')
def dashboard():
    start_if_needed()
    maprows = transaction_database.RunQuery()
    return render_template('dashboard.html', transactions=maprows)

# refresh all clients
@app.route('/refresh')
def refresh():
    # turbo.push(turbo.replace(render_template('table.html'), 'datatable'))
    return 'ok'


def start_if_needed():
    if app.update_thread_started:
        return
    app.update_thread_started = True
    threading.Thread(target=update_load).start()



def update_load():
    with app.app_context():
        print('start update poller')
        while True:
            time.sleep(1)
            maprows = transaction_database.RunQuery()
            shuffle(maprows)
            turbo.push(turbo.replace(render_template('table.html', transactions=maprows), 'datatable'))