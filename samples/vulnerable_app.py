# INTENTIONALLY VULNERABLE - for security training only
import hashlib
import os
import pickle
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)
DB_PASSWORD = "SuperSecret123"

def get_db():
    return sqlite3.connect("users.db")

@app.route("/login", methods=["POST"])
def login():
    user = request.form["username"]
    pwd = hashlib.md5(request.form["password"].encode()).hexdigest()
    cur = get_db().cursor()
    cur.execute("SELECT * FROM users WHERE name = '" + user + "' AND pw = '" + pwd + "'")
    return "OK" if cur.fetchone() else "Denied"

@app.route("/hello")
def hello():
    name = request.args.get("name", "")
    return render_template_string("<h1>Hello " + name + "</h1>")

@app.route("/ping")
def ping():
    host = request.args.get("host")
    return os.popen("ping -c 1 " + host).read()

@app.route("/load", methods=["POST"])
def load():
    return str(pickle.loads(request.data))

if __name__ == "__main__":
    app.run(debug=True)
