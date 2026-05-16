import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ucrs-dev-secret-2024')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'continue7x')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'ucrs')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
