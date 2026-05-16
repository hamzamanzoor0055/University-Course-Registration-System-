from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from db import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for(f'{session["role"]}.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = get_db()
        cursor = db.cursor(dictionary=True)

        user = None
        role = None

        cursor.execute(
            'SELECT student_id AS user_id, name, password_hash FROM students WHERE email = %s',
            (email,)
        )
        row = cursor.fetchone()
        if row:
            user, role = row, 'student'

        if not user:
            cursor.execute(
                'SELECT faculty_id AS user_id, name, password_hash FROM faculty WHERE email = %s',
                (email,)
            )
            row = cursor.fetchone()
            if row:
                user, role = row, 'faculty'

        if not user:
            cursor.execute(
                'SELECT admin_id AS user_id, name, password_hash FROM admins WHERE email = %s',
                (email,)
            )
            row = cursor.fetchone()
            if row:
                user, role = row, 'admin'

        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['role'] = role
            session['name'] = user['name']
            flash(f'Welcome, {user["name"]}!', 'success')
            return redirect(url_for(f'{role}.dashboard'))

        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
