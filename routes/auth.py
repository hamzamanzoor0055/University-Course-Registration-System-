from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
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


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for(f'{session["role"]}.dashboard'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT dept_id, dept_name FROM departments ORDER BY dept_name')
    departments = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        dept_id = request.form.get('dept_id', type=int)

        if not name or not email or not password or not dept_id:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html', departments=departments)

        password_hash = generate_password_hash(password)
        cursor = db.cursor()
        try:
            cursor.execute(
                'INSERT INTO students (name, email, password_hash, dept_id) VALUES (%s, %s, %s, %s)',
                (name, email, password_hash, dept_id)
            )
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except mysql.connector.Error as e:
            flash(f'Registration failed: {e.msg}', 'error')
            return render_template('auth/register.html', departments=departments)
        finally:
            cursor.close()

    return render_template('auth/register.html', departments=departments)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
