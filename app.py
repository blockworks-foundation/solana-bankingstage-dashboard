from flask import Flask, render_template
from turbo_flask import Turbo
import transaction_database

app = Flask(__name__)
turbo = Turbo(app)

@app.route('/dashboard')
def table():
    maprows = transaction_database.RunQuery()
    print(maprows)
    return render_template('table.html', transactions=maprows)

@app.route('/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
