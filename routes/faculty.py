from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from db import get_db
from routes.utils import login_required

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

VALID_GRADES = {'A', 'B', 'C', 'D', 'F'}


@faculty_bp.route('/dashboard')
@login_required(role='faculty')
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    faculty_id = session['user_id']

    cursor.execute(
        '''SELECT co.offering_id, c.course_name, c.credit_hours,
                  sem.name AS semester_name, sem.year,
                  co.seats_total, co.seats_available,
                  COUNT(e.enrollment_id) AS enrolled_count
           FROM course_offerings co
           JOIN courses c ON co.course_id = c.course_id
           JOIN semesters sem ON co.semester_id = sem.semester_id
           LEFT JOIN enrollments e ON e.offering_id = co.offering_id
           WHERE co.faculty_id = %s
           GROUP BY co.offering_id
           ORDER BY sem.year DESC, sem.name''',
        (faculty_id,)
    )
    offerings = cursor.fetchall()
    cursor.close()

    return render_template('faculty/dashboard.html', offerings=offerings)


@faculty_bp.route('/grades/')
@login_required(role='faculty')
def grades():
    offering_id = request.args.get('offering_id', type=int)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    faculty_id = session['user_id']

    cursor.execute(
        '''SELECT co.offering_id, c.course_name,
                  sem.name AS semester_name, sem.year, co.semester_id
           FROM course_offerings co
           JOIN courses c ON co.course_id = c.course_id
           JOIN semesters sem ON co.semester_id = sem.semester_id
           WHERE co.faculty_id = %s
           ORDER BY sem.year DESC, sem.name''',
        (faculty_id,)
    )
    offerings = cursor.fetchall()

    students = []
    selected_offering = None

    if offering_id:
        cursor.execute(
            '''SELECT co.offering_id, c.course_name, sem.name AS semester_name,
                      sem.year, co.semester_id
               FROM course_offerings co
               JOIN courses c ON co.course_id = c.course_id
               JOIN semesters sem ON co.semester_id = sem.semester_id
               WHERE co.offering_id = %s AND co.faculty_id = %s''',
            (offering_id, faculty_id)
        )
        selected_offering = cursor.fetchone()

        if selected_offering:
            cursor.execute(
                '''SELECT e.enrollment_id, e.grade, s.name AS student_name,
                          s.student_id, s.email
                   FROM enrollments e
                   JOIN students s ON e.student_id = s.student_id
                   WHERE e.offering_id = %s
                   ORDER BY s.name''',
                (offering_id,)
            )
            students = cursor.fetchall()

    cursor.close()
    return render_template('faculty/grades.html',
                           offerings=offerings,
                           students=students,
                           selected_offering=selected_offering)


@faculty_bp.route('/grades/submit', methods=['POST'])
@login_required(role='faculty')
def submit_grades():
    offering_id = request.form.get('offering_id', type=int)
    semester_id = request.form.get('semester_id', type=int)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    updated = 0
    for key, value in request.form.items():
        if not key.startswith('grade_'):
            continue
        enrollment_id = key[len('grade_'):]
        grade = value.strip().upper() if value.strip() else None

        if grade and grade not in VALID_GRADES:
            flash(f'Invalid grade "{grade}" ignored.', 'error')
            continue

        cursor.execute(
            'SELECT student_id FROM enrollments WHERE enrollment_id = %s',
            (enrollment_id,)
        )
        row = cursor.fetchone()
        if not row:
            continue

        cursor.execute(
            'UPDATE enrollments SET grade = %s WHERE enrollment_id = %s',
            (grade, enrollment_id)
        )

        if grade and semester_id:
            try:
                cursor.callproc('calculate_gpa', [row['student_id'], semester_id])
            except mysql.connector.Error as e:
                flash(f'GPA calculation error: {e.msg}', 'error')

        updated += 1

    cursor.close()
    if updated:
        flash(f'{updated} grade(s) saved successfully.', 'success')

    return redirect(url_for('faculty.grades', offering_id=offering_id))
