from flask import Flask, render_template
import dbtestcall

app = Flask(__name__)


@app.route('/txerrors')
def table():
    maprows = dbtestcall.RunQuery()
    return render_template('table.html', transactions=maprows)

@app.route('/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
