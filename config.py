# config.py

class Config:
    # Secret key for sessions and forms
    SECRET_KEY = "supersecretkey"

    # Database URI (SQLite for starter)
    SQLALCHEMY_DATABASE_URI = "sqlite:///mydb.db"

    # Disable unnecessary tracking to save memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional: debug mode (can override later)
    DEBUG = True