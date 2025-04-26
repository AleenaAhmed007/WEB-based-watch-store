# app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'watch_haven_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///watches.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import routes after initializing db to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(debug=True)