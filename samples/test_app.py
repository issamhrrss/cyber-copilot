import os
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# 1. Hardcoded API Key & Password (بيانات حساسة مكشوفة)
API_KEY = "AIzaSyD-TEST-KEY-1234567890ABCDEF"
DATABASE_PASSWORD = "SuperSecretPassword123!"

# 2. SQL Injection Vulnerability (ثغرة حقن أوامر SQL)
@app.route('/user')
def get_user():
    username = request.args.get('username')
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return str(cursor.fetchall())

# 3. Command Injection Vulnerability (ثغرة تنفيذ أوامر النظام)
@app.route('/ping')
def ping_host():
    ip = request.args.get('ip')
    os.system(f"ping -c 1 {ip}")
    return "Ping executed"

if __name__ == '__main__':
    app.run(debug=True)
