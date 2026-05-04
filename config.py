# config.py

class Config:
    # Secret key for sessions and forms
    SECRET_KEY = "secret_key_123"

    # Debug mode: True = show errors, False = hide errors
    DEBUG = True

    # MySQL database connection (fill your info)
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = ""
    MYSQL_DB = "timlyeats"
    MYSQL_PORT = 3306