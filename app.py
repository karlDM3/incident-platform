# app.py
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize the database
def init_db():
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        location TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Check if user exists
def get_user(username):
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user(username):
            return "User already exists!"
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, hash_password(password)))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and user[2] == hash_password(password):
            session['user_id'] = user[0]
            return redirect(url_for('report'))
        return "Invalid username or password!"
    return render_template('login.html')

# Report incident route
@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        user_id = session['user_id']
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reports (user_id, title, description, location) VALUES (?, ?, ?, ?)",
                       (user_id, title, description, location))
        conn.commit()
        conn.close()
        return redirect(url_for('view_reports'))
    
    return render_template('report.html')

# View all reports route
@app.route('/reports')
def view_reports():
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    cursor.execute("SELECT reports.id, users.username, reports.title, reports.description, reports.location, reports.timestamp FROM reports JOIN users ON reports.user_id = users.id ORDER BY reports.timestamp DESC")
    reports = cursor.fetchall()
    conn.close()
    return render_template('reports.html', reports=reports)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
