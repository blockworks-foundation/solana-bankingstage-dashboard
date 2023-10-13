from flask import Flask, render_template
import transaction_database

app = Flask(__name__)


@app.route('/dashboard')
def table():
    maprows = transaction_database.RunQuery()
    print(maprows)
    return render_template('table.html', transactions=maprows)

@app.route('/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
