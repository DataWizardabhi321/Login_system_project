import configparser
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

# Create Flask app instance
app = Flask(__name__)

# Secret key for session management
app.secret_key = 'd9f2a63d7e4f8d1b3c9e2f8a0a7d2e9c4'

# Read configuration from .ini file
config = configparser.ConfigParser()

# Use a try-except block to handle potential errors
try:
    config.read('db.ini')
    
    # Check if the 'mysql' section exists
    if 'mysql' not in config:
        raise ValueError("The 'mysql' section is missing in the configuration file.")
    
    # Configure MySQL
    app.config['MYSQL_HOST'] = config.get('mysql', 'host')
    app.config['MYSQL_USER'] = config.get('mysql', 'user')
    app.config['MYSQL_PASSWORD'] = config.get('mysql', 'password')
    app.config['MYSQL_DB'] = config.get('mysql', 'db')

except (configparser.NoSectionError, ValueError) as e:
    print(f"Error: {e}")
    exit(1)  # Exit the program if the configuration is invalid

# Initialize MySQL
mysql = MySQL(app)

# Regex patterns
email_regex = re.compile(r'[^@]+@[^@]+\.[^@]+')
username_regex = re.compile(r'[A-Za-z0-9]+')

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and all(key in request.form for key in ['username', 'password']):
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, username FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully'
            return render_template('index.html', msg=msg)
        else:
            msg = 'Incorrect username/Password'
    
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        if not all(key in request.form for key in ['username', 'password', 'email']):
            msg = 'Please fill the form!'
        else:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            
            if not email_regex.match(email):
                msg = 'Invalid email address'
            elif not username_regex.match(username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not password or not email:
                msg = 'Please fill the form'
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT id FROM accounts WHERE username = %s', (username,))
                if cursor.fetchone():
                    msg = 'Account already exists'
                else:
                    cursor.execute('INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
                    mysql.connection.commit()
                    msg = 'You have successfully registered'
    
    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)
