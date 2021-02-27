

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return "website is started"


@app.route("/bootstrap")
def bootstrap():
    return render_template('bootstrap.html')


app.run(debug = True)
