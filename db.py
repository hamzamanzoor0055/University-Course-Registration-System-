import mysql.connector
from flask import g, current_app


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            port=current_app.config['MYSQL_PORT'],
            autocommit=True,
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
