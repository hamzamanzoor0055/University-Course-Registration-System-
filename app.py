from flask import Flask, redirect, url_for
from config import Config
from db import init_app


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_app(app)

    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.faculty import faculty_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
