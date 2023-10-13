from flask import Flask, render_template
import dbtestcall

app = Flask(__name__)


@app.route('/txerrors')
def table():
    rows = dbtestcall.some_data()
    return render_template('table.html', rows=rows)

@app.route('/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
